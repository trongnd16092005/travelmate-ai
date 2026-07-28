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
