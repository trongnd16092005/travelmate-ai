# TravelMate AI Mobile

Ứng dụng di động native của TravelMate AI, xây bằng Expo SDK 54, React Native và Expo Router. SDK 54 được chọn để chạy trực tiếp bằng Expo Go trên iPhone vật lý trong giai đoạn chuyển tiếp SDK hiện tại. Ứng dụng kết nối Core API tại `services/core-api` và AI service tại `services/ai-service` trong monorepo.

## Tính năng

- Đăng ký, đăng nhập, quên/đặt lại/đổi mật khẩu và lưu phiên bằng SecureStore.
- Trang tổng quan, danh sách chuyến đi và chi tiết hành trình.
- Tạo chuyến đi, sinh lịch trình AI, đánh dấu hoạt động hoàn thành.
- Quản lý chi phí và theo dõi ngân sách.
- Trợ lý AI hiểu chuyến đi đang chọn và giữ ngữ cảnh hội thoại.
- Bản đồ native với địa điểm do AI gợi ý.
- Hồ sơ cá nhân và cập nhật thông tin tài khoản.

## Chạy với Expo Go

1. Chạy backend ở cổng `8080` và AI ở cổng `8000`.
2. Điện thoại và máy tính phải dùng cùng một mạng Wi-Fi.
3. Trong thư mục này chạy:

   ```powershell
   npm install
   npm run start:lan
   ```

4. Mở Expo Go trên điện thoại và quét mã QR.

Trong chế độ phát triển, ứng dụng tự lấy IP máy tính từ địa chỉ Metro để gọi backend. Nếu mạng có cấu hình đặc biệt, tạo file `.env` từ `.env.example` rồi điền IP LAN thủ công:

```env
EXPO_PUBLIC_API_URL=http://192.168.1.10:8080
```

Sau khi thay `.env`, khởi động lại bằng `npx expo start --lan --clear`.

## Kiểm tra dự án

```powershell
npm run typecheck
npm run lint
npm run doctor
npm run export:android
npm run export:ios
```

## Cấu trúc chính

- `src/app`: route và màn hình Expo Router.
- `src/components`: component giao diện dùng chung.
- `src/context`: trạng thái đăng nhập và chuyến đi.
- `src/lib`: API client, kiểu dữ liệu và lưu phiên bảo mật.
- `src/constants`: design tokens và ánh xạ ảnh địa danh.
- `assets/images`: ảnh du lịch được đóng gói trong ứng dụng.
