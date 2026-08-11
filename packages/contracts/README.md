# Integration Contracts

Hợp đồng giao tiếp dùng chung giữa mobile, Core API và AI Service.

- [`openapi/ai-internal.yaml`](openapi/ai-internal.yaml): ba endpoint nội bộ mà
  Core API gọi sang FastAPI (`chat`, `itineraries/generate`, `suggest-places`).
- Mobile chỉ gọi các proxy công khai dưới `/api/v1/ai` của Core API; API key và
  URL AI Service không được đóng gói trong ứng dụng.

Mọi thay đổi ảnh hưởng request/response phải cập nhật đặc tả này cùng code hai
phía trong một nhánh tích hợp.
