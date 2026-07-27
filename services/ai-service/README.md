# TravelMate AI Service

Dịch vụ FastAPI phụ trách sinh lịch trình, chatbot và các tính năng AI.

## Thiết lập local

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`

Health check: `http://localhost:8000/internal/v1/health`

