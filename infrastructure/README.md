# Infrastructure

Cấu hình chạy toàn bộ TravelMate bằng Docker Compose.

## Khởi động

Từ thư mục gốc:

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infrastructure/compose.yaml up --build
```

Các địa chỉ mặc định:

- Web: `http://localhost:3000`
- Core API: `http://localhost:8080/api/v1/health`
- AI Swagger: `http://localhost:8000/docs`
- MySQL: `localhost:3306`
