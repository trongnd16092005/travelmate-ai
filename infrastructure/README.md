# Infrastructure

Cấu hình chạy Core API và AI Service bằng Docker Compose. Core API lưu dữ liệu bền vững
trong SQLite volume `core-data`; ứng dụng mobile chạy bằng Expo trên máy phát triển và chỉ
kết nối tới Core API.

## Khởi động

Từ thư mục gốc:

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infrastructure/compose.yaml up --build
```

Các địa chỉ mặc định:

- Core Swagger: `http://localhost:8080/swagger-ui.html`
- Core health: `http://localhost:8080/actuator/health`
- AI Swagger: `http://localhost:8000/docs`
- AI health: `http://localhost:8000/internal/v1/health`

SQLite nằm tại `/app/data/travelmate.db` trong container và được gắn với Docker volume
`core-data`, vì vậy dữ liệu không mất khi container được tạo lại.
