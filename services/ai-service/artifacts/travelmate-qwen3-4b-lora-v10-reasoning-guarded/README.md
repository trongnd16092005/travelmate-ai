---
base_model: Qwen/Qwen3-4B
library_name: peft
model_name: travelmate-qwen3-4b-lora-v10-reasoning-guarded
tags:
- base_model:adapter:Qwen/Qwen3-4B
- lora
- sft
- travel
- vietnamese
pipeline_tag: text-generation
---

# TravelMate Qwen3-4B LoRA — production v10

Đây là adapter production của TravelMate AI. Trọng số LoRA đến từ adapter v9
đã được kiểm chứng; tên v10 thể hiện gói production kết hợp trọng số đó với
state, grounding, guardrail và guarded-reasoning policy v10 trong AI Service.

Adapter không phải model độc lập. Khi inference, AI Service tải model nền
`Qwen/Qwen3-4B`, sau đó nạp `adapter_model.safetensors` bằng PEFT. Không cần
train lại. Xem `services/ai-service/README.md` để cài dependency và chạy API.

Không dùng raw adapter để tự xác nhận giá, thời tiết, giờ mở cửa, tình trạng
dịch vụ hoặc giao dịch. Các lớp kiểm tra trong TravelMate AI Service là một
phần bắt buộc của phiên bản production.
