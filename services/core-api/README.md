# TravelMate Core API

REST API chính của TravelMate, xây dựng bằng Java 21, Spring Boot 3.3, Spring Security,
Spring Data JPA/Hibernate và SQLite.

## Trách nhiệm

- Đăng ký, đăng nhập, JWT access/refresh token và hồ sơ người dùng.
- Chuyến đi, thành viên, phân quyền OWNER/EDITOR/VIEWER và liên kết chia sẻ.
- Lịch trình, hoạt động, chi phí, chia tiền và địa điểm đã lưu.
- Lưu lịch sử chat và chuyển ngữ cảnh chuyến đi sang AI Service.
- Cung cấp OpenAPI/Swagger cho Mobile và kiểm thử tích hợp.

Mobile chỉ gọi Core API. API key và logic provider AI không được đưa vào ứng dụng.

## SQLite

Cấu hình mặc định:

```yaml
spring:
  datasource:
    url: jdbc:sqlite:./data/travelmate.db
    driver-class-name: org.sqlite.JDBC
  jpa:
    properties:
      hibernate:
        dialect: org.hibernate.community.dialect.SQLiteDialect
```

Ứng dụng dùng một kết nối ghi, bật foreign key, WAL, `busy_timeout=5000` và lưu file tại
`data/travelmate.db`. Thư mục `data` không được commit; file `.gitkeep` chỉ giữ cấu trúc thư
mục sau khi clone.

## Chạy local

Yêu cầu JDK 21:

```powershell
.\mvnw.cmd test
.\mvnw.cmd spring-boot:run
```

Nếu AI Service chạy ở địa chỉ khác:

```powershell
$env:APP_AI_SERVICE_URL='http://127.0.0.1:8000/internal/v1/ai'
.\mvnw.cmd spring-boot:run
```

Local mặc định không bắt xác minh email để nhóm demo mà không cần SMTP. Production bật:

```powershell
$env:APP_AUTH_REQUIRE_EMAIL_VERIFICATION='true'
```

Swagger UI: `http://localhost:8080/swagger-ui.html`

## Cấu trúc

Mỗi domain dùng chuỗi `controller → service → repository → entity/dto`. Các domain chính:
`auth`, `user`, `trip`, `itinerary`, `expense`, `place`, `ai` và `admin`.
