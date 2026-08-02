# TravelMate AI Service

Dịch vụ FastAPI phụ trách chatbot và các tính năng AI. Chatbot hỗ trợ hai chế
độ: `mock` để tích hợp không cần tải model và `local` để chạy Qwen3-4B cùng
LoRA adapter đã fine-tune.

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

## Chạy mô hình local

Không cần cài dependency nặng nếu chỉ dùng chế độ `mock`. Để chạy Qwen3-4B:

```powershell
python -m pip install -e ".[local-llm]"
Copy-Item .env.example .env
```

Trong `.env`, đặt `LLM_PROVIDER=local`. Nếu đã fine-tune, đặt
`LOCAL_ADAPTER_PATH` đến thư mục LoRA adapter. Hướng dẫn huấn luyện nằm tại
[`training/README.md`](training/README.md).
