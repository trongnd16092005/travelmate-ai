# Backend handoff cho phần AI

Tài liệu này ghi riêng những thay đổi nằm ngoài phạm vi AI Service để thành viên
backend review và tự đưa vào nhánh backend. Người phụ trách AI không cần nhận
ownership các file Java bên dưới.

## Contract Core API → AI Service

Core API cần cấu hình base URL:

```yaml
app:
  ai-service-url: http://127.0.0.1:8000/internal/v1/ai
```

Dùng `127.0.0.1` thay cho `localhost` để tránh JVM phân giải sang IPv6 `::1`
trong khi FastAPI demo đang bind IPv4 tại `0.0.0.0:8000`.

Các endpoint AI Service đang tồn tại:

| Chức năng | Method và path |
|---|---|
| Chat | `POST /internal/v1/ai/chat` |
| Sinh lịch trình | `POST /internal/v1/ai/itineraries/generate` |
| Gợi ý địa điểm bản đồ | `POST /internal/v1/ai/suggest-places` |

AI Service hiện không có endpoint `optimize-itinerary`. Backend cần bỏ route
proxy tương ứng hoặc chỉ bổ sung lại sau khi hai bên thống nhất contract.

## 1. Sinh lịch trình

Request gửi từ Core API sang AI Service phải dùng camelCase:

```json
{
  "destination": "Đà Nẵng",
  "durationDays": 3,
  "startDate": "2026-08-20",
  "endDate": "2026-08-22",
  "budgetVnd": 5000000,
  "numPeople": 2,
  "preferences": ["RELAXATION", "ẩm thực"],
  "notes": "Đi cùng gia đình"
}
```

Danh sách ngày nằm tại `plan.days`, không nằm trực tiếp ở root. Mỗi activity có
các trường:

```json
{
  "period": "morning",
  "kind": "visit",
  "title": "Tham quan bán đảo Sơn Trà",
  "placeId": "vn-48:ban-dao-son-tra",
  "placeName": "bán đảo Sơn Trà",
  "notes": null
}
```

Mapping backend cần áp dụng:

| `kind` từ AI | `ActivityType` backend |
|---|---|
| `visit` | `SIGHTSEEING` |
| `meal` | `FOOD` |
| `travel` | `TRANSPORT` |
| `rest`, `free_time` | `OTHER` |

Nếu `placeName` trùng một bản ghi Place, backend có thể gắn quan hệ `Activity.place`.
Nếu không tìm thấy thì vẫn phải lưu `title`; không được đổi tên hoạt động thành
`OTHER`. AI không trả giá vé hoặc chi phí ước tính cho từng địa điểm.

Các file backend đang có thay đổi phục vụ contract này:

- `services/core-api/src/main/java/com/travelmate/domain/ai/service/AIProxyService.java`
- `services/core-api/src/main/java/com/travelmate/domain/place/repository/PlaceRepository.java`
- `services/core-api/src/main/resources/application.yml`

## 2. Chat

Payload backend gửi sang AI Service:

```json
{
  "message": "Gợi ý lịch trình cho tôi",
  "history": [
    { "role": "user", "content": "Tôi muốn đi Đà Nẵng" }
  ],
  "tripContext": {
    "destination": "Đà Nẵng",
    "startDate": "2026-08-20",
    "endDate": "2026-08-22",
    "budgetVnd": 5000000,
    "numPeople": 2
  }
}
```

Không dùng hai field cũ `chat_history` và `trip_context` dạng chuỗi.

Core API phải chuyển tiếp hai trường metadata trong response AI thay vì tự gán
giá trị mặc định:

```json
{
  "reply": "Mình chỉ hỗ trợ các nội dung liên quan đến du lịch.",
  "isOutOfScope": true,
  "suggestedQuestions": ["Bạn muốn lên lịch trình cho tỉnh nào?"]
}
```

`AIProxyService.chat` hiện đã đọc `isOutOfScope` và `suggestedQuestions` từ
FastAPI rồi trả lại cho mobile. Khi AI Service không gửi hai trường này,
backend vẫn fallback an toàn về `false` và danh sách rỗng.

Khi FastAPI mất kết nối hoặc đang nạp lại model, fallback chat dùng thông báo
`AI đang khởi động hoặc mất kết nối` để phản ánh đúng trạng thái; mobile không
nên hiển thị badge online tĩnh trong trường hợp này.

## 3. Gợi ý địa điểm bản đồ

Request Core API nhận và chuyển tiếp:

```json
{
  "city": "Đà Nẵng",
  "type": null,
  "specialNote": "Địa điểm nổi bật",
  "count": 3
}
```

`budget` và `tripId` không còn thuộc contract này. `count` hợp lệ từ 1 đến 6.
Response chứa địa điểm từ catalog cùng `latitude`, `longitude`, `address`,
`mapUrl` và `source`. Response không có `estimatedCostVnd`.

Các file backend đang có thay đổi phục vụ contract này:

- `services/core-api/src/main/java/com/travelmate/domain/ai/dto/SuggestPlacesRequest.java`
- `services/core-api/src/main/java/com/travelmate/domain/ai/service/AIProxyService.java`

## 4. Route backend đang đề nghị bỏ

`POST /api/v1/ai/optimize-itinerary/{tripId}` đang proxy đến một endpoint không
tồn tại trong AI Service và hiện không được mobile gọi. Thay đổi hiện tại đã bỏ
route khỏi:

- `services/core-api/src/main/java/com/travelmate/domain/ai/controller/AIController.java`
- `services/core-api/src/main/java/com/travelmate/domain/ai/service/AIProxyService.java`

Backend có thể giữ route nếu muốn phát triển sau, nhưng không nên đưa vào phạm
vi demo hiện tại khi chưa có implementation phía AI.

## 5. Kiểm tra dành cho backend

Đã xác nhận `mvnw.cmd clean test` compile thành công. Repository Core API hiện
không có Java test source, vì vậy backend nên bổ sung tối thiểu test cho ba
contract trên trước khi merge.

Không cần migration để bỏ `priceRange` hoặc `openingHours`. Các cột cũ nên được
giữ để tương thích database; chỉ không dùng chúng trong luồng AI hiện tại.
