# TravelMate Mobile

Ứng dụng React Native của TravelMate AI, sử dụng Expo SDK 57, Expo Router và
TypeScript.

## Yêu cầu

- Node.js 22.13 trở lên
- Android Studio để build Android local
- Xcode trên macOS để build iOS local

## Khởi động development server

```powershell
Copy-Item .env.example .env
npm install
npm start
```

`EXPO_PUBLIC_API_URL` phải là địa chỉ backend mà điện thoại truy cập được.
Không dùng `localhost` khi chạy trên thiết bị thật; hãy thay bằng IP LAN của
máy chạy Spring Boot.

Để thử trực tiếp tab AI khi Spring Boot chưa có AI proxy, cấu hình thêm:

```env
EXPO_PUBLIC_AI_SERVICE_URL=http://IP_LAN_CUA_MAY:8000/internal/v1
```

Khởi động FastAPI trước khi gửi tin nhắn. Kết nối trực tiếp này chỉ dành cho
phát triển; bản tích hợp chính thức sẽ gọi AI thông qua Core API.

## Demo trên laptop

Đặt URL AI Service trong `.env` về localhost:

```env
EXPO_PUBLIC_AI_SERVICE_URL=http://localhost:8000/internal/v1
```

Sau khi FastAPI đã chạy ở cổng `8000`, mở một terminal khác:

```powershell
npm run web
```

Expo sẽ mở ứng dụng trong trình duyệt. Tab AI dùng cùng source với bản mobile,
nhưng phần nội dung được giới hạn chiều rộng để trình chiếu trên laptop.

## Development build

```powershell
npm run android
```

Trên macOS:

```bash
npm run ios
```

Kiểm tra source:

```powershell
npm run typecheck
npm run lint
npm run doctor
```
