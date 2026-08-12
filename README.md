# TravelMate AI

TravelMate AI là ứng dụng lập kế hoạch và đồng hành du lịch cho cá nhân hoặc nhóm. Người dùng có thể tạo chuyến đi, để AI dựng lịch trình theo điểm đến/ngày/ngân sách, hỏi đáp theo ngữ cảnh, xem địa điểm trên bản đồ, theo dõi chi phí và chia sẻ chuyến đi.

## Vì sao TravelMate hữu ích?

Lập kế hoạch du lịch thường bị phân tán giữa nhiều ứng dụng: tìm địa điểm, sắp lịch, tính tiền và trao đổi với nhóm. TravelMate gom các bước đó vào một luồng duy nhất, đồng thời dùng AI có dữ liệu nền và kiểm tra đầu ra để hạn chế gợi ý chung chung hoặc sai địa điểm.

## Tính năng chính

- Onboarding mobile, đăng ký/đăng nhập, refresh token và lưu phiên an toàn.
- Tạo và quản lý chuyến đi: điểm đến, ngày đi, ngân sách, số người và phong cách du lịch.
- Sinh lịch trình bằng AI theo ngữ cảnh chuyến đi; lịch trình được kiểm tra schema và lưu vào SQLite.
- Chat với TravelMate AI, giữ lịch sử hội thoại và ngữ cảnh chuyến đi hiện tại.
- Gợi ý địa điểm/ẩm thực từ catalog TravelMate; tọa độ và địa chỉ được xác minh qua OpenStreetMap Nominatim.
- Bản đồ native với marker và thẻ địa điểm có ảnh thật; ảnh điểm đến được lấy/cached từ Wikipedia.
- Theo dõi hoạt động, chi phí và số dư nhóm.
- Chia sẻ chuyến đi bằng public link hoặc mời thành viên với quyền `OWNER`, `EDITOR`, `VIEWER`.
- Thời tiết realtime qua Open-Meteo, có cache và trạng thái “chưa xác minh” khi nguồn không phản hồi.

## Kiến trúc

```text
┌─────────────────────────────┐
│ apps/mobile                  │  Expo + React Native + Expo Router
└──────────────┬──────────────┘
               │ REST / JSON + JWT
┌──────────────▼──────────────┐
│ services/core-api            │  Java 21 + Spring Boot + SQLite
│ auth · trips · itinerary     │
│ expenses · places · sharing │
└──────────────┬──────────────┘
               │ internal AI contract
┌──────────────▼──────────────┐
│ services/ai-service          │  FastAPI + provider adapter
│ grounding · validation       │
│ Groq / Gemini / local Qwen   │
└─────────────────────────────┘
```

Mobile chỉ gọi Core API. API key và logic chọn model nằm trong AI Service, không nằm trong mobile bundle. Core API là nơi xác thực, phân quyền, lưu dữ liệu và chuyển ngữ cảnh cần thiết sang AI.

## Cấu trúc repository

```text
apps/mobile/                 # FE mobile Expo/React Native
services/core-api/            # Backend Spring Boot, SQLite, JWT
services/ai-service/          # AI FastAPI, Groq/Gemini/local Qwen
packages/contracts/           # OpenAPI contract giữa Core và AI
infrastructure/               # Docker Compose
docs/                         # tài liệu bàn giao và kiểm thử
PTTK/                         # phân tích, thiết kế hệ thống
```

## Chạy nhanh trên Windows

Yêu cầu: Node.js 22+, JDK 21, Python 3.12 và Git. Lệnh dưới đây chạy ba tiến trình ở ba terminal riêng.

### 1. AI Service

```powershell
cd services/ai-service
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Trong `.env`, chọn một provider. Groq phù hợp để demo trên máy không có GPU:

```dotenv
LLM_PROVIDER=groq
GROQ_API_KEY=your-key
GROQ_MODEL=llama-3.3-70b-versatile
```

Khởi động:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Kiểm tra: `http://localhost:8000/internal/v1/health`.

### 2. Core API

```powershell
cd services/core-api
.\mvnw.cmd test
.\mvnw.cmd spring-boot:run
```

Core API chạy ở `http://localhost:8080`; SQLite mặc định nằm tại `services/core-api/data/travelmate.db`. Thư mục dữ liệu và file `.env` không được commit.

Swagger: `http://localhost:8080/swagger-ui.html`.

### 3. Mobile

```powershell
cd apps/mobile
npm install
npm run start:lan
```

Quét QR bằng Expo Go trên iPhone/Android. Điện thoại phải cùng Wi‑Fi với máy chạy Metro. Nếu Expo không nhận đúng IP LAN, tạo `apps/mobile/.env` từ `.env.example` và đặt:

```dotenv
EXPO_PUBLIC_API_URL=http://<IP-LAN-CUA-MAY>:8080
```

Sau đó chạy lại `npx expo start --lan --clear`.

### Chạy bằng Docker

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f infrastructure/compose.yaml up --build
```

Compose khởi động Core API và AI Service. Mobile vẫn chạy bằng Expo trên máy phát triển.

## Luồng AI

```text
Người dùng nhập yêu cầu
        ↓
Mobile → Core API (JWT + trip context)
        ↓
AI Service (catalog + prompt + provider)
        ↓
Groq/Gemini/Qwen
        ↓
Schema validator + grounding + budget allocator
        ↓
Core API lưu itinerary/chat vào SQLite
        ↓
Mobile hiển thị kết quả
```

AI Service không cho model tự do tạo `placeId`. Điểm tham quan phải thuộc catalog TravelMate; dữ liệu vị trí dùng Nominatim để kiểm tra. Lịch trình luôn được kiểm tra đủ số ngày, loại hoạt động, địa điểm hợp lệ và tổng ngân sách trước khi trả về.

## API chính

| Nhóm | Endpoint tiêu biểu |
|---|---|
| Auth | `POST /api/v1/auth/register`, `POST /api/v1/auth/login` |
| Trips | `GET/POST /api/v1/trips`, `GET /api/v1/trips/{id}` |
| AI proxy | `POST /api/v1/ai/generate-itinerary` |
| AI chat | `POST /api/v1/ai/chat` |
| AI places | `POST /api/v1/ai/suggest-places` |
| Itinerary | `GET /api/v1/trips/{id}/itinerary` |
| Expenses | `/api/v1/trips/{id}/expenses` |
| Sharing | `/api/v1/trips/{id}/members/invite` |

Contract nội bộ của AI nằm tại [`packages/contracts/openapi/ai-internal.yaml`](packages/contracts/openapi/ai-internal.yaml).

## Kiểm thử

```powershell
# Mobile
cd apps/mobile
npm run typecheck
npm run lint
npm run export:android

# AI
cd services/ai-service
python -m pytest -q

# Core API
cd services/core-api
.\mvnw.cmd test
```

Các kiểm thử tích hợp bao phủ đăng nhập, gọi AI proxy, sinh itinerary, grounding địa điểm, chia sẻ chuyến đi và integrity của SQLite. Khi demo thật, kiểm tra thêm iPhone cùng Wi‑Fi, AI health và Core API trước khi quét QR.

## Bảo mật và triển khai

- Không commit `.env`, API key, refresh token hoặc database demo.
- Đổi `JWT_SECRET` và bật email verification khi triển khai production.
- Đặt AI Service sau Core API; không mở API key cho client mobile.
- Adapter Qwen LoRA nằm trong Git LFS; không cần train lại để chạy inference local.
- Xem hướng dẫn chi tiết tại [`services/core-api/README.md`](services/core-api/README.md), [`services/ai-service/README.md`](services/ai-service/README.md) và [`apps/mobile/README.md`](apps/mobile/README.md).

## Tài liệu

- [`docs/backend-ai-handoff.md`](docs/backend-ai-handoff.md): bàn giao contract và luồng tích hợp.
- [`PTTK/00_TravelMate_AI_PTTK_V2.md`](PTTK/00_TravelMate_AI_PTTK_V2.md): phân tích và thiết kế hệ thống.
- [`services/ai-service/training/README.md`](services/ai-service/training/README.md): dữ liệu, version và đánh giá model.

## License

Dự án phục vụ mục đích học tập và đồ án. Xem [`apps/mobile/LICENSE`](apps/mobile/LICENSE) để biết điều khoản cấp phép hiện tại.
