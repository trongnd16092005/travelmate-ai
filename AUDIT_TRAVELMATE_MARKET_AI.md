# BÁO CÁO AUDIT HỢP NHẤT — TRAVELMATE AI

**Ngày đánh giá:** 01/08/2026  
**Phạm vi:** yêu cầu Khoa, source code, build/lint/test, runtime API, Expo Web và nghiên cứu đối thủ từ nguồn chính thức  
**Mục tiêu:** đánh giá mức độ phù hợp đồ án Software Engineering năm 4, độ sâu chức năng/AI và hướng phát triển

## Cập nhật sau sửa lỗi và tái kiểm thử — 01/08/2026

Phần kết luận bên dưới ghi lại trạng thái tại thời điểm audit ban đầu. Sau vòng sửa lỗi và tái kiểm thử, kết quả hiện tại là:

| Hạng mục | Trạng thái mới | Bằng chứng |
|---|---|---|
| Wizard bước 2 | **Đã sửa** | Ngày `10/08/2026→12/08/2026` và ngân sách `5.000.000đ` bật nút tiếp tục; đi được tới bước 3 |
| Sửa ngân sách làm mất ngày | **Đã sửa** | Đổi ngân sách thành `6.000.000đ`, cả hai ngày vẫn được giữ nguyên |
| Ngày kết thúc không hợp lệ | **Đã sửa** | Hiện lý do rõ ràng và vô hiệu hoá nút tiếp tục |
| Lưu chuyến sau reload | **Đã kiểm tra đạt** | Chuyến đã tạo vẫn tồn tại sau khi tải lại trang |
| AI với câu hỏi mơ hồ | **Đã cải thiện** | Yêu cầu người dùng nêu tỉnh/thành phố thay vì trả lỗi JSON chung chung |
| Prompt xin system prompt/API key | **Đã cải thiện** | Từ chối an toàn, có hướng dẫn quay lại tác vụ du lịch |
| AI grounded bình thường | **Không hồi quy** | Câu hỏi về Huế vẫn trả kết quả có nguồn qua AI Search Layer |
| Chạy Expo và API bằng một lệnh | **Còn mở** | Hiện vẫn cần bảo đảm API cổng 3000 được bật trước khi demo |

Quality gate sau sửa lỗi: `4/4` regression test đạt, `tsc --noEmit` đạt, Expo lint đạt, Expo web export đạt và root production build đạt. Với core flow đã thông nhưng chưa thống nhất runtime/dữ liệu đa nền tảng, mức hợp lý hiện tại là khoảng **6,5–7,0/10**; các mục P1 về backend sync, security và chiều sâu AI vẫn giữ nguyên.

### Tái kiểm thử AI sau vòng sửa grounding — 01/08/2026

- **BUG-02 đã sửa:** câu “Lên lịch trình Việt Nam 3 ngày” không còn kế thừa âm thầm điểm đến của trip đang chọn; hệ thống trả về `TravelMate · Clarification Layer` và yêu cầu tỉnh/thành phố cụ thể.
- **BUG-03 đã sửa ở tầng ngữ cảnh:** follow-up về Huế ưu tiên địa điểm trong lịch sử hội thoại thay vì trip active Đà Nẵng; nguồn Đà Nẵng không còn được trả về.
- **BUG-01 đã giảm rủi ro:** API chỉ trả nguồn có tiêu đề khớp với tên địa điểm trong recommendation; nguồn không khớp bị ẩn và được ghi chú rõ, không còn gắn citation chung chung.
- **Grounding prompt đã siết:** recommendation PLACE/ITINERARY phải dùng tên có trong dữ liệu Wikimedia/Google Maps đã truy xuất.
- **BUG-04 đã cải thiện:** khi câu hỏi có ngân sách cụ thể, response bổ sung phân bổ tham khảo cho lưu trú, ăn uống, di chuyển và vé/phát sinh; tổng các hạng mục khớp ngân sách đầu vào.

Quality gate bổ sung: root `vinext build` **Pass** sau các thay đổi worker; test trực tiếp API cho vague query, câu hỏi Huế và follow-up context đều phản hồi thành công. Responsive 768/390px vẫn chưa được xác minh. Groq là dịch vụ ngoài nên cần có retry/fallback khi provider tạm thời không phản hồi.

### Xử lý BUG-08 reliability follow-up — 01/08/2026

Đã bổ sung:

- Groq timeout 15 giây mỗi attempt, retry theo backoff `300ms → 900ms → 1800ms` và bắt cả lỗi mạng/timeout.
- History Expo AI giảm còn 4 message gần nhất, mỗi message tối đa 700 ký tự.
- Search context được compact trước khi gửi provider, tránh phình prompt khi conversation dài.
- Nếu Groq lỗi hoặc trả JSON không hợp lệ, API trả `TravelMate · Fallback Layer` với bản nháp dựa trên nguồn đã truy xuất thay vì HTTP 502.
- Prompt injection và clarification layer vẫn bypass Groq, nên tiếp tục phản hồi nhanh và an toàn.

Retest sau build: follow-up trong context Huế trả HTTP 200 bằng Fallback Layer khi Groq không phản hồi; câu hỏi mơ hồ vẫn trả Clarification Layer; prompt injection vẫn trả Safety Layer. BUG-08 đã được **giảm từ P0 chặn demo xuống P1 cần theo dõi**, vì trải nghiệm vẫn có thể mất chất lượng AI nâng cao khi provider ngoài bị gián đoạn nhưng không còn lỗi backend làm gãy luồng.

## 1. Kết luận điều hành

TravelMate có tư duy sản phẩm và giao diện tốt hơn mặt bằng đồ án sinh viên thông thường, đồng thời đã có một lớp AI grounded bằng dữ liệu thật. Tuy nhiên, ở trạng thái audit, sản phẩm chưa đủ ổn định để bảo vệ an toàn:

- Wizard Expo không thể qua bước nhập ngày và ngân sách dù dữ liệu hợp lệ.
- Expo chỉ chạy ở cổng 8081 trong khi frontend gọi API cổng 3000; backend không được bật nên AI và Khám phá báo `Failed to fetch`.
- Web và Expo chưa dùng chung tài khoản, chuyến đi và lịch sử chat.
- “Nhịp Chung” mới chủ yếu nằm trong tài liệu, chưa phải chức năng chạy thật.
- Test hiện tại không đủ chứng minh nghiệp vụ, phân quyền, bảo mật và chất lượng AI.
- Tài liệu mô tả nhiều thành phần chưa tồn tại trong code.

### Điểm đánh giá

| Trạng thái | Điểm dự kiến |
|---|---:|
| Mang đúng phiên đã audit đi bảo vệ | **5,5/10** |
| Chạy đúng backend nhưng chưa sửa wizard/test/security | **6,5–7,0/10** |
| Sửa P0/P1, demo ổn định và thu hẹp tuyên bố | **7,5–8,0/10** |
| Hoàn thiện Nhịp Chung, đồng bộ dữ liệu và AI evaluation | **8,0–8,5/10** |

Điểm thấp của trạng thái audit không phản ánh toàn bộ tiềm năng code. Nó phản ánh nguyên tắc hội đồng sẽ chấm: chức năng không chạy trong demo gần như không tạo ra điểm.

## 2. Mức đáp ứng yêu cầu của Khoa

Yêu cầu chính thức chấp nhận sản phẩm thực tế có yếu tố đa nền tảng, kiểm thử, bảo mật hoặc AI. Nhóm phải nộp sản phẩm, hồ sơ dự án, phân tích thiết kế, source code, báo cáo PDF ít nhất 20 trang nội dung và slide tiếng Anh.

| Đầu ra | Trạng thái hiện tại |
|---|---|
| Sản phẩm thực tế | Có, nhưng core flow Expo đang lỗi |
| Source code | Có, quy mô đủ cho đồ án |
| Phân tích thiết kế | Có nhiều tài liệu; V2 là bản chính thức |
| Kiến trúc khớp implementation | Chưa hoàn toàn |
| Kiểm thử có bằng chứng | Rất thiếu |
| Báo cáo PDF ≥ 20 trang | Chưa tìm thấy trong workspace |
| Slide tiếng Anh | Chưa tìm thấy trong workspace |

Hai đầu ra cuối là rủi ro thủ tục, không chỉ là điểm cộng thêm.

## 3. Bằng chứng kỹ thuật

### 3.1 Build và kiểm tra mã nguồn

- Web `vinext build`: **Pass**.
- Test web: **Pass 2/2**, nhưng chỉ kiểm tra HTML shell và starter marker.
- Expo `tsc --noEmit` và `expo lint`: **Pass** trong lần kiểm tra riêng.
- Root lint: **Fail**, ghi nhận 58 error và 4.688 warning. Phần lớn warning bị khuếch đại do lint quét artifact sinh ra, nhưng vẫn có lỗi source React thật.
- Source TypeScript/TSX/MJS khoảng 9.700 dòng, nhưng tập trung quá nhiều trong một số file lớn: `worker/index.ts`, `app/page.tsx`, màn AI và trip detail.

Kết luận: dự án build được nhưng quality gate tổng chưa xanh; số lượng test quá thấp để xem là bằng chứng chất lượng.

### 3.2 P0-01 — Expo không tự khởi động backend

Trong `travelmate-app/services/travel-api.ts`, web Expo tự xây base URL theo hostname và cổng 3000. `.env.local` không đặt URL khác. Tại thời điểm audit chỉ có cổng 8081 lắng nghe, không có cổng 3000.

Hệ quả:

- AI Chat báo `Failed to fetch`.
- Khám phá/Wikimedia báo `Failed to fetch`.
- Người dùng không được giải thích backend chưa chạy.
- Một người chỉ chạy `npm run app:web` rất dễ tưởng toàn bộ AI bị hỏng.

Sau khi chạy `npm run dev:expo-api`, Worker sẵn sàng tại `127.0.0.1:3000` và các kiểm tra trực tiếp thành công:

| Endpoint | Kết quả |
|---|---|
| `GET /api/places?query=Hue&limit=2` | HTTP thành công, trả 2 địa điểm Wikimedia và source URL |
| `POST /api/ai/assistant` | Thành công, Groq · AI Search Layer |
| AI prompt tiếng Việt về Huế | Khoảng 7,6 giây, trả 10 source refs |

**Chẩn đoán:** đây chủ yếu là lỗi vận hành/dev topology, không phải AI backend chết. Tuy nhiên đối với demo, lỗi vận hành vẫn là P0.

### 3.3 P0-02 — Wizard tạo chuyến bị khóa ở bước 2

Lỗi được tái hiện trên phiên Expo sạch tại cổng 8082:

1. Nhập điểm đến `Đà Nẵng` và tên `Đà Nẵng 3 ngày`.
2. Qua bước 2.
3. Nhập ngày bắt đầu `2026-08-10`.
4. Nhập ngày kết thúc `2026-08-12`.
5. Nhập ngân sách `5000000`.
6. DOM hiển thị đủ ba giá trị nhưng nút `Tiếp tục` vẫn `disabled`.
7. Đổi ngân sách thành `6000000` làm ngày bắt đầu trở về rỗng.

Điều kiện trong source ở `create-trip.tsx` nhìn hợp lý:

```ts
!!startDate && !!endDate && !dateError && Number(budget) > 0
```

Do đó cần kiểm tra vòng đời event của date input trên React Native Web, reconciliation khi sibling `TextInput` cập nhật và ảnh hưởng của React Compiler. Không nên chỉ thay điều kiện bằng cách bỏ validation.

### Acceptance criteria sửa lỗi

- Nhập/sửa ngân sách không thay đổi hai ngày.
- Nút enable ngay khi ba giá trị hợp lệ.
- Ngày kết thúc trước ngày bắt đầu hiển thị lỗi và disable nút.
- Back bước 1 rồi forward bước 2 không mất dữ liệu.
- Reload sau khi tạo chuyến vẫn thấy chuyến vừa tạo.
- Có component test và E2E test cho luồng này.

## 4. Đánh giá chức năng hiện tại

| Module | Trạng thái | Độ sâu | Nhận xét |
|---|---|---:|---|
| Onboarding/auth Expo | Prototype local-only | 2/5 | Account nằm trên từng trình duyệt/thiết bị, không phải auth production |
| Trang chủ/profile/empty states | Hoạt động | 3,5/5 | Copy tốt, không bịa dữ liệu hành vi |
| Tạo chuyến Expo | Bị lỗi P0 | 1/5 | Không thể hoàn thành wizard trong audit |
| Danh sách chuyến Expo | Local-only | 2/5 | Dữ liệu bằng AsyncStorage, không đồng bộ D1 |
| Địa điểm/thời tiết | Hoạt động khi API bật | 3/5 | Có Open-Meteo và Wikimedia, có source |
| AI chat | Hoạt động khi API bật | 3/5 | Grounded answer tốt hơn chatbot thuần, nhưng phụ thuộc quy trình chạy 2 server |
| AI lập lịch trình | Một phần | 2,5/5 | Có structured output nhưng validation/optimization còn hạn chế |
| Apply itinerary | Có nhưng thiếu versioning | 2/5 | Thay lịch trình hiện tại, chưa có draft/version conflict/rollback hoàn chỉnh |
| Thành viên và phân quyền | Web có một phần | 2/5 | Expo chưa đồng bộ backend, khó chứng minh collaboration thật |
| Chi phí | Cơ bản | 2/5 | Chưa có expense split chi tiết và settle-up đầy đủ |
| Nhịp Chung | Chỉ có trong thiết kế | 0,5/5 | Preferences/proposals/votes/conflict matrix chưa triển khai |
| Booking/TikTok/Google Maps | Credential-dependent | 1,5/5 | Có integration state nhưng không phải luồng booking hoàn chỉnh |

### Kết luận chức năng

TravelMate hiện có **độ rộng module khá**, nhưng độ sâu phần lớn mới ở mức prototype. Không có một vertical slice hoàn chỉnh xuyên suốt:

> tài khoản thật → tạo chuyến → mời thành viên → thu sở thích → AI tạo phương án → nhóm chọn → áp dụng → đồng bộ web/mobile → theo dõi chi phí.

Đây là lý do sản phẩm trông nhiều chức năng nhưng vẫn dễ bị hội đồng nhận xét là “còn đơn giản”.

## 5. Đánh giá AI

### Mức AI thực tế

TravelMate đang ở **mức 2/4**:

1. Chatbot gọi LLM: đã vượt qua.
2. LLM có dữ liệu grounded và output cấu trúc: **đang ở mức này**.
3. AI workflow có validation, scoring, versioning và human approval: chưa đầy đủ.
4. AI decision system có tối ưu, feedback và xử lý nhiều thành viên: chưa có.

### Điểm tốt

- API key nằm ở Worker, không đặt trực tiếp trong Expo.
- Có dữ liệu Open-Meteo/Wikimedia thật.
- Response có `sources`, `retrievedAt` và trạng thái từng integration.
- AI có thể trả structured trip plan.
- UI minh bạch khi Google Places thiếu key/billing và không tự gắn rating giả.
- Prompt backend có ý thức phân tách dữ liệu nguồn và chống prompt injection ở mức chỉ dẫn.

### Điểm yếu

- Chưa có vector RAG hoặc knowledge base riêng.
- Chưa có thuật toán kiểm tra xung đột thời gian, khoảng cách và opening hours đáng tin cậy.
- Chưa có budget solver hoặc route optimizer.
- Chưa có bộ evaluation chuẩn để đo hallucination, constraint satisfaction và citation coverage.
- Chưa có feedback loop.
- Chưa có phiên bản draft, diff, rollback và optimistic concurrency đúng như tài liệu mô tả.
- Endpoint Expo AI có thể được mở công khai khi bridge bật, CORS `*` và chưa thấy rate limiting thực tế.
- Một câu trả lời có thể có source refs nhưng chưa chắc từng factual claim được map đến citation cụ thể.

### Bộ chỉ số AI cần có

| Chỉ số | Mục tiêu ban đầu |
|---|---:|
| Lịch trình hợp lệ về ngày/giờ | ≥ 95% |
| Không vượt hard constraint | ≥ 95% |
| Bám ngân sách trong sai số cho phép | ≥ 85% |
| Factual claims có citation hỗ trợ | ≥ 90% |
| Không bịa địa điểm/rating/giá | ≥ 98% |
| P95 latency AI | < 15 giây |
| Tỷ lệ parse JSON thành công | ≥ 99% |
| Apply failure không làm mất lịch cũ | 100% |

Nên xây dataset 20–30 tình huống cố định: đi một mình, gia đình, người lớn tuổi, nhóm mâu thuẫn, ngân sách thấp, ngày mưa, điểm đến ít dữ liệu và prompt injection.

## 6. So sánh thị trường

Phần này là desk research từ website/help center chính thức ngày 01/08/2026, không phải hands-on test đầy đủ từng đối thủ.

### Năng lực đã được đối thủ công bố

- [Wanderlog](https://wanderlog.com/pages/help-center): itinerary + map, live collaboration, import booking, expense splitting, recommendation, offline và route optimization.
- [Mindtrip](https://mindtrip.ai/): personalized AI, nguồn dữ liệu đối tác, group chat/collaboration, comments/likes, receipts, maps, booking và itinerary chỉnh sửa được.
- [Layla](https://layla.ai/): AI itinerary theo ngày, live price/availability, booking, multi-city/route optimization và human travel expert.
- [TripIt](https://www.tripit.com/web/free): tự nhập confirmation email, đồng bộ đa thiết bị, mobile itinerary, maps, sharing, calendar sync và travel alerts.
- [Roadtrippers Autopilot](https://support.roadtrippers.com/hc/en-us/articles/24995143275412-Using-Autopilot-to-Plan-a-Trip): AI hỏi budget/vehicle/preferences, gợi ý stop trên route, bản đồ và itinerary có thể chỉnh sửa.

### Ma trận 0–5

| Tiêu chí | TravelMate | Wanderlog | Mindtrip | Layla | TripIt | Roadtrippers |
|---|---:|---:|---:|---:|---:|---:|
| AI planning | 2,5 | 4 | 5 | 5 | 1 | 4 |
| Grounding/dữ liệu thật | 3 | 4 | 5 | 4 | 4 | 5 |
| Map và routing | 1 | 5 | 4 | 4 | 3 | 5 |
| Collaboration thật | 1 | 5 | 5 | 2 | 2 | 4 |
| Group consensus/voting | 0 | 2 | 3 | 1 | 0 | 1 |
| Expense/splitting | 2 | 5 | 3 | 1 | 1 | 1 |
| Import booking/receipt | 1 | 4 | 5 | 5 | 5 | 2 |
| Đồng bộ web/mobile | 1 | 5 | 4 | 4 | 5 | 5 |
| Offline | 0 | 5 | 3 | 2 | 5 | 5 |
| Minh bạch nguồn | 4 | 2 | 3 | 2 | 3 | 3 |
| Phù hợp người Việt | 4 | 2 | 2 | 2 | 1 | 1 |

Điểm số đối thủ phản ánh năng lực được công bố, không phải benchmark hiệu năng tuyệt đối.

### Kết luận cạnh tranh

TravelMate không thể thắng bằng thông điệp “AI tạo lịch trình”, vì Mindtrip, Layla, Wanderlog và Roadtrippers đều làm sâu hơn. Các module itinerary, map, expense, collaboration và booking cũng đã là feature hygiene của thị trường.

Hai hướng có thể tạo khác biệt:

1. **Grounded AI minh bạch cho dữ liệu du lịch Việt Nam**, hiển thị nguồn và không bịa rating/giá.
2. **Nhịp Chung — ra quyết định cho nhóm**, không chỉ cho nhiều người cùng sửa một itinerary.

Hướng thứ hai có tiềm năng mạnh hơn nhưng hiện chưa được triển khai.

## 7. Thiết kế Nhịp Chung nên triển khai

### Luồng sản phẩm

1. Owner tạo chuyến và mời thành viên.
2. Mỗi thành viên nhập ngân sách, nhịp di chuyển, sở thích, điều không muốn và nhu cầu đặc biệt.
3. Hệ thống chia thành hard constraints và soft preferences.
4. AI tạo 2–3 phương án: tiết kiệm, cân bằng, trải nghiệm.
5. Mỗi phương án có điểm và giải thích trade-off.
6. Thành viên vote hoặc like/dislike từng hoạt động.
7. AI tái tối ưu dựa trên vote.
8. Owner xem diff, xác nhận và áp dụng.
9. Hệ thống giữ version cũ để rollback.

### Scoring gợi ý

```text
proposal_score =
  0.30 * hard_constraint_pass
+ 0.20 * budget_fit
+ 0.20 * member_satisfaction
+ 0.15 * route_feasibility
+ 0.10 * source_confidence
+ 0.05 * schedule_balance
```

Mọi điểm phải giải thích được, ví dụ:

> Phương án B bỏ Bà Nà Hills vì vượt ngân sách 18% và không phù hợp thành viên hạn chế di chuyển; đổi sang Bảo tàng Chăm giúp tăng điểm hài lòng nhóm từ 72 lên 84.

### Data tối thiểu

- `member_preferences`
- `constraint_sets`
- `itinerary_proposals`
- `proposal_scores`
- `activity_votes`
- `ai_drafts`
- `itinerary_versions`
- `audit_logs`

## 8. Danh sách vấn đề ưu tiên

| ID | Mức | Vấn đề | Tác động |
|---|---|---|---|
| P0-01 | P0 | Không có lệnh chạy Expo + API cùng nhau | AI/Explore chết khi demo |
| P0-02 | P0 | Wizard bước 2 không enable, sửa budget mất start date | Không tạo được chuyến |
| P1-01 | P1 | Expo auth/trips/chat local-only | Không phải hệ thống đa nền tảng thật |
| P1-02 | P1 | Public AI bridge, CORS `*`, chưa rate limit | Rủi ro lạm dụng và chi phí |
| P1-03 | P1 | Chỉ có 2 test HTML nông | Không có bằng chứng SE |
| P1-04 | P1 | Tài liệu overclaim Nhịp Chung/rate limit/versioning | Dễ bị phản biện mất điểm |
| P1-05 | P1 | Thiếu report PDF và slide tiếng Anh trong workspace | Rủi ro thủ tục |
| P2-01 | P2 | Root lint fail và scope lint artifact sai | Quality gate không đáng tin |
| P2-02 | P2 | Worker và page chính quá lớn | Khó maintain/test |
| P2-03 | P2 | Data model thiếu constraint/provenance/split chi tiết | Dễ sai dữ liệu |

## 9. Roadmap đề xuất

### Trong 24 giờ

1. Tạo một lệnh duy nhất `npm run dev:demo` chạy API 3000 và Expo 8081, kiểm tra health trước khi mở app.
2. Sửa wizard và thêm test tái hiện lỗi ngày/ngân sách.
3. Thêm màn lỗi có hành động “Thử lại” và thông báo “API chưa sẵn sàng”, không hiện `Failed to fetch` thô.
4. Chuẩn bị script smoke test: health → places → weather → AI.
5. Chọn web làm sản phẩm chính; ghi Expo là prototype nếu chưa đồng bộ kịp.

### Trong 2–4 ngày

1. Yêu cầu auth hoặc signed token cho AI bridge.
2. Giới hạn CORS theo domain và thêm quota/rate limit.
3. Bổ sung 10–15 test quan trọng: wizard, validation, RBAC/IDOR, expense, AI parse, apply transaction và E2E happy path.
4. Làm tài liệu V2 khớp code; chuyển mọi phần chưa làm thành Future Work.
5. Hoàn thành báo cáo PDF ≥20 trang và slide tiếng Anh.
6. Chuẩn bị tài khoản/demo data hợp lệ và video backup.

### Trong 2–4 tuần

1. Đưa Expo auth/trips/chat lên cùng Worker và D1.
2. Thêm API CRUD đầy đủ, foreign key, unique/check constraints và optimistic concurrency.
3. Làm AI draft → validate → preview diff → apply → rollback.
4. Triển khai Nhịp Chung MVP: preferences, proposals, scoring và voting.
5. Tạo AI evaluation suite chạy không phụ thuộc Internet bằng fixtures.

### Trong 1–3 tháng

1. Route/time-window/budget optimizer.
2. Retrieval index cho dữ liệu địa điểm Việt Nam có provenance.
3. Feedback learning và personalization có quyền kiểm soát dữ liệu.
4. Offline/read-only trip pack trên mobile.
5. Booking import và expense settlement thật.
6. Observability: latency, error rate, provider health, token cost và hallucination report.

## 10. Kịch bản demo bảo vệ

Demo chỉ nên dài 6–8 phút:

1. Nêu pain point của nhóm đi du lịch: mỗi người một sở thích, khó thống nhất.
2. Tạo chuyến thành công.
3. Mời thành viên hoặc trình bày rõ giới hạn nếu chưa có backend sync.
4. Nhập preferences.
5. AI lấy thời tiết/địa điểm thật và hiển thị nguồn.
6. Tạo phương án lịch trình, preview rồi apply.
7. Thêm chi phí.
8. Cho xem một test phân quyền và một test AI validation.
9. Kết luận bằng kiến trúc và roadmap Nhịp Chung.

Không nên demo tính năng credential-dependent như Booking hoặc Google Places nếu chưa kiểm tra ngay trước buổi bảo vệ.

## 11. Câu hỏi hội đồng có thể hỏi

1. TravelMate khác Wanderlog/Mindtrip ở đâu?
2. Vì sao gọi là AI thay vì chatbot gọi API?
3. Làm sao chứng minh AI không bịa dữ liệu?
4. Nếu nguồn bên ngoài chết thì hệ thống xử lý thế nào?
5. Web và mobile có cùng database không?
6. Mật khẩu Expo được bảo vệ ra sao?
7. Thành viên có thể sửa chuyến không thuộc quyền không?
8. Apply itinerary lỗi giữa chừng có mất lịch cũ không?
9. Rate limit và kiểm soát chi phí AI ở đâu?
10. Nhịp Chung hiện chạy thật đến mức nào?
11. Nhóm đã đo chất lượng AI bằng bộ dữ liệu nào?
12. Vì sao tài liệu có bảng/API mà code không có?

## 12. Kết luận cuối

TravelMate không yếu ở ý tưởng hoặc thẩm mỹ. Điểm yếu lớn nhất là **khoảng cách giữa hình ảnh sản phẩm và bằng chứng engineering**. Việc cần làm không phải thêm nhiều màn hình hay thêm một chatbot nữa, mà là hoàn thiện một luồng xuyên suốt, chạy ổn định, có test và có sự khác biệt.

Ưu tiên đúng là:

> sửa core flow → thống nhất runtime → thu hẹp tuyên bố → chứng minh bằng test → triển khai Nhịp Chung có scoring/voting/versioning.

Nếu chỉ sửa P0 và trình bày trung thực, đồ án có thể đạt mức khá. Nếu biến Nhịp Chung thành workflow thật và đo được chất lượng AI, đồ án mới có cơ sở đạt mức giỏi vững chắc.

## Phụ lục — giới hạn báo cáo browser-only nhận được

File browser-only được cung cấp kết thúc giữa dòng F13. Nó không chứa phần AI test hoàn chỉnh, ma trận đối thủ, bug list đầy đủ hoặc roadmap đã yêu cầu. Báo cáo hợp nhất này giữ lại các quan sát có thể tái hiện và bổ sung bằng source/runtime/nguồn chính thức; không coi các phần bị thiếu là đã kiểm tra.

## Phụ lục customer/UX research

Bản tổng hợp customer journey, persona, so sánh TravelMate với Wanderlog/Mindtrip/TripIt/Layla/Roadtrippers và phân loại tính năng mới/overclaim nằm tại [CUSTOMER_UX_RESEARCH_TRAVELMATE_VS_COMPETITORS.md](D:/Learn/DACN2/TravelAI/CUSTOMER_UX_RESEARCH_TRAVELMATE_VS_COMPETITORS.md).
