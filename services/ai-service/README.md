# TravelMate AI Service

Dịch vụ FastAPI phụ trách chatbot và các tính năng AI. Chatbot hỗ trợ `mock`
để kiểm tra tích hợp, `gemini` để demo qua Gemini API và `local` để chạy
Qwen3-4B cùng LoRA adapter đã fine-tune.

## Chạy thành quả đã train (không cần train lại)

Repository chứa sẵn adapter production tại
`artifacts/travelmate-qwen3-4b-lora-v10-reasoning-guarded`. Trọng số adapter
được quản lý bằng Git LFS; đây là LoRA v9 đã vượt các bộ regression, kết hợp
với state, grounding, guardrail và guarded-reasoning policy v10 trong runtime.

Yêu cầu:

- Git LFS để tải file trọng số khi clone.
- Python 3.12.
- GPU NVIDIA/CUDA được khuyến nghị cho Qwen3-4B 4-bit. Không cần chạy bất kỳ
  script nào trong `training/`.
- Kết nối Internet ở lần chạy đầu để Transformers tải model nền
  `Qwen/Qwen3-4B`; repository chỉ chứa LoRA adapter đã fine-tune.

Clone và tải adapter:

```powershell
git lfs install
git clone https://github.com/trongnd16092005/travelmate-ai.git
Set-Location travelmate-ai
git switch feature/ai-itinerary-generation
git lfs pull
```

Khởi động inference:

```powershell
Set-Location services/ai-service
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[local-llm]"
Copy-Item .env.example .env
```

Trong `.env`, đổi provider sang local và giữ nguyên đường dẫn adapter:

```dotenv
LLM_PROVIDER=local
LOCAL_MODEL_ID=Qwen/Qwen3-4B
LOCAL_ADAPTER_PATH=artifacts/travelmate-qwen3-4b-lora-v10-reasoning-guarded
```

Sau đó chạy:

```powershell
uvicorn app.main:app --reload --port 8000
```

Kiểm tra `http://localhost:8000/internal/v1/health` và Swagger UI tại
`http://localhost:8000/docs`. Mobile/Expo Web trỏ tới:

```dotenv
EXPO_PUBLIC_AI_SERVICE_URL=http://localhost:8000/internal/v1
```

Nếu chạy mobile trên điện thoại thật, thay `localhost` bằng IP LAN của máy
chạy AI Service. Nếu máy không đủ tài nguyên để nạp Qwen3-4B, giữ
`LLM_PROVIDER=mock` để làm giao diện hoặc dùng URL của một AI Service đã được
deploy; không cần và cũng không nên train lại trên máy UX/UI.

Có thể xác minh file tải về bằng SHA-256:

| File | SHA-256 |
|---|---|
| `adapter_model.safetensors` | `5CCFA8B8372EF1756806D198F610B8A28CD5DB6DB790A715DC666DE692E8975B` |
| `tokenizer.json` | `BE75606093DB2094D7CD20F3C2F385C212750648BD6EA4FB2BF507A6A4C55506` |

## Thiết lập local

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`

Health check: `http://localhost:8000/internal/v1/health`

Chat API: `POST http://localhost:8000/internal/v1/ai/chat`

Itinerary API: `POST http://localhost:8000/internal/v1/ai/itineraries/generate`

Ví dụ request:

```json
{
  "message": "Ngày thứ hai ở Đà Nẵng nên đi đâu?",
  "history": [],
  "tripContext": {
    "destination": "Đà Nẵng",
    "budgetVnd": 5000000,
    "numPeople": 2
  }
}
```

Itinerary API kiểm tra các trường bắt buộc trước khi gọi mô hình. Nếu thiếu
thông tin, API trả `status=needs_clarification` cùng danh sách câu hỏi. Khi đủ
điểm đến, số ngày, số người và ngân sách, API trả `status=ready` với lịch trình
JSON. Phần chia ngân sách được Python tính lại để tổng luôn đúng bằng ngân sách
người dùng cung cấp.

Ví dụ request:

```json
{
  "destination": "Đà Nẵng",
  "durationDays": 3,
  "numPeople": 2,
  "budgetVnd": 5000000,
  "preferences": ["biển", "ẩm thực"]
}
```

## Demo bằng Gemini

Tạo API key trong Google AI Studio, sau đó sao chép file cấu hình:

```powershell
Copy-Item .env.example .env
```

Chỉnh hai dòng sau trong `.env`:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key
```

Không đưa file `.env` hoặc API key vào Git. Khởi động lại FastAPI sau khi đổi
cấu hình. Model mặc định là `gemini-3.6-flash`; có thể đổi bằng
`GEMINI_MODEL`.

## Chạy adapter khác để nghiên cứu

Không cần cài dependency nặng nếu chỉ dùng chế độ `mock`. Để thử một adapter
khác ngoài bản production:

```powershell
python -m pip install -e ".[local-llm]"
Copy-Item .env.example .env
```

Trong `.env`, đặt `LLM_PROVIDER=local` và đổi `LOCAL_ADAPTER_PATH`. Chỉ adapter
production v10 được đưa vào repository; các candidate/checkpoint nghiên cứu
khác vẫn không được commit. Hướng dẫn huấn luyện nằm tại
[`training/README.md`](training/README.md).

Nếu WSL rơi về `networkingMode VirtioProxy` và không forward được cổng sang
Windows, chạy AI Service trong WSL ở cổng `8002`, rồi mở proxy trên Windows:

```powershell
python scripts/wsl_demo_proxy.py --port 8001 --target-port 8002
```

Expo Web tiếp tục gọi `http://localhost:8001/internal/v1`. Qwen được giữ trong
GPU của WSL; proxy chỉ chuyển tiếp request và không tải lại model mỗi lượt.
