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

Bộ `training/data/challenge_v1.jsonl` gồm 20 tình huống viết tay và không được
đưa vào train. Tập này kiểm tra câu hỏi mới, hội thoại nhiều lượt, giới hạn
giao dịch, dữ liệu thời gian thực, tính an toàn và nguy cơ bịa địa điểm.

Quá trình huấn luyện thuận lợi nhất trên Linux có GPU NVIDIA khoảng 16 GB VRAM,
chẳng hạn Google Colab hoặc Kaggle. Laptop RTX 4050 6 GB vẫn có thể fine-tune
Qwen3-4B bằng QLoRA trong WSL2 với batch size 1, gradient accumulation 16,
context 512 và LoRA `r=8`; thời gian chạy sẽ lâu hơn và cần theo dõi nhiệt độ.

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

Dataset do generator tạo có `splitGroup` theo điểm đến. Script chia dữ liệu sẽ
giữ toàn bộ một điểm đến trong đúng một tập. Ví dụ, nếu `Đà Nẵng` thuộc
Validation thì không bản ghi Đà Nẵng nào xuất hiện trong Train hoặc Test, kể cả
khi chúng thuộc category khác nhau. Dataset cũ không có `splitGroup` vẫn được
chia theo category để tương thích.

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

Benchmark Qwen3-4B trên GPU 6 GB trước khi chạy dài:

```bash
python -m training.train_qlora \
  --train-dataset training/data/processed/train.jsonl \
  --eval-dataset training/data/processed/validation.jsonl \
  --output-dir artifacts/travelmate-qwen3-4b-lora-v2-benchmark \
  --epochs 1 \
  --max-length 512 \
  --gradient-accumulation-steps 16 \
  --lora-r 8 \
  --lora-alpha 16 \
  --max-steps 20 \
  --save-steps 20
```

`--max-steps` chỉ dùng cho benchmark. Nếu 20 bước hoàn tất mà không hết VRAM,
bỏ tham số này và đổi sang thư mục output v2 chính thức để chạy đủ epoch. Không
dùng chung thư mục benchmark với adapter đã được đánh giá hoặc adapter v1.

### Reinforcement v2

Reinforcement v2 bổ sung các tình huống tiếng lóng ngân sách, yêu cầu còn thiếu,
ngân sách bất khả thi, dữ liệu thời gian thực, bẫy địa danh, an toàn, ngoài phạm
vi và ranh giới giao dịch. Script bắt buộc prompt reinforcement không trùng với
tập challenge:

```bash
python -m training.build_reinforcement_v2 \
  --approved-v1-dir training/data/processed/approved_v1 \
  --challenge training/data/challenge_v1.jsonl \
  --reinforcement-output training/data/reinforcement_v2.jsonl \
  --processed-output-dir training/data/processed/reinforcement_v2 \
  --approved-at YYYY-MM-DD
```

Lần chạy local đã kiểm chứng trên GPU 6 GB dùng một epoch và learning rate thấp
hơn bản v1:

```bash
python -m training.train_qlora \
  --train-dataset training/data/processed/reinforcement_v2/train.jsonl \
  --eval-dataset training/data/processed/reinforcement_v2/validation.jsonl \
  --output-dir artifacts/travelmate-qwen3-4b-lora-v2-expanded \
  --epochs 1 \
  --max-length 512 \
  --learning-rate 1e-4 \
  --gradient-accumulation-steps 16 \
  --lora-r 8 \
  --lora-alpha 16 \
  --save-steps 20
```

Reinforcement được ghép vào train; validation và test v1 giữ nguyên. Challenge
chỉ dùng để đánh giá, tuyệt đối không ghép vào train để tránh rò rỉ dữ liệu.

### Grounding và reinforcement v3

V3 bổ sung hai lớp bảo vệ: dữ liệu hội thoại cho các ca thiếu thông tin, ngoài
phạm vi, giao dịch, realtime và an toàn; cùng dữ liệu lịch trình JSON chỉ được
tham chiếu `placeId` thuộc danh mục điểm đến. Challenge vẫn chỉ dùng để chấm và
script sẽ dừng nếu phát hiện prompt bị trùng:

```bash
python -m training.build_training_v3 \
  --processed-v2-dir training/data/processed/reinforcement_v2 \
  --challenge training/data/challenge_v1.jsonl \
  --reinforcement-output training/data/reinforcement_v3.jsonl \
  --processed-output-dir training/data/processed/grounded_v3 \
  --approved-at YYYY-MM-DD
```

Dataset hiện gồm 1.820 mẫu train, 160 validation và 160 test. Trong số mẫu mới
có 200 hội thoại guardrail, 480 lịch trình train và 80 lịch trình validation/
test trên 20 điểm đến. Train local đã dùng cấu hình sau:

```bash
python -m training.train_qlora \
  --train-dataset training/data/processed/grounded_v3/train.jsonl \
  --eval-dataset training/data/processed/grounded_v3/validation.jsonl \
  --output-dir artifacts/travelmate-qwen3-4b-lora-v3-grounded \
  --epochs 1 \
  --max-length 512 \
  --learning-rate 8e-5 \
  --gradient-accumulation-steps 16 \
  --lora-r 8 \
  --lora-alpha 16 \
  --save-steps 20
```

Model chỉ sinh `day`, `period`, `kind` và `placeId`. Backend kiểm tra schema,
từ chối ID ngoài danh mục rồi ánh xạ ID hợp lệ sang tên địa điểm chuẩn. Không
đưa tên địa điểm tự do do model sinh thẳng vào lịch trình của người dùng.

### Hội thoại tự nhiên v4

V4 bổ sung hội thoại bốn lượt để model học cách nhớ ngữ cảnh, hỏi từng tham số,
tiếp nhận việc người dùng sửa ý, nói ngắn gọn và giữ cách xưng hô `mình - bạn`.
Không dùng Markdown vì giao diện mobile hiện hiển thị text thường:

```bash
python -m training.build_conversation_v4 \
  --processed-v3-dir training/data/processed/grounded_v3 \
  --challenge training/data/challenge_v1.jsonl \
  --reinforcement-output training/data/reinforcement_v4.jsonl \
  --processed-output-dir training/data/processed/natural_v4 \
  --approved-at YYYY-MM-DD
```

Bộ mới có 240 hội thoại: 200 train, 20 validation và 20 test. Khi ghép với v3,
tổng phân bố là 2.020/180/180. Mỗi phản hồi assistant được audit để không quá
320 ký tự, không có Markdown và chỉ hỏi tối đa một câu. Prompt challenge không
được đưa vào bất kỳ split nào.

Sau khi review mẫu thủ công, có thể train candidate v4 từ base model trên toàn
bộ train kết hợp. Không chỉ train tiếp 200 mẫu mới vì dễ quên schema/guardrail
đã học ở v3:

```bash
python -m training.train_qlora \
  --train-dataset training/data/processed/natural_v4/train.jsonl \
  --eval-dataset training/data/processed/natural_v4/validation.jsonl \
  --output-dir artifacts/travelmate-qwen3-4b-lora-v4-natural \
  --epochs 1 \
  --max-length 512 \
  --learning-rate 6e-5 \
  --gradient-accumulation-steps 16 \
  --lora-r 8 \
  --lora-alpha 16 \
  --save-steps 20
```

Các mẫu v4 dùng system prompt huấn luyện rút gọn để toàn bộ hội thoại nhiều lượt
nằm trong giới hạn 512 token. Pipeline sẽ dừng trước khi tải model nếu prompt đã
chiếm hết giới hạn và làm mất completion. Adapter mặc định vẫn là v3 cho đến khi
candidate v4 vượt structured test, challenge và đánh giá hội thoại nhiều lượt.

Pipeline dùng NF4 4-bit, LoRA trên toàn bộ lớp tuyến tính và chỉ tính loss cho
phần trả lời của assistant. Checkpoint, metric và cấu hình lần chạy được lưu
cùng adapter. Mặc định checkpoint được lưu mỗi 20 bước và giữ lại ba bản gần
nhất để hạn chế mất tiến trình khi runtime Colab bị reset. Sau khi dựng lại môi
trường và mount đúng thư mục Drive, tiếp tục lần chạy bằng cùng tham số và thêm:

```bash
--resume-from-checkpoint
```

Callback lưu định kỳ vẫn dùng `--save-steps` của lần chạy mới nếu checkpoint cũ
được tạo với chu kỳ lưu khác.

## 3. Đánh giá

Sinh phản hồi cho tập Test:

```bash
python -m training.generate_predictions \
  --dataset training/data/processed/test.jsonl \
  --adapter-path artifacts/travelmate-qwen3-4b-lora \
  --output training/outputs/test_predictions.jsonl \
  --resume
```

`--resume` ghi từng phản hồi xuống file ngay sau khi sinh và bỏ qua các ID đã
có, giúp tiếp tục đánh giá khi runtime bị reset.

Chấm độ phủ, phản hồi rỗng và các hành vi đã gán trong dataset:

```bash
python -m training.evaluate_predictions \
  --dataset training/data/processed/test.jsonl \
  --predictions training/outputs/test_predictions.jsonl \
  --output training/outputs/evaluation_report.json
```

Sau mỗi lần fine-tune, đánh giá riêng bộ challenge:

```bash
python -m training.generate_predictions \
  --dataset training/data/challenge_v1.jsonl \
  --adapter-path artifacts/travelmate-qwen3-4b-lora \
  --output training/outputs/challenge_predictions.jsonl \
  --resume

python -m training.evaluate_predictions \
  --dataset training/data/challenge_v1.jsonl \
  --predictions training/outputs/challenge_predictions.jsonl \
  --output training/outputs/challenge_report.json
```

Với v3, sinh và chấm riêng 40 ca lịch trình cấu trúc chưa xuất hiện trong train:

```bash
python -m training.generate_predictions \
  --dataset training/data/processed/grounded_v3/structured_test.jsonl \
  --adapter-path artifacts/travelmate-qwen3-4b-lora-v3-grounded \
  --output training/outputs/structured_test_predictions.jsonl \
  --max-new-tokens 512 \
  --resume

python -m training.evaluate_structured_predictions \
  --dataset training/data/processed/grounded_v3/structured_test.jsonl \
  --predictions training/outputs/structured_test_predictions.jsonl \
  --output training/outputs/structured_test_report.json
```

Điểm tự động không thay thế đánh giá thủ công. Cần đọc từng lịch trình để kiểm
tra tính hợp lý, độ đúng của thông tin và mức hữu ích đối với người dùng. Toàn
bộ 20 phản hồi challenge cần được chấm độ đúng, hữu ích, an toàn, tự nhiên và
tuân thủ yêu cầu theo thang 1–5.

## 4. Dùng adapter trong AI Service

```env
LLM_PROVIDER=local
LOCAL_MODEL_ID=Qwen/Qwen3-4B
LOCAL_ADAPTER_PATH=artifacts/travelmate-qwen3-4b-lora-v3-grounded
LOCAL_MODEL_LOAD_IN_4BIT=true
```

Không commit thư mục `artifacts`, `training/data/processed`, `training/outputs`
hoặc file trọng số lên Git. Chỉ commit mã nguồn, notebook không chứa output,
dataset được phép chia sẻ và báo cáo thống kê cần thiết.
