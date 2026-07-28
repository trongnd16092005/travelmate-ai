# Infrastructure

Cấu hình chạy MySQL, Core API và AI Service bằng Docker Compose. Ứng dụng
mobile chạy bằng Expo trên máy phát triển và kết nối tới Core API.

## Khởi động

Từ thư mục gốc:

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infrastructure/compose.yaml up --build
```

Các địa chỉ mặc định:

- Core API: `http://localhost:8080/api/v1/health`
- AI Swagger: `http://localhost:8000/docs`
- MySQL: `localhost:3306`
