# TravelMate AI Service

Dịch vụ FastAPI phụ trách chatbot và các tính năng AI. Chatbot hỗ trợ `mock`
để kiểm tra tích hợp, `gemini` để demo qua Gemini API và `local` để chạy
Qwen3-4B cùng LoRA adapter đã fine-tune.

## Chạy thành quả đã train (không cần train lại)

Repository chứa sẵn adapter production tại
`artifacts/travelmate-qwen3-4b-lora-v12-grounded-conversation-r3`. Trọng số
adapter được quản lý bằng Git LFS; đây là Qwen3-4B LoRA v12-r3 đã vượt cổng
grounding toàn quốc, ranh giới realtime và regression runtime.

Yêu cầu:

- Git LFS để tải file trọng số khi clone.
- Python 3.12.
- GPU NVIDIA/CUDA được khuyến nghị cho Qwen3-4B 4-bit. Không cần chạy bất kỳ
  script nào trong `training/`.
- Kết nối Internet ở lần chạy đầu để Transformers tải model nền
  `Qwen/Qwen3-4B`; repository chỉ chứa LoRA adapter đã fine-tune.

Clone và tải adapter:

```powershell
git lfs install
git clone https://github.com/trongnd16092005/travelmate-ai.git
Set-Location travelmate-ai
git switch feature/ai-itinerary-generation
git lfs pull
```

Khởi động inference:

```powershell
Set-Location services/ai-service
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[local-llm]"
Copy-Item .env.example .env
```

Trong `.env`, đổi provider sang local và giữ nguyên đường dẫn adapter:

```dotenv
LLM_PROVIDER=local
LOCAL_MODEL_ID=Qwen/Qwen3-4B
LOCAL_ADAPTER_PATH=artifacts/travelmate-qwen3-4b-lora-v12-grounded-conversation-r3
```

Sau đó chạy:

```powershell
uvicorn app.main:app --reload --port 8000
```

Kiểm tra `http://localhost:8000/internal/v1/health` và Swagger UI tại
`http://localhost:8000/docs`. Mobile/Expo Web trỏ tới:

```dotenv
EXPO_PUBLIC_AI_SERVICE_URL=http://localhost:8000/internal/v1
```

Nếu chạy mobile trên điện thoại thật, thay `localhost` bằng IP LAN của máy
chạy AI Service. Nếu máy không đủ tài nguyên để nạp Qwen3-4B, giữ
`LLM_PROVIDER=mock` để làm giao diện hoặc dùng URL của một AI Service đã được
deploy; không cần và cũng không nên train lại trên máy UX/UI.

Có thể xác minh file tải về bằng SHA-256:

| File | SHA-256 |
|---|---|
| `adapter_model.safetensors` | `5CCFA8B8372EF1756806D198F610B8A28CD5DB6DB790A715DC666DE692E8975B` |
| `tokenizer.json` | `BE75606093DB2094D7CD20F3C2F385C212750648BD6EA4FB2BF507A6A4C55506` |

## Thiết lập local

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`

Health check: `http://localhost:8000/internal/v1/health`

Chat API: `POST http://localhost:8000/internal/v1/ai/chat`

Itinerary API: `POST http://localhost:8000/internal/v1/ai/itineraries/generate`

Ví dụ request:

```json
{
  "message": "Ngày thứ hai ở Đà Nẵng nên đi đâu?",
  "history": [],
  "tripContext": {
    "destination": "Đà Nẵng",
    "budgetVnd": 5000000,
    "numPeople": 2
  }
}
```

Itinerary API kiểm tra các trường bắt buộc trước khi gọi mô hình. Nếu thiếu
thông tin, API trả `status=needs_clarification` cùng danh sách câu hỏi. Khi đủ
điểm đến, số ngày, số người và ngân sách, API trả `status=ready` với lịch trình
JSON. Phần chia ngân sách được Python tính lại để tổng luôn đúng bằng ngân sách
người dùng cung cấp.

## Grounded conversation

Các câu hỏi như “nên đi đâu”, “gợi ý ba điểm” hoặc “ăn gì” không còn để Qwen
tự nhớ tên địa điểm. Runtime nhận diện tên hiện hành/tên tỉnh cũ, truy xuất đúng
catalog 34 tỉnh/thành và dựng câu trả lời từ dữ liệu whitelist. Tỉnh thông
thường giữ ba địa điểm; 12 trung tâm/điểm nóng du lịch có sáu địa điểm runtime.
Nếu người dùng yêu cầu rõ “ba điểm”, runtime vẫn chỉ trả đúng ba. Bộ ba đã audit
dùng cho train/evaluation v11-v12 được giữ nguyên để báo cáo có thể tái lập.
Với những lượt khác cần gọi model, catalog của tỉnh hiện tại được
chèn vào system context; validator thay phản hồi bằng catalog fallback nếu
model đề xuất địa điểm không được phép.

Câu nhập lỗi ngắn có chữ và số dính nhau được hỏi lại thay vì suy diễn. Câu hỏi
về giá vé hoặc giờ hoạt động đi thẳng vào guardrail realtime: AI không tự tạo
con số và hướng người dùng kiểm tra nguồn chính thức của từng địa điểm.

Luồng xử lý hiện tại:

```text
Câu hỏi → nhận diện tỉnh/alias → lấy catalog → Qwen hoặc renderer → validator → trả lời
```

Thời tiết realtime được lấy từ Open-Meteo qua hai bước geocoding và forecast.
Phản hồi chat chỉ hiển thị thông tin thời tiết cần thiết, không hiện tên provider,
URL hay thời điểm truy xuất. Metadata nguồn vẫn được giữ nội bộ để kiểm thử và
truy vết. Kết quả được cache 15 phút; khi timeout, lỗi mạng hoặc không tìm thấy
địa điểm, runtime trả trạng thái chưa xác minh thay vì dùng dữ liệu cũ hoặc để
model đoán.

Cấu hình:

```dotenv
REALTIME_WEATHER_ENABLED=true
REALTIME_WEATHER_TIMEOUT_SECONDS=5
REALTIME_WEATHER_CACHE_TTL_SECONDS=900
```

Open-Meteo không cần API key cho endpoint công khai, nhưng khi deploy cần kiểm
tra điều khoản sử dụng và giới hạn phù hợp với mục đích của hệ thống. Cảnh báo
thời tiết nguy hiểm trong runtime luôn được ưu tiên trước retrieval; người dùng
vẫn phải làm theo cảnh báo chính thức tại địa phương.

Giá vé realtime không nằm trong phạm vi sản phẩm hiện tại. AI không đưa giá vé
vào gợi ý địa điểm và không tự khẳng định giá, giờ mở cửa hoặc tình trạng dịch
vụ. `POST /internal/v1/ai/suggest-places` lấy địa điểm từ catalog TravelMate,
sau đó chỉ dùng OpenStreetMap Nominatim để xác minh tọa độ và địa chỉ cho màn
hình Map; kết quả được cache 24 giờ.

Cấu hình geocoding:

```dotenv
PLACE_GEOCODING_TIMEOUT_SECONDS=5
PLACE_GEOCODING_CACHE_TTL_SECONDS=86400
```

Ví dụ request:

```json
{
  "destination": "Đà Nẵng",
  "durationDays": 3,
  "numPeople": 2,
  "budgetVnd": 5000000,
  "preferences": ["biển", "ẩm thực"]
}
```

## Demo bằng Gemini

Tạo API key trong Google AI Studio, sau đó sao chép file cấu hình:

```powershell
Copy-Item .env.example .env
```

Chỉnh hai dòng sau trong `.env`:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key
```

Không đưa file `.env` hoặc API key vào Git. Khởi động lại FastAPI sau khi đổi
cấu hình. Model mặc định là `gemini-3.6-flash`; có thể đổi bằng
`GEMINI_MODEL`.

## Chạy adapter khác để nghiên cứu

Không cần cài dependency nặng nếu chỉ dùng chế độ `mock`. Để thử một adapter
khác ngoài bản production:

```powershell
python -m pip install -e ".[local-llm]"
Copy-Item .env.example .env
```

Trong `.env`, đặt `LLM_PROVIDER=local` và đổi `LOCAL_ADAPTER_PATH`. Chỉ các file
inference của adapter production v12-r3 được đưa vào repository; checkpoint và
candidate nghiên cứu không được commit. Hướng dẫn huấn luyện nằm tại
[`training/README.md`](training/README.md).

Candidate v11 toàn quốc đã được train local tại
`artifacts/travelmate-qwen3-4b-lora-v11-nationwide`. Bản này đạt `34/34` ca
lịch trình JSON grounded trên 34 tỉnh/thành nhưng mới đạt `22/34` ca
alias/free-text, vì vậy **chưa phải adapter mặc định**. Có thể thử bằng cách đổi
`LOCAL_ADAPTER_PATH` sang đường dẫn trên; luôn giữ itinerary validator và không
dùng phản hồi tự do của candidate để khẳng định địa điểm hoặc dữ liệu realtime.
Chi tiết kết quả nằm trong
[`training/experiments/2026-08-10-local-qwen3-4b-v11.md`](training/experiments/2026-08-10-local-qwen3-4b-v11.md).

V12-r3 tiếp tục từ r2 bằng một epoch sửa lỗi với learning rate thấp. Bản
production đạt tên tỉnh, đủ địa điểm catalog và ranh giới realtime `102/102`;
structured itinerary `34/34`; demo runtime `20/20`. Sáu ca không khớp template
nghiêm ngặt chỉ khác cách diễn đạt, không sai nội dung. Xem báo cáo tại
[`training/experiments/2026-08-11-local-qwen3-4b-v12.md`](training/experiments/2026-08-11-local-qwen3-4b-v12.md).

Nếu WSL rơi về `networkingMode VirtioProxy` và không forward được cổng sang
Windows, chạy AI Service trong WSL ở cổng `8002`, rồi mở proxy trên Windows:

```powershell
python scripts/wsl_demo_proxy.py --port 8001 --target-port 8002
```

Expo Web tiếp tục gọi `http://localhost:8001/internal/v1`. Qwen được giữ trong
GPU của WSL; proxy chỉ chuyển tiếp request và không tải lại model mỗi lượt.
