# TravelMate — Báo cáo kiểm tra demo ngày 10/08/2026

## Kết luận

**Có thể demo đầy đủ kịch bản chính trên web sau khi warm-up AI**, gồm đăng nhập, tạo chuyến đi, chat với TravelMate AI, sinh lịch trình 3 ngày, lưu lịch trình vào Core API và hiển thị lại trên giao diện.

Ứng dụng **chưa nên xem là production-ready hoàn toàn**. Luồng đăng ký tài khoản mới, bản đồ tương tác trên web và một số chức năng AI phụ vẫn cần hoàn thiện trước khi demo không có người kỹ thuật hỗ trợ.

## Môi trường đã chạy

- Web/Expo: `http://localhost:8081`
- Core API: `http://localhost:8080/api/v1`
- AI service: `http://localhost:8001/internal/v1`
- AI provider: `local`
- Base model: `Qwen/Qwen3-4B`
- Runtime/model version trả về: `v10`
- Adapter: `services/ai-service/artifacts/travelmate-qwen3-4b-lora-v10-reasoning-guarded`
- Database demo: H2 file local (fallback vì Docker/MySQL không khả dụng trên máy kiểm thử)

AI hiện dùng Qwen local, không gọi Gemini. V10 là adapter/policy guarded-reasoning của TravelMate; README của AI service ghi rõ trọng số LoRA nền bắt nguồn từ lần train v9 và được đóng gói với policy runtime v10.

## Kết quả kiểm thử

| Hạng mục | Trạng thái | Kết quả |
|---|---|---|
| AI unit/integration tests | PASS | `150 passed` |
| Core API compile | PASS | Maven compile thành công |
| Web khởi động | PASS | Trang đăng nhập và các tab chính tải được |
| Đăng nhập | PASS | Đăng nhập tài khoản demo thành công |
| Tạo chuyến đi | PASS | Tạo “Demo Đà Nẵng 3 ngày”, 2 người, ngân sách 5 triệu |
| Chat AI end-to-end | PASS | Web → Core API → Qwen local → trả lời và lưu hội thoại |
| Sinh lịch trình bằng AI | PASS | Qwen sinh đủ 3 ngày, 9 hoạt động; Core API lưu DB và web hiển thị lại |
| Bản đồ trên web | PARTIAL | Có màn preview cho UX/UI; bản đồ tương tác đầy đủ chỉ chạy trên mobile native |
| Đăng ký tài khoản mới | PARTIAL | Backend yêu cầu xác minh email nhưng frontend đang cố auto-login ngay; cần SMTP hoặc chế độ demo bypass |
| AI gợi ý địa điểm/tối ưu lịch trình | BLOCKED | Core API vẫn có endpoint proxy nhưng AI service hiện chưa cung cấp route tương ứng |
| Core health public | PARTIAL | `/api/v1/health` trả `403`; actuator/service health riêng vẫn hoạt động |

## Thay đổi được thực hiện khi kiểm thử

- Sửa URL Core API trên web để tránh lặp `/api/v1/api/v1`.
- Bổ sung storage phù hợp riêng cho web và native.
- Bổ sung màn bản đồ preview cho web để UX/UI có thể chạy dự án.
- Cho phép Core API chạy bằng H2 local phục vụ demo khi Docker/MySQL không có sẵn.
- Đồng bộ contract Core API ↔ AI service:
  - base path `/internal/v1/ai`;
  - route chat và sinh lịch trình;
  - payload camelCase và cấu trúc `tripContext`;
  - parse response `plan.days` và lưu hoạt động;
  - tăng timeout sinh lịch trình local từ 30 lên 120 giây.

## Kịch bản demo đề xuất

1. Khởi động AI service trước và gọi một request warm-up.
2. Khởi động Core API với `APP_AI_SERVICE_URL=http://localhost:8001/internal/v1/ai` nếu AI chạy cổng 8001.
3. Khởi động Expo web cổng 8081.
4. Đăng nhập tài khoản demo đã kích hoạt.
5. Tạo chuyến đi hoặc mở “Demo Đà Nẵng 3 ngày”.
6. Mở TravelMate AI và hỏi “Gợi ý món địa phương”.
7. Trong chi tiết chuyến đi, bấm “Để AI tạo lịch trình”.
8. Chờ khoảng 30–90 giây tùy lần đầu tải model; xác nhận đủ ngày và hoạt động.
9. Mở tab Chi tiêu và tab Bản đồ preview để giới thiệu phần UI còn lại.

## Lưu ý trước buổi demo

- Lần chạy đầu cần tải khoảng 8,04 GB model Qwen từ Hugging Face; nên tải và warm-up trước buổi demo. Các lần sau dùng cache local.
- Máy kiểm thử dùng RTX 4050 Laptop 6 GB và chế độ 4-bit; chat nhanh sau warm-up, sinh lịch trình dài hơn.
- Luồng chat từng trả “2 ngày” khi chuyến đi hiển thị 3 ngày do cách AI suy ra chênh lệch ngày; cần sửa quy tắc tính số ngày inclusive trong chat để tránh lời đáp không nhất quán.
- Không demo đăng ký mới nếu chưa cấu hình SMTP/xác minh email hoặc thêm demo bypass rõ ràng.
- Không quảng bá bản đồ web là tương tác đầy đủ; đây là preview cho UX/UI.
- Một Gemini API key từng tồn tại trong file `.env` local dù provider đang là Qwen. Key đã được xóa khỏi máy kiểm thử; cần **revoke/rotate key cũ** để đảm bảo an toàn.
- Không commit mật khẩu, API key, token hoặc model cache Hugging Face lên Git.

## Bằng chứng

- AI health: `status=ok`
- Chat response: `provider=local`, `modelVersion=v10`
- Sinh lịch trình: `POST /internal/v1/ai/itineraries/generate` trả `200 OK`
- UI hiển thị 3 ngày từ 17/08/2026 đến 19/08/2026, tổng cộng 9 hoạt động.

