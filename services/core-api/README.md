# TravelMate Core API

REST API trung tâm của TravelMate, xây dựng bằng Spring Boot.

## Chạy local

Khởi động MySQL trước, sau đó:

```powershell
.\mvnw.cmd spring-boot:run
```

Health check: `http://localhost:8080/api/v1/health`

Các cấu hình có thể truyền qua biến môi trường:

- `DB_URL`
- `DB_USERNAME`
- `DB_PASSWORD`
- `AI_SERVICE_URL`
- `SERVER_PORT`

