# Huấn luyện TravelMate Chatbot

Pipeline fine-tune `Qwen/Qwen3-4B` bằng QLoRA được chia thành bốn giai đoạn,
tương ứng với bốn notebook Google Colab:

1. [`TravelMate_01_Data_Prep.ipynb`](notebooks/TravelMate_01_Data_Prep.ipynb):
   kiểm tra và chia dữ liệu.
2. [`TravelMate_02_QLoRA_Training.ipynb`](notebooks/TravelMate_02_QLoRA_Training.ipynb):
   dry-run và train LoRA adapter.
3. [`TravelMate_03_Evaluation.ipynb`](notebooks/TravelMate_03_Evaluation.ipynb):
   sinh phản hồi trên tập Test và chấm các hành vi bắt buộc.
4. [`TravelMate_04_Inference_Demo.ipynb`](notebooks/TravelMate_04_Inference_Demo.ipynb):
   nạp adapter và hỏi thử mô hình.

Quá trình huấn luyện chính thức nên chạy trên Linux có GPU NVIDIA tối thiểu
khoảng 16 GB VRAM, chẳng hạn Google Colab hoặc Kaggle. Laptop RTX 4050 6 GB
chỉ nên dùng để chạy API, giao diện demo hoặc thử suy luận 4-bit.

## 1. Chuẩn bị dữ liệu

Mỗi dòng JSONL là một cuộc hội thoại. `id` phải duy nhất, `category` dùng để
chia dữ liệu theo chủ đề và `expectedBehaviors` phục vụ đánh giá:

```json
{
  "id": "realtime-001",
  "category": "realtime_limit",
  "expectedBehaviors": ["realtime_limit", "ask_clarification"],
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "Khách sạn nào còn phòng tối nay?"},
    {"role": "assistant", "content": "Mình cần tra cứu nguồn đặt phòng..."}
  ]
}
```

Kiểm tra và chia cố định theo seed `42`:

```bash
python -m training.validate_dataset \
  training/data/travelmate_train.sample.jsonl \
  --minimum-records 20 \
  --require-metadata

python -m training.prepare_dataset \
  training/data/travelmate_train.sample.jsonl \
  --output-dir training/data/processed \
  --seed 42
```

File 20 mẫu chỉ dùng để kiểm tra pipeline. Trước khi train chính thức, cần mở
rộng thành khoảng 1.000–3.000 hội thoại đã được rà soát. Dữ liệu nên bao phủ
lịch trình, chỗ ở, ngân sách, ăn uống, an toàn, câu hỏi cần làm rõ, giới hạn
dữ liệu thời gian thực, giới hạn giao dịch và nội dung ngoài phạm vi.

Repo có bộ 1.200 hội thoại nháp tái lập từ template:

```bash
python -m training.generate_synthetic_dataset \
  --output training/data/travelmate_synthetic_v1.jsonl

python -m training.validate_dataset \
  training/data/travelmate_synthetic_v1.jsonl \
  --minimum-records 1200 \
  --require-metadata

python -m training.prepare_dataset \
  training/data/travelmate_synthetic_v1.jsonl \
  --output-dir training/data/processed \
  --seed 42
```

Phân bố hiện tại là 300 lịch trình, 240 ngân sách, 200 chỗ ở, 120 ăn uống,
120 an toàn/thời tiết, 80 giới hạn dữ liệu thời gian thực, 80 câu ngoài phạm
vi và 60 giới hạn giao dịch. Mỗi mẫu có `reviewBatch` từ 1 đến 12, tương ứng
12 lô, mỗi lô 100 mẫu.

Tất cả mẫu sinh tự động mang `reviewStatus=synthetic_draft_v1`. Sau khi đọc,
sửa và chấp thuận một mẫu, đổi trạng thái thành `approved`. Có thể kiểm tra
toàn bộ dataset đã được duyệt bằng lệnh:

```bash
python -m training.approve_dataset \
  --draft training/data/travelmate_synthetic_v1.jsonl \
  --output training/data/travelmate_train_v1.jsonl \
  --report training/reports/dataset_v1_review.json \
  --approved-at 2026-08-03
```

Lệnh trên chỉ phê duyệt khi dataset khớp generator đã rà soát, có đủ phân bố,
không trùng ID/câu hỏi/câu trả lời, đủ 12 lô, đạt giới hạn độ dài và vượt toàn
bộ rule hành vi. Đây là audit template/schema/rule, chưa thay thế đánh giá độc
lập của người dùng.

Có thể kiểm tra lại file đã phê duyệt bằng lệnh:

```bash
python -m training.validate_dataset \
  training/data/travelmate_train_v1.jsonl \
  --minimum-records 1200 \
  --require-metadata \
  --require-review-status approved
```

Script train mặc định từ chối dataset còn trạng thái nháp. Cờ
`--allow-unreviewed-data` chỉ được dùng khi dry-run hoặc thử pipeline, không
dùng để tạo adapter báo cáo chính thức.

## 2. Dry-run và train QLoRA

Cài dependency:

```bash
python -m pip install -e ".[training]"
```

Kiểm tra dữ liệu và tham số mà không tải model:

```bash
python -m training.train_qlora \
  --train-dataset training/data/processed/train.jsonl \
  --eval-dataset training/data/processed/validation.jsonl \
  --output-dir artifacts/travelmate-qwen3-4b-lora \
  --dry-run
```

Smoke test 1 epoch trên CPU dùng kiến trúc Qwen3 cực nhỏ khởi tạo ngẫu nhiên.
Lệnh này kiểm tra tokenizer, LoRA, `SFTTrainer`, Train/Validation và việc lưu
adapter; metric sinh ra không đại diện cho chất lượng mô hình:

```bash
python -m training.train_qlora \
  --train-dataset training/data/processed/train.jsonl \
  --eval-dataset training/data/processed/validation.jsonl \
  --output-dir artifacts/smoke-qwen3-tiny-lora \
  --model-id Qwen/Qwen3-0.6B \
  --epochs 1 \
  --max-length 128 \
  --gradient-accumulation-steps 1 \
  --smoke-test
```

Train adapter:

```bash
python -m training.train_qlora \
  --train-dataset training/data/processed/train.jsonl \
  --eval-dataset training/data/processed/validation.jsonl \
  --output-dir artifacts/travelmate-qwen3-4b-lora \
  --epochs 3
```

Pipeline dùng NF4 4-bit, LoRA trên toàn bộ lớp tuyến tính và chỉ tính loss cho
phần trả lời của assistant. Checkpoint, metric và cấu hình lần chạy được lưu
cùng adapter.

## 3. Đánh giá

Sinh phản hồi cho tập Test:

```bash
python -m training.generate_predictions \
  --dataset training/data/processed/test.jsonl \
  --adapter-path artifacts/travelmate-qwen3-4b-lora \
  --output training/outputs/test_predictions.jsonl
```

Chấm độ phủ, phản hồi rỗng và các hành vi đã gán trong dataset:

```bash
python -m training.evaluate_predictions \
  --dataset training/data/processed/test.jsonl \
  --predictions training/outputs/test_predictions.jsonl \
  --output training/outputs/evaluation_report.json
```

Điểm tự động không thay thế đánh giá thủ công. Cần đọc từng lịch trình để kiểm
tra tính hợp lý, độ đúng của thông tin và mức hữu ích đối với người dùng.

## 4. Dùng adapter trong AI Service

```env
LLM_PROVIDER=local
LOCAL_MODEL_ID=Qwen/Qwen3-4B
LOCAL_ADAPTER_PATH=artifacts/travelmate-qwen3-4b-lora
LOCAL_MODEL_LOAD_IN_4BIT=true
```

Không commit thư mục `artifacts`, `training/data/processed`, `training/outputs`
hoặc file trọng số lên Git. Chỉ commit mã nguồn, notebook không chứa output,
dataset được phép chia sẻ và báo cáo thống kê cần thiết.
