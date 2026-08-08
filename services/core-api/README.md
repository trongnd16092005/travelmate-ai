# 🌍 TravelMate AI - Core API (Backend)

Đây là mã nguồn Backend chính (Core API) của dự án **TravelMate AI** - Hệ thống Hỗ trợ Quản lý Du lịch thông minh tích hợp Trí tuệ nhân tạo. Backend được xây dựng bằng kiến trúc nguyên khối phân tầng (Layered Monolithic Architecture) để đảm bảo dễ bảo trì và mở rộng trong tương lai.

## 🛠 Công nghệ sử dụng (Tech Stack)
* **Ngôn ngữ:** Java 21
* **Framework:** Spring Boot 3.3.2
* **Cơ sở dữ liệu:** MySQL 8.x
* **Bảo mật:** Spring Security & JWT (JSON Web Token) phiên bản mới nhất
* **ORM:** Spring Data JPA / Hibernate
* **Tài liệu API:** Swagger (OpenAPI 3.0)
* **Khác:** Lombok, Flyway (Migration)

---

## 📂 Cấu trúc thư mục (Project Structure)
Dự án được tổ chức theo cấu trúc phân tầng nghiệp vụ (Domain-Driven Package Structure):

```text
src/main/java/com/travelmate/
 ├── common/         # Chứa các Class dùng chung (Enums, Exception Handler, Response Utils)
 ├── config/         # Cấu hình hệ thống (Swagger, Security, WebMvc,...)
 ├── security/       # Xử lý Logic xác thực JWT, Filters, Authentication
 ├── infrastructure/ # Tích hợp với dịch vụ bên ngoài (AI Proxy Client, 3rd Party APIs)
 └── domain/         # Chứa các nghiệp vụ chính (Phân theo từng nhóm tính năng)
      ├── user/      # Nghiệp vụ tài khoản, xác thực người dùng
      ├── trip/      # Nghiệp vụ chuyến đi, thành viên, phân quyền
      ├── itinerary/ # Nghiệp vụ lịch trình, hoạt động (Activities)
      ├── expense/   # Nghiệp vụ quản lý ngân sách, chia tiền
      └── ai/        # Nghiệp vụ AI Chatbot, Sinh lịch trình tự động
```
*(Bên trong mỗi domain sẽ tuân theo cấu trúc: `controller` -> `service` -> `repository` -> `entity` -> `dto`)*

---

## 🚀 Hướng dẫn cài đặt và chạy (Setup & Run)

### 1. Yêu cầu hệ thống (Prerequisites)
* Đã cài đặt **JDK 21** (Nên dùng Oracle OpenJDK hoặc Amazon Corretto 21).
* Đã cài đặt **MySQL Server** (XAMPP hoặc MySQL Workbench).
* IDE: Khuyên dùng **IntelliJ IDEA**.

### 2. Khởi tạo Cơ sở dữ liệu (Database Setup)
Tạo sẵn một Schema/Database rỗng trong MySQL với tên `travelmate_db` bằng lệnh SQL sau:
```sql
CREATE DATABASE travelmate_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Cấu hình ứng dụng (Application Configuration)
Cấu hình kết nối Database nằm ở file `src/main/resources/application.yml`.
Bạn hãy cập nhật lại `username` và `password` cho khớp với tài khoản MySQL trên máy tính của bạn:
```yaml
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/travelmate_db?useSSL=false&serverTimezone=Asia/Ho_Chi_Minh
    username: root
    password: 123456 # Đổi mật khẩu này
```
*(Lưu ý: Hibernate `ddl-auto: update` đang được bật. Khi chạy lần đầu, Spring Boot sẽ tự động quét các Entity và tạo ra các bảng dữ liệu tương ứng trong MySQL mà không cần script SQL).*

### 4. Chạy dự án (Run the application)

**Cách 1: Chạy bằng IntelliJ IDEA (Khuyên dùng)**
1. Mở thư mục `core-api` bằng IntelliJ.
2. Thiết lập **Project SDK** và **Language Level** thành **Java 21**.
3. Chờ IntelliJ tải xong thư viện Maven.
4. Mở file `TravelMateApplication.java` và bấm nút **Play (Run)** màu xanh.

**Cách 2: Chạy bằng Maven CLI (Terminal)**
Đảm bảo biến môi trường `JAVA_HOME` của bạn đang trỏ tới JDK 21. Chạy lệnh:
```powershell
.\mvnw clean install -DskipTests
.\mvnw spring-boot:run
```

---

## 📖 Tài liệu API (API Documentation)
Khi Server đang chạy, bạn có thể xem và kiểm thử trực tiếp tất cả các REST API (Đã có giao diện mô tả) thông qua Swagger UI:
👉 **URL:** [http://localhost:8080/swagger-ui.html](http://localhost:8080/swagger-ui.html)

---

## 🤝 Hướng dẫn Đóng góp (Git Workflow)
Khi làm việc nhóm, vui lòng tuân thủ quy trình Git sau:
1. Tuyệt đối **không** code trực tiếp và đẩy (push) thẳng lên nhánh `main` hoặc nhánh `backend`.
2. Tạo một nhánh mới từ nhánh `backend` để làm tính năng:
   ```bash
   git checkout -b feature/ten-tinh-nang
   ```
3. Commit code với thông điệp rõ ràng theo chuẩn: `feat: ...`, `fix: ...`, `chore: ...`.
4. Đẩy nhánh của bạn lên GitHub và tạo **Pull Request (PR)** gộp vào nhánh `backend`. Nhờ một thành viên khác vào Review Code trước khi Merge.
