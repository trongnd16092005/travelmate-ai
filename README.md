# TravelMate AI

TravelMate AI là hệ thống hỗ trợ lập kế hoạch và tư vấn du lịch thông minh.

## Cấu trúc repository

```text
.
├── apps/
│   └── mobile/               # Ứng dụng React Native bằng Expo
├── services/
│   ├── core-api/             # REST API chính bằng Spring Boot
│   └── ai-service/           # Dịch vụ AI độc lập bằng FastAPI
├── packages/
│   └── contracts/            # OpenAPI, JSON Schema và dữ liệu mẫu dùng chung
├── infrastructure/           # Docker Compose và cấu hình triển khai
└── PTTKHT/                   # Tài liệu phân tích và thiết kế hệ thống
```

## Luồng giao tiếp

```text
apps/mobile → services/core-api → services/ai-service → LLM provider
                        ↓
                      MySQL
```

Ứng dụng mobile chỉ gọi `core-api`. API chính chịu trách nhiệm xác thực, phân
quyền, truy cập cơ sở dữ liệu và chuyển ngữ cảnh cần thiết sang `ai-service`.

## Bắt đầu nhanh

### Chạy backend bằng Docker

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infrastructure/compose.yaml up --build
```

### Chạy từng thành phần để phát triển

Mobile:

```powershell
Set-Location apps/mobile
Copy-Item .env.example .env
npm install
npm start
```

Ứng dụng sử dụng Expo SDK 57 và yêu cầu Node.js 22.13 trở lên. Khi chạy trên
điện thoại thật, `EXPO_PUBLIC_API_URL` phải dùng IP LAN của máy chạy backend,
không dùng `localhost`.

Core API:

```powershell
Set-Location services/core-api
.\mvnw.cmd spring-boot:run
```

AI service:

```powershell
Set-Location services/ai-service
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Adapter production đã fine-tune được lưu bằng Git LFS trong
`services/ai-service/artifacts/travelmate-qwen3-4b-lora-v10-reasoning-guarded`.
Thành viên chỉ cần chạy inference, không cần train lại; xem hướng dẫn đầy đủ tại
[`services/ai-service/README.md`](services/ai-service/README.md).

Không commit file `.env` hoặc bất kỳ API key nào lên Git.

## Quy trình Git bắt buộc

> **Lưu ý cho thành viên và trợ lý AI:** Trước khi sửa code, luôn chạy
> `git branch --show-current` và đọc phần này. Không commit trực tiếp vào
> `main` hoặc `develop`.

Vai trò của các nhánh:

| Nhánh | Mục đích | Quy tắc |
|---|---|---|
| `main` | Phiên bản ổn định để demo hoặc phát hành | Chỉ nhận Pull Request từ `develop` |
| `develop` | Tích hợp và kiểm thử công việc của cả nhóm | Chỉ nhận Pull Request từ `feature/*` hoặc `fix/*` |
| `feature/*` | Phát triển một chức năng cụ thể | Luôn tạo từ `develop` mới nhất |
| `fix/*` | Sửa lỗi chưa phát hành | Luôn tạo từ `develop` mới nhất |

Luồng chuẩn:

```text
feature/* → develop → main
```

Trước khi bắt đầu một chức năng:

```powershell
git switch develop
git pull origin develop
git switch -c feature/ten-chuc-nang
```

Sau khi hoàn thành:

```powershell
git add .
git commit -m "Tạo màn hình đăng nhập"
git push -u origin feature/ten-chuc-nang
```

Sau đó tạo Pull Request từ `feature/*` vào `develop`. Chỉ tạo Pull Request
từ `develop` vào `main` khi mobile vượt qua lint và typecheck, backend và AI
vượt qua test, luồng tích hợp hoạt động và không có secret trong thay đổi.

### Quy tắc dành cho AI hỗ trợ lập trình

- Phải kiểm tra nhánh hiện tại trước khi tạo hoặc sửa file.
- Không tự commit, merge hoặc push vào `main` hay `develop`.
- Nếu đang ở `main` hoặc `develop`, phải tạo/chuyển sang đúng nhánh
  `feature/*` hoặc `fix/*` trước khi triển khai.
- Không đổi API contract mà chưa cập nhật `packages/contracts`.
- Không đọc, ghi hoặc commit API key, mật khẩu hay file `.env`.
- Không merge khi build, lint hoặc test của phần bị ảnh hưởng chưa thành công.
