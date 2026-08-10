---
base_model: Qwen/Qwen3-4B
library_name: peft
model_name: travelmate-qwen3-4b-lora-v12-grounded-conversation-r3
tags:
- base_model:adapter:Qwen/Qwen3-4B
- lora
- sft
- transformers
- trl
license: apache-2.0
pipeline_tag: text-generation
---

# TravelMate Qwen3-4B LoRA v12-r3

Adapter production của TravelMate AI, fine-tune từ
[Qwen/Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B) bằng TRL/PEFT. Đây là
artifact inference; người dùng không cần train lại.

## Cách chạy

Từ thư mục `services/ai-service`, cài dependencies local rồi cấu hình:

```dotenv
LLM_PROVIDER=local
LOCAL_MODEL_ID=Qwen/Qwen3-4B
LOCAL_ADAPTER_PATH=artifacts/travelmate-qwen3-4b-lora-v12-grounded-conversation-r3
```

Sau đó chạy `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Base model được
tải từ Hugging Face ở lần đầu; file adapter trong thư mục này được lấy qua Git
LFS. Xem hướng dẫn đầy đủ tại `services/ai-service/README.md`.

## Phạm vi và guardrail

- Hội thoại du lịch tiếng Việt grounded theo catalog 34 tỉnh/thành.
- Không dùng adapter độc lập để khẳng định giá vé, giờ mở cửa, thời tiết hay
  tình trạng dịch vụ. Các dữ kiện động phải đi qua retrieval/guardrail runtime.
- Renderer, validator và itinerary whitelist trong AI Service là thành phần bắt
  buộc của bản production.

## Kết quả phát hành

- Grounded current province/catalog/realtime: `102/102` cho từng cổng.
- Nationwide structured itinerary: `34/34`.
- Demo runtime: `20/20`.
- SHA-256 `adapter_model.safetensors`:
  `C9295E454A28ABC71875EECD00A73A60B92C3B9506DA2350AA1E6E0E7C2B45AC`.

## Framework lúc train

- PEFT 0.20.0
- TRL: 0.29.1
- Transformers: 5.14.1
- Pytorch: 2.11.0+cu128
- Datasets: 4.8.5
- Tokenizers: 0.22.2
