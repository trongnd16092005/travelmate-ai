# Huấn luyện TravelMate Chatbot

Thư mục này chứa pipeline fine-tune `Qwen/Qwen3-4B` bằng QLoRA. Quá trình
huấn luyện nên chạy trên Linux có GPU NVIDIA 16 GB, chẳng hạn Google Colab
hoặc Kaggle. File dữ liệu đi kèm chỉ dùng để kiểm tra pipeline.

## Chuẩn bị dữ liệu

Mỗi dòng trong file JSONL là một cuộc hội thoại theo định dạng `messages`:

```json
{"messages":[{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}]}
```

Trước khi huấn luyện thật, cần mở rộng thành ít nhất 3.000 hội thoại đã được
rà soát. Dữ liệu nên bao phủ tìm chỗ ở, lập lịch trình, ngân sách, câu hỏi cần
làm rõ và từ chối nội dung ngoài phạm vi du lịch.

Kiểm tra file dữ liệu:

```bash
python training/validate_dataset.py training/data/travelmate_train.sample.jsonl
```

## Chạy QLoRA

```bash
python -m pip install -e ".[training]"
python training/train_qlora.py \
  --dataset training/data/travelmate_train.sample.jsonl \
  --output-dir artifacts/travelmate-qwen3-4b-lora \
  --epochs 3
```

Sau khi train, cấu hình AI Service:

```env
LLM_PROVIDER=local
LOCAL_MODEL_ID=Qwen/Qwen3-4B
LOCAL_ADAPTER_PATH=artifacts/travelmate-qwen3-4b-lora
LOCAL_MODEL_LOAD_IN_4BIT=true
```

Không commit thư mục `artifacts` hoặc file trọng số lên Git. Chỉ commit mã
nguồn, cấu hình huấn luyện, thống kê đánh giá và phiên bản dataset phù hợp.
