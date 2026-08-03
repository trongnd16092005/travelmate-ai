# TravelMate AI – Tài liệu Phân tích & Thiết kế Hệ thống
## Phần 3: Activity Diagram · Sequence Diagram · Kiến trúc Hệ thống

> **Phiên bản:** 1.0 | **Ngày:** 2026-07-26

---

# PHẦN 7 – ACTIVITY DIAGRAM

> Các Activity Diagram mô tả luồng hoạt động (workflow) của từng chức năng chính trong hệ thống.

## 7.1 Activity Diagram – Đăng ký & Xác minh tài khoản

```mermaid
flowchart TD
    A([Bắt đầu]) --> B[Mở màn hình Đăng ký]
    B --> C[Nhập: Họ tên, Email, Password, Xác nhận Password]
    C --> D{Validate\nđầu vào?}
    D -- Lỗi --> E[Hiển thị lỗi inline]
    E --> C
    D -- Hợp lệ --> F[Gửi request đăng ký lên Backend]
    F --> G{Email đã\ntồn tại?}
    G -- Có --> H[Hiển thị: Email đã được sử dụng]
    H --> C
    G -- Không --> I[Tạo User với status = PENDING]
    I --> J[Sinh email verification token]
    J --> K[Gửi email xác minh]
    K --> L[Hiển thị: Kiểm tra hộp thư của bạn]
    L --> M{User mở\nemail?}
    M -- Không mở\ntrong 24h --> N[Token hết hạn]
    N --> O{Yêu cầu\ngửi lại?}
    O -- Có --> J
    O -- Không --> P([Kết thúc – Chưa kích hoạt])
    M -- Có --> Q{Link còn\nhiệu lực?}
    Q -- Hết hạn --> N
    Q -- Còn hiệu lực --> R[Kích hoạt tài khoản\nstatus = ACTIVE]
    R --> S[Redirect sang màn hình Đăng nhập]
    S --> T([Kết thúc – Đăng ký thành công])
```

---

## 7.2 Activity Diagram – AI Sinh Lịch Trình Tự Động

```mermaid
flowchart TD
    A([Bắt đầu]) --> B[User mở Trip Detail]
    B --> C{Trip có đủ\nthông tin cơ bản?}
    C -- Thiếu --> D[Yêu cầu bổ sung:\nĐiểm đến / Ngày đi]
    D --> B
    C -- Đủ --> E[User bấm Nhờ AI lên kế hoạch]
    E --> F[Hiển thị dialog xác nhận\nthông tin đầu vào]
    F --> G{User xác\nnhận?}
    G -- Hủy --> H([Quay về Trip Detail])
    G -- Xác nhận --> I[Hiển thị loading animation]
    I --> J[Backend nhận request\nKiểm tra rate limit]
    J --> K{Rate limit\nOK?}
    K -- Vượt giới hạn --> L[Trả về 429\nThông báo chờ X giây]
    L --> H
    K -- Trong giới hạn --> M[Backend gọi AI Service\n FastAPI]
    M --> N[AI Service build prompt\nvới context chuyến đi]
    N --> O[Gọi LLM API\nGemini / OpenAI]
    O --> P{LLM phản\nhồi thành công?}
    P -- Timeout / Lỗi --> Q{Số lần\nretry < 2?}
    Q -- Còn retry --> O
    Q -- Hết retry --> R[Dùng fallback template\nThông báo user]
    P -- Thành công --> S[Parse JSON response\nValidate schema]
    S --> T{JSON hợp\nlệ?}
    T -- Không hợp lệ --> R
    T -- Hợp lệ --> U[Lưu lịch trình\nvào database]
    U --> V[Trả response về Client]
    V --> W[Hiển thị lịch trình\nvới reveal animation]
    W --> X{User hài\nlòng?}
    X -- Muốn sinh lại --> E
    X -- Muốn chỉnh sửa --> Y[Chỉnh sửa thủ công]
    X -- Áp dụng --> Z[Lưu và hoàn tất]
    Z --> AA([Kết thúc – Lịch trình đã lưu])
```

---

## 7.3 Activity Diagram – Quản lý Chi phí Nhóm & Chia tiền

```mermaid
flowchart TD
    A([Bắt đầu]) --> B[Mở tab Chi phí trong Trip]
    B --> C{Vai trò\ncủa User?}
    C -- Viewer --> D[Chỉ xem thống kê\nvà danh sách chi phí]
    C -- Owner/Editor --> E[Có thể thêm / sửa / xóa]
    E --> F[Bấm + Thêm chi phí]
    F --> G[Nhập: Tên, Số tiền, Danh mục,\nNgày, Người chi, Chia cho ai]
    G --> H[Chọn kiểu chia tiền]
    H --> H1{Kiểu chia?}
    H1 -- Đều nhau --> I1[Chia đều cho tất cả\nhoặc các thành viên được chọn]
    H1 -- Tùy chỉnh --> I2[Nhập số tiền\ncụ thể cho từng người]
    H1 -- Một người --> I3[Chỉ một người\nchịu toàn bộ]
    I1 & I2 & I3 --> J[Xác nhận tổng tiền\nvà phân chia]
    J --> K{Tổng chia =\nSố tiền gốc?}
    K -- Không khớp --> L[Hiển thị lỗi\nYêu cầu điều chỉnh]
    L --> H
    K -- Khớp --> M[Lưu expense\nvà expense_splits]
    M --> N[Cập nhật balance\nsheet của nhóm]
    N --> O{Chi phí tổng\n> 80% ngân sách?}
    O -- Có --> P[Hiển thị cảnh báo\ngân sách]
    O -- Không --> Q[Cập nhật dashboard\nchi phí]
    P --> Q
    Q --> R{User muốn\nxem chia tiền?}
    R -- Có --> S[Mở tab Quyết toán]
    S --> T[Hiển thị: A nợ B X đồng\nC nợ A Y đồng...]
    T --> U{Xuất\nbáo cáo?}
    U -- Có --> V[Tạo và tải\nPDF / CSV]
    U -- Không --> W([Kết thúc])
    V --> W
    R -- Không --> W
    D --> W
```

---

## 7.4 Activity Diagram – Mời Thành viên & Phân quyền

```mermaid
flowchart TD
    A([Bắt đầu]) --> B{Actor là\nOwner?}
    B -- Không --> C[Hiển thị lỗi\nKhông có quyền]
    C --> Z([Kết thúc])
    B -- Có --> D[Mở màn hình Thành viên]
    D --> E[Bấm Mời thành viên]
    E --> F{Phương thức\nmời?}

    F -- Qua Email --> G[Nhập email người được mời]
    G --> H[Chọn vai trò: Editor / Viewer]
    H --> I{Email người\nnhận tồn tại?}
    I -- Có --> J[Tạo invitation\ntoken – 7 ngày]
    I -- Không --> K[Tạo pre-registered\ninvitation]
    J & K --> L[Gửi email mời\nvới deep link]
    L --> M[Thành viên xuất hiện\ntrạng thái Pending]

    F -- Qua Link --> N[Tạo invite link\nvới token]
    N --> O[Owner copy và\nchia sẻ link]
    O --> P{Người nhận\nbấm link?}
    P -- Chưa đăng ký --> Q[Redirect sang Đăng ký\nRồi tự động join]
    P -- Đã đăng ký --> R[Xác nhận tham gia]
    Q & R --> S[Thêm vào TripMember\nvới vai trò mặc định: Viewer]

    M --> T{Người nhận\nchấp nhận?}
    T -- Chấp nhận --> U[Tham gia trip\nvới vai trò đã gán]
    T -- Từ chối --> V[Xóa invitation\nThông báo Owner]
    T -- Hết hạn 7 ngày --> V

    S & U --> W[Gửi push notification\ncho Owner]
    W --> X{Owner muốn\nđổi quyền?}
    X -- Có --> Y[Chọn thành viên\n→ Đổi vai trò]
    Y --> AA[Cập nhật TripMember\nbảng phân quyền]
    AA --> Z
    X -- Không --> Z
    V --> Z
```

---

## 7.5 Activity Diagram – AI Chatbot Tư vấn Du lịch

```mermaid
flowchart TD
    A([Bắt đầu]) --> B[User mở màn hình AI Chat]
    B --> C[Load lịch sử chat\ncủa conversation này]
    C --> D[Hiển thị welcome message\nnếu chat mới]
    D --> E[User nhập câu hỏi]
    E --> F{Độ dài tin nhắn\n≤ 1000 ký tự?}
    F -- Quá dài --> G[Hiển thị cảnh báo\nĐề xuất rút gọn]
    G --> E
    F -- Hợp lệ --> H[Gửi request đến Backend]
    H --> I[Backend xây dựng payload:\n system_prompt + trip_context\n + chat_history + user_message]
    I --> J[Chuyển tiếp đến\nAI Service FastAPI]
    J --> K[AI Service gọi\nLLM API streaming]
    K --> L{LLM phản\nhồi?}
    L -- Lỗi --> M[Trả về lỗi\nHiển thị icon retry]
    L -- Thành công --> N{Streaming\nhỗ trợ?}
    N -- Có --> O[Stream từng token\nvề Client]
    N -- Không --> P[Chờ toàn bộ response]
    O --> Q[Hiển thị typing animation\nvà từng từ xuất hiện]
    P --> R[Hiển thị đầy đủ response]
    Q & R --> S{Nội dung có\nphù hợp du lịch?}
    S -- Ngoài phạm vi\ndo system prompt lọc --> T[Hiển thị: Mình chỉ tư\nvấn du lịch thôi nhé!]
    S -- Phù hợp --> U[Lưu cặp message\nvào chat_messages table]
    T --> U
    U --> V{User muốn\ntiếp tục?}
    V -- Có --> E
    V -- Không --> W([Kết thúc chat])
    M --> V
```

---

# PHẦN 8 – SEQUENCE DIAGRAM

> Sequence Diagram mô tả tương tác theo thời gian giữa các thành phần hệ thống.

## 8.1 Sequence Diagram – Đăng nhập với JWT

```mermaid
sequenceDiagram
    actor U as User
    participant App as React Native App
    participant BE as Spring Boot Backend
    participant DB as MySQL Database
    participant Cache as Redis Cache

    U->>App: Nhập email + password → Bấm Đăng nhập
    App->>BE: POST /api/v1/auth/login {email, password}
    BE->>DB: SELECT user WHERE email = ?
    DB-->>BE: User record (hashed_password, status, role)

    alt Tài khoản không tồn tại
        BE-->>App: 401 {error: "Invalid credentials"}
        App-->>U: Hiển thị "Email hoặc mật khẩu không đúng"
    else Tài khoản bị khoá
        BE-->>App: 403 {error: "Account locked", unlock_at: timestamp}
        App-->>U: Hiển thị "Tài khoản bị khoá đến HH:MM"
    else Đăng nhập thành công
        BE->>BE: BCrypt.verify(password, hashed_password)
        BE->>BE: Generate JWT AccessToken (15 phút)
        BE->>BE: Generate RefreshToken (7 ngày, UUID)
        BE->>DB: INSERT INTO refresh_tokens (user_id, token, expires_at)
        BE->>Cache: SET session:{userId} = {meta} EX 900
        BE-->>App: 200 {access_token, refresh_token, user_info}
        App->>App: Lưu tokens vào SecureStorage
        App-->>U: Redirect sang Home Screen
    end
```

---

## 8.2 Sequence Diagram – Refresh Token khi Access Token hết hạn

```mermaid
sequenceDiagram
    actor U as User
    participant App as React Native App
    participant BE as Spring Boot Backend
    participant DB as MySQL Database

    U->>App: Thực hiện bất kỳ action nào
    App->>BE: GET /api/v1/trips (Authorization: Bearer <expired_token>)
    BE->>BE: Verify JWT → TokenExpiredException

    BE-->>App: 401 {error: "Token expired"}

    Note over App: Interceptor tự động bắt 401
    App->>BE: POST /api/v1/auth/refresh {refresh_token}
    BE->>DB: SELECT * FROM refresh_tokens WHERE token = ? AND is_revoked = 0
    
    alt Refresh token hợp lệ
        DB-->>BE: Refresh token record (user_id, expires_at)
        BE->>BE: Kiểm tra expires_at > NOW()
        BE->>BE: Generate JWT AccessToken mới (15 phút)
        BE->>DB: UPDATE refresh_tokens SET last_used = NOW()
        BE-->>App: 200 {new_access_token}
        App->>App: Cập nhật token trong SecureStorage
        App->>BE: GET /api/v1/trips (với token mới) – Retry request gốc
        BE-->>App: 200 {trips data}
        App-->>U: Hiển thị dữ liệu bình thường
    else Refresh token hết hạn / bị thu hồi
        DB-->>BE: Không tìm thấy hoặc is_revoked = 1
        BE-->>App: 401 {error: "Session expired, please login again"}
        App->>App: Xóa toàn bộ tokens
        App-->>U: Redirect về màn hình Đăng nhập
    end
```

---

## 8.3 Sequence Diagram – AI Sinh Lịch Trình (End-to-End)

```mermaid
sequenceDiagram
    actor U as User
    participant App as React Native App
    participant BE as Spring Boot Backend
    participant AI as Python FastAPI AI Service
    participant LLM as Gemini / OpenAI API
    participant DB as MySQL Database

    U->>App: Bấm "Nhờ AI lên kế hoạch"
    App->>App: Hiển thị dialog xác nhận thông tin
    U->>App: Xác nhận + bấm "Tạo lịch trình"
    App->>App: Hiển thị loading skeleton

    App->>BE: POST /api/v1/ai/generate-itinerary\n{trip_id, preferences, budget, style}
    
    BE->>BE: Xác thực JWT token
    BE->>BE: Kiểm tra quyền (Owner/Editor của trip)
    BE->>BE: Kiểm tra rate limit (10 req/phút/user)

    alt Rate limit vượt quá
        BE-->>App: 429 {error: "Rate limit exceeded", retry_after: 60}
        App-->>U: "Vui lòng chờ 60 giây trước khi thử lại"
    else Trong giới hạn
        BE->>DB: SELECT trip details, user preferences
        DB-->>BE: Trip info + user profile
        
        BE->>AI: POST /generate-itinerary\n{destination, days, budget, style, interests}
        
        AI->>AI: Build system prompt + user prompt
        AI->>AI: Validate input parameters
        
        AI->>LLM: API call với formatted prompt
        Note over LLM: Xử lý 3–8 giây
        
        alt LLM thành công
            LLM-->>AI: JSON response (lịch trình chi tiết)
            AI->>AI: Parse và validate JSON schema
            AI->>AI: Enrich data (estimate costs, durations)
            AI-->>BE: 200 {itinerary: [...days]}
            
            BE->>DB: BEGIN TRANSACTION
            BE->>DB: DELETE old itinerary (nếu sinh lại)
            BE->>DB: INSERT itinerary_days, activities
            BE->>DB: COMMIT
            
            BE-->>App: 200 {itinerary, generated_at}
            App->>App: Ẩn loading, reveal lịch trình với animation
            App-->>U: Hiển thị lịch trình đầy đủ từng ngày
            
        else LLM timeout / lỗi (retry ≤ 2)
            LLM-->>AI: Error / Timeout
            AI->>AI: Retry với exponential backoff
            AI->>LLM: Retry request
            
        else Hết retry
            AI-->>BE: 503 {error: "AI service unavailable"}
            BE-->>App: 503 {error: "AI tạm thời không khả dụng"}
            App-->>U: "AI đang bận, thử lại sau nhé!"
        end
    end
```

---

## 8.4 Sequence Diagram – Mời thành viên qua Email

```mermaid
sequenceDiagram
    actor O as Trip Owner
    actor M as Người được mời
    participant App as React Native App
    participant BE as Spring Boot Backend
    participant DB as MySQL Database
    participant Mail as Email Service

    O->>App: Mở Thành viên → Mời qua email
    App->>App: Hiển thị form: email + vai trò
    O->>App: Nhập email + chọn Editor → Bấm Gửi

    App->>BE: POST /api/v1/trips/{tripId}/members/invite\n{email, role: "EDITOR"}
    
    BE->>BE: Xác thực JWT, kiểm tra quyền Owner
    BE->>DB: SELECT user WHERE email = ?
    
    alt User đã có tài khoản
        DB-->>BE: User record
        BE->>DB: INSERT invitations\n(trip_id, invitee_id, role, token, expires_at=+7days)
    else User chưa có tài khoản
        DB-->>BE: null
        BE->>DB: INSERT invitations\n(trip_id, invitee_email, role, token, expires_at=+7days)
    end
    
    BE->>Mail: sendInvitationEmail(email, tripName, inviterName, token)
    Mail-->>M: Email: "Bạn được mời tham gia [Trip Name]"
    
    BE-->>App: 200 {message: "Lời mời đã gửi", pending_member}
    App-->>O: Hiển thị thành viên mới với badge "Pending"

    Note over M: M nhận email, bấm "Chấp nhận"
    
    M->>BE: GET /api/v1/invitations/accept?token=xxx
    BE->>DB: SELECT invitation WHERE token = ? AND expires_at > NOW()
    
    alt Token hợp lệ
        DB-->>BE: Invitation record
        BE->>DB: INSERT trip_members (trip_id, user_id, role = "EDITOR")
        BE->>DB: UPDATE invitations SET status = "ACCEPTED"
        BE->>BE: Generate notification cho Owner
        BE-->>M: 200 → Redirect vào Trip
        
        Note over O: Owner nhận push notification
        BE->>App: Push: "[Tên] đã tham gia chuyến đi của bạn!"
        App-->>O: Hiển thị notification
        
    else Token hết hạn hoặc không hợp lệ
        BE-->>M: 400 → Trang "Lời mời đã hết hạn"
        M->>O: Yêu cầu mời lại
    end
```

---

# PHẦN 9 – KIẾN TRÚC HỆ THỐNG

## 9.1 Tổng quan kiến trúc (Architecture Overview)

TravelMate AI sử dụng kiến trúc **Client–Server** với 3 tầng chính, kết hợp dịch vụ AI riêng biệt:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT TIER                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              React Native App (Expo)                         │   │
│  │   iOS Device          Android Device          Tablet         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTPS / REST API / JWT
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                        SERVER TIER                                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               Spring Boot Backend (Java 21)                 │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │    │
│  │  │Auth/JWT  │  │Trip Mgmt │  │Itinerary │  │Expense   │   │    │
│  │  │Controller│  │Service   │  │Service   │  │Service   │   │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │    │
│  │  │Place     │  │Share/    │  │Admin     │  │AI Proxy  │   │    │
│  │  │Service   │  │Perm Svc  │  │Service   │  │Service   │   │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                           │                │                         │
│              ┌────────────┘                └────────────┐            │
│              ▼                                          ▼            │
│  ┌─────────────────────┐              ┌──────────────────────┐       │
│  │    MySQL 8.x DB      │              │   Redis Cache         │      │
│  │  (Primary Database)  │              │  (Session, Rate Limit)│      │
│  └─────────────────────┘              └──────────────────────┘       │
└────────────────────────────┬────────────────────────────────────────┘
                             │ Internal HTTP (Docker network)
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                         AI SERVICE TIER                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              Python FastAPI AI Service                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │    │
│  │  │ /generate-   │  │ /chat        │  │ /suggest-places  │  │    │
│  │  │  itinerary   │  │              │  │ /optimize        │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │    │
│  │              │                                               │    │
│  │     ┌────────▼──────────────────────────────┐              │    │
│  │     │      Prompt Builder & Context Manager  │              │    │
│  │     └────────────────────────────────────────┘              │    │
│  └─────────────────────┬───────────────────────────────────────┘    │
└───────────────────────┬┘                                            │
                        │                                              │
           ┌────────────▼──────────────┐                              │
           │   External AI APIs         │                              │
           │  ┌─────────┐ ┌──────────┐ │                              │
           │  │ Gemini  │ │ OpenAI   │ │                              │
           │  │  API    │ │  GPT-4o  │ │                              │
           │  └─────────┘ └──────────┘ │                              │
           └────────────────────────────┘
```

## 9.2 Component Diagram

```mermaid
flowchart LR
    subgraph Client["📱 Client – React Native Expo"]
        direction TB
        Nav[Navigation\nExpo Router]
        AuthCtx[Auth Context\nZustand Store]
        TripCtx[Trip Context\nZustand Store]
        APIClient[Axios API Client\nInterceptors]
        UI[UI Components\nNativeWind / RN]
        Nav --> UI
        AuthCtx --> APIClient
        TripCtx --> APIClient
    end

    subgraph Backend["⚙️ Backend – Spring Boot"]
        direction TB
        SecurityFilter[Security Filter Chain\nJWT Filter]
        Controllers[REST Controllers\n/api/v1/*]
        Services[Business Services\nTrip, Itinerary, Auth...]
        Repos[JPA Repositories\nMySQL via Hibernate]
        AIProxy[AI Proxy Service\nHTTP Client to FastAPI]
        SecurityFilter --> Controllers
        Controllers --> Services
        Services --> Repos
        Services --> AIProxy
    end

    subgraph AIService["🤖 AI Service – FastAPI"]
        direction TB
        Router[FastAPI Router]
        PromptBuilder[Prompt Builder]
        LLMClient[LLM Client\nGoogle Generative AI / OpenAI]
        ResponseParser[Response Parser\nJSON Schema Validator]
        Router --> PromptBuilder
        PromptBuilder --> LLMClient
        LLMClient --> ResponseParser
    end

    subgraph DataLayer["🗄️ Data Layer"]
        MySQL[(MySQL 8.x\nPrimary DB)]
        Redis[(Redis\nCache & Rate Limit)]
        S3[(AWS S3 / Cloudinary\nImage Storage)]
    end

    Client <-->|HTTPS REST| Backend
    Backend <-->|Internal HTTP| AIService
    Backend <-->|JDBC / JPA| MySQL
    Backend <-->|Redis Client| Redis
    Backend <-->|HTTP SDK| S3
    AIService <-->|HTTPS| ExternalAI[Gemini / OpenAI API]
```

---

## 9.3 Deployment Diagram

```mermaid
flowchart TD
    subgraph UserDevice["👤 User Device"]
        iOS[iOS App\nExpo Go / IPA]
        Android[Android App\nExpo Go / APK]
    end

    subgraph Cloud["☁️ Cloud Infrastructure – Docker / VPS"]
        subgraph DockerCompose["Docker Compose / Kubernetes"]
            NGX[Nginx\nReverse Proxy\nSSL Termination\nPort 443]
            BE_Container[Spring Boot Container\nPort 8080]
            AI_Container[FastAPI Container\nPort 8000]
            Redis_Container[Redis Container\nPort 6379]
        end
        MySQL_Instance[(MySQL 8.x\nManaged DB / RDS\nPort 3306)]
        Storage[AWS S3 / Cloudinary\nImage & File Storage]
    end

    subgraph ExternalServices["🌐 External Services"]
        GeminiAPI[Google Gemini API]
        OpenAI[OpenAI GPT-4o API]
        EmailSvc[SendGrid / SMTP\nEmail Service]
        GoogleOAuth[Google OAuth 2.0]
        APNS[Apple Push\nNotification Service]
        FCM[Firebase Cloud\nMessaging]
    end

    iOS & Android -->|HTTPS| NGX
    NGX -->|Reverse proxy /api| BE_Container
    BE_Container -->|Internal| AI_Container
    BE_Container -->|TCP| Redis_Container
    BE_Container -->|TCP| MySQL_Instance
    BE_Container -->|SDK| Storage
    BE_Container -->|SMTP| EmailSvc
    BE_Container -->|OAuth| GoogleOAuth
    BE_Container -->|APNS/FCM| APNS & FCM
    AI_Container -->|HTTPS| GeminiAPI
    AI_Container -->|HTTPS| OpenAI
```

---

## 9.4 Layer Architecture

### 9.4.1 Spring Boot Backend – Clean Architecture

```
┌──────────────────────────────────────────────────┐
│                PRESENTATION LAYER                 │
│  REST Controllers → Request/Response DTOs         │
│  Exception Handlers → API Response Wrapper        │
├──────────────────────────────────────────────────┤
│                 SERVICE LAYER                     │
│  Business Logic → Validation → Orchestration      │
│  Transaction Management → Event Publishing        │
├──────────────────────────────────────────────────┤
│               REPOSITORY LAYER                    │
│  Spring Data JPA → Custom JPQL Queries            │
│  Repository Interfaces → Entity Mapping            │
├──────────────────────────────────────────────────┤
│                  DATA LAYER                       │
│  MySQL (JPA/Hibernate) │ Redis │ External APIs    │
└──────────────────────────────────────────────────┘

Cross-cutting Concerns:
  • Security: Spring Security + JWT Filter
  • Logging: SLF4J + Logback (JSON format)
  • Validation: Bean Validation (JSR-380)
  • Exception: GlobalExceptionHandler (@RestControllerAdvice)
  • Mapping: MapStruct (Entity ↔ DTO)
```

### 9.4.2 FastAPI AI Service – Layered Design

```
┌──────────────────────────────────────────────────┐
│                   ROUTER LAYER                    │
│  FastAPI Routers → Pydantic Request/Response      │
├──────────────────────────────────────────────────┤
│                  SERVICE LAYER                    │
│  ItineraryService │ ChatService │ PlaceService    │
├──────────────────────────────────────────────────┤
│               PROMPT ENGINE LAYER                 │
│  PromptBuilder → ContextManager → TemplateLoader  │
├──────────────────────────────────────────────────┤
│                  CLIENT LAYER                     │
│  GeminiClient │ OpenAIClient → Response Parser    │
├──────────────────────────────────────────────────┤
│                  SCHEMA LAYER                     │
│  JSON Schema Validator → Pydantic Models          │
└──────────────────────────────────────────────────┘
```

### 9.4.3 React Native App – Feature-based Structure

```
src/
├── app/                   # Expo Router screens
│   ├── (auth)/           # Login, Register, ForgotPassword
│   ├── (tabs)/           # Home, Trips, AI, Profile
│   └── trip/[id]/        # Trip Detail, Itinerary, Expense
├── components/           # Reusable UI components
│   ├── common/           # Button, Input, Card, Modal
│   ├── trip/             # TripCard, MemberList, ExpenseItem
│   └── ai/               # ChatBubble, ItineraryCard
├── services/             # API calls (axios instances)
│   ├── authService.ts
│   ├── tripService.ts
│   └── aiService.ts
├── stores/               # Zustand global state
│   ├── authStore.ts
│   └── tripStore.ts
├── hooks/                # Custom hooks
└── utils/                # Helpers, formatters, constants
```

---

## 9.5 Luồng xử lý Request tổng quát

```mermaid
sequenceDiagram
    participant C as Client (RN App)
    participant N as Nginx
    participant B as Spring Boot
    participant R as Redis
    participant D as MySQL
    participant A as AI FastAPI

    C->>N: HTTPS Request + Bearer Token
    N->>B: Forward (SSL terminated)
    B->>B: JWT Filter: verify token signature + expiry
    B->>R: Check rate limit (INCR key, TTL)
    
    alt Rate limit OK
        R-->>B: count < limit
        B->>B: Authorization check (role/permission)
        
        alt Cần AI
            B->>A: POST /ai-endpoint {context, params}
            A->>A: Build prompt + call LLM
            A-->>B: JSON response
        end
        
        B->>D: Query / Write data
        D-->>B: Result
        B->>B: Map Entity → DTO
        B-->>N: 2xx + JSON response
        N-->>C: Response
        
    else Rate limit exceeded
        R-->>B: count >= limit
        B-->>C: 429 Too Many Requests
    end
```

---

## 9.6 Chiến lược Bảo mật

| Lớp | Biện pháp | Công nghệ |
|-----|-----------|-----------|
| **Transport** | HTTPS/TLS 1.3 toàn bộ traffic | Nginx + Let's Encrypt |
| **Authentication** | JWT RS256, Access + Refresh token | Spring Security |
| **Authorization** | Role-based (ADMIN/USER) + Trip-level permission | Custom annotations |
| **Password** | BCrypt cost=12 | Spring Security |
| **Input** | Validation + Sanitization tất cả input | Bean Validation + OWASP ESAPI |
| **Rate Limiting** | 100 req/phút/IP, 10 AI req/phút/user | Redis + custom filter |
| **SQL Injection** | Parameterized queries qua JPA | Hibernate |
| **CORS** | Whitelist chính xác origins | Spring Security CORS config |
| **Secrets** | Biến môi trường, không hardcode | Docker secrets / .env |
| **Logging** | Audit log cho mọi thao tác nhạy cảm | SLF4J + AOP |

---

## 9.7 Chiến lược AI Integration

| Pattern | Mô tả | Áp dụng |
|---------|-------|---------|
| **Proxy Pattern** | Backend làm trung gian giữa Client và AI Service | Bảo vệ AI API key, kiểm soát rate limit |
| **Retry + Backoff** | Tự động retry 2 lần với delay 1s, 3s | Tăng resilience khi LLM timeout |
| **Fallback** | Template lịch trình mẫu khi AI down | Đảm bảo UX không bị gián đoạn hoàn toàn |
| **Async Processing** | Queue request AI nếu > 5s (future) | Tăng throughput, không block UI |
| **Context Injection** | Inject thông tin trip vào mỗi AI request | AI biết ngữ cảnh cụ thể của từng user |
| **Output Validation** | Validate JSON schema trước khi lưu DB | Tránh corrupt data từ LLM hallucination |

---

> **📌 Kết thúc Phần 3** – Bao gồm: Activity Diagram (5 luồng), Sequence Diagram (4 luồng), Kiến trúc hệ thống đầy đủ (Architecture Overview, Component, Deployment, Layer, Security, AI Integration).
>
> Gõ **"Tiếp tục"** để nhận **Phần 4**: Thiết kế CSDL (ERD, Data Dictionary) · Thiết kế API RESTful.
