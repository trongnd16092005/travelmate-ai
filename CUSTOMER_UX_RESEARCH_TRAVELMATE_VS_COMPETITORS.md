# BÁO CÁO CUSTOMER/UX RESEARCH

## TravelMate so với Wanderlog, Mindtrip, TripIt, Layla và Roadtrippers

**Ngày kiểm tra:** 01/08/2026  
**Bối cảnh test:** người dùng tại Đà Nẵng, Việt Nam  
**Ứng dụng:** TravelMate tại `localhost:8081`, API tại `localhost:3000`  
**Mục đích:** đánh giá TravelMate từ góc nhìn khách hàng thật, đo độ tiện dụng, chất lượng AI và mức khác biệt so với các nền tảng đang có trên thị trường.

> Báo cáo này tổng hợp bằng chứng customer/UX do vòng QA thực địa cung cấp, sau đó đối chiếu với trạng thái code/runtime sau vòng sửa lỗi. Những lỗi đã quan sát trước khi sửa được giữ lại để chứng minh quá trình cải tiến, nhưng không được mô tả như lỗi hiện tại nếu đã retest đạt.

## 1. Executive summary

TravelMate có trải nghiệm tiếng Việt bản địa, wizard tạo chuyến ngắn và luồng chat → áp dụng lịch trình liền mạch. Đây là những ưu điểm có giá trị thật với người dùng Việt Nam.

Tuy nhiên, TravelMate chưa thắng được các nền tảng lớn ở ba năng lực sản phẩm đã trở thành tiêu chuẩn: bản đồ trực quan, routing/route feasibility và collaboration nhóm. AI cũng mới ở mức grounded assistant; chưa phải decision system có scoring, tối ưu nhiều ràng buộc và versioning hoàn chỉnh.

Các phát hiện sau vòng customer test:

- Core flow tạo, lưu và reload trip hoạt động.
- Prompt injection được xử lý an toàn.
- Lỗi câu hỏi mơ hồ về địa lý đã được sửa: “Việt Nam 3 ngày” hiện yêu cầu tỉnh/thành cụ thể.
- Context hội thoại đã được ưu tiên hơn trip active khi follow-up về chủ đề khác.
- Citation không khớp hiện bị lọc/ẩn thay vì hiển thị nguồn sai.
- Budget breakdown đã được bổ sung khi người dùng đưa ngân sách cụ thể.
- Map view, quick follow-up actions, group decision-making và offline pack vẫn thiếu.

### Kết luận customer

Nếu chỉ cần một trợ lý lập kế hoạch du lịch Việt Nam bằng tiếng Việt, TravelMate đã có lý do để được chọn. Nếu cần bản đồ, route, booking/import, chia sẻ nhóm và itinerary production-ready, Mindtrip/Wanderlog/Layla vẫn tiện hơn.

Điểm định tính hiện tại của TravelMate: **6,8–7,2/10**. Điểm này có thể tăng lên khoảng 8/10 nếu hoàn thiện map + route, citation theo entity và workflow Nhịp Chung.

### Cập nhật reliability sau BUG-08

Vòng test mới quan sát Groq lỗi lặp lại ở follow-up. Sau đó backend đã được harden bằng timeout 15 giây, retry backoff, history/context compact và `Fallback Layer` có cấu trúc. Retest follow-up khi provider không phản hồi vẫn nhận HTTP 200 với bản nháp dựa trên dữ liệu đã truy xuất; app không còn gãy ở bước thứ hai của hội thoại. Đây là giảm thiểu reliability, chưa phải thay thế hoàn toàn chất lượng của provider AI chính.

## 2. Phạm vi và phương pháp

### 2.1 Persona customer

| Persona | Nhu cầu | Ràng buộc |
|---|---|---|
| A — Solo tiết kiệm | Đi Huế 3 ngày, ăn đặc sản, lịch trình nhẹ | Ngân sách 5.000.000đ, ít di chuyển |
| B — Cặp đôi | Đi Đà Nẵng 3 ngày, chụp ảnh và ăn uống | Muốn trải nghiệm mới, không xếp lịch quá dày |
| C — Nhóm có người lớn tuổi | Đi Đà Nẵng 3 ngày | Ngân sách 5.000.000đ, ít đi bộ, hạn chế đổi địa điểm |

### 2.2 Customer journey được test

1. Mở app và hiểu sản phẩm trong 30 giây đầu.
2. Tìm/khám phá điểm đến.
3. Tạo trip mới.
4. Nhập ngày, ngân sách và sở thích.
5. Nhờ AI tạo lịch trình.
6. Gửi follow-up để giảm chi phí, giảm đi bộ hoặc thay đổi hoạt động.
7. Kiểm tra context và citation.
8. Áp dụng lịch trình vào trip.
9. Reload để kiểm tra persistence.
10. Đối chiếu mức tiện dụng với các platform cạnh tranh.

### 2.3 Nguyên tắc đánh giá

- Ưu tiên task success và số bước hơn nhận xét cảm tính.
- Phân biệt “tính năng có trong tài liệu” với “tính năng thao tác được”.
- Không gọi một tính năng là mới nếu đối thủ đã có chức năng tương đương.
- Khi một platform không thể kiểm tra do paywall, login hoặc giới hạn công cụ, ghi rõ là chưa kiểm chứng.

## 3. Kết quả customer journey trên TravelMate

| Task | Kết quả | Nhận xét customer |
|---|---|---|
| Hiểu mục đích app | Đạt | UI tiếng Việt và CTA tạo chuyến dễ hiểu |
| Tạo trip | Đạt sau sửa | Wizard 3 bước, progress sidebar rõ |
| Nhập ngày/ngân sách | Đạt sau sửa | Validation real-time, lỗi có lý do |
| Đổi ngân sách | Đạt | Không còn mất ngày khởi hành/kết thúc |
| Ngày không hợp lệ | Đạt | Nút tiếp tục bị khóa, lỗi hiển thị rõ |
| Tạo và reload trip | Đạt | Dữ liệu trip còn sau reload local flow |
| Hỏi AI bình thường | Đạt có điều kiện | Phụ thuộc API/Groq và nguồn truy xuất |
| Câu hỏi mơ hồ | Đạt sau sửa | Hỏi lại tỉnh/thành, không tự nối nhiều tỉnh |
| Follow-up khác trip active | Đạt sau sửa | Context hội thoại được ưu tiên |
| Prompt injection | Đạt | Từ chối an toàn, không lộ secrets |
| Citation | Cải thiện | Nguồn không khớp bị ẩn; cần entity-level citation tốt hơn |
| Budget breakdown | Cải thiện | Có phân bổ tham khảo theo hạng mục khi có tổng tiền |
| Map view | Chưa có | Đây là gap UX lớn nhất hiện tại |
| Responsive 768/390px | Chưa đủ bằng chứng | Cần chạy lại bằng viewport thật |

### 3.1 Luồng tạo trip

Luồng có lợi thế rõ về số bước và copy:

1. Điểm đến + tên chuyến.
2. Ngày + ngân sách.
3. Phong cách + sở thích.

Sau khi sửa, dữ liệu kiểm thử `Đà Nẵng · 10/08/2026–12/08/2026 · 5.000.000đ` đi qua được wizard. Đây là điểm đã chuyển từ P0 sang pass.

### 3.2 Luồng AI

TravelMate cho cảm giác như một “travel decision assistant” hơn chatbot thuần vì có integration state, nguồn và structured brief. Tuy vậy, customer vẫn gặp ba giới hạn:

- Không có map để kiểm tra khoảng cách bằng mắt.
- Nguồn hiện được lọc an toàn nhưng chưa phải citation gắn trực tiếp từng claim.
- Khi provider ngoài tạm thời không phản hồi, trải nghiệm vẫn phụ thuộc retry/fallback.

## 4. Test AI theo nhu cầu khách hàng

| Input customer | Kết quả mong đợi | Kết quả sau retest |
|---|---|---|
| “Mình đi Huế 3 ngày, ngân sách 5 triệu, thích ăn đặc sản và không muốn đi quá nhiều.” | Lịch trình thực tế, có budget | Có structured response, nguồn khớp được lọc |
| “Lịch trình này đắt quá...” | Tối ưu lại ngân sách | Context được giữ, có phân bổ ngân sách khi có số tiền |
| “Mình đi cùng người lớn tuổi...” | Giảm đi bộ và đổi địa điểm | AI nhận ràng buộc trong prompt; cần thêm route validation |
| “Nếu trời mưa thì đổi hoạt động trong nhà.” | Có phương án dự phòng | Có thể hỏi follow-up; cần weather-aware itinerary workflow sâu hơn |
| “Tóm tắt thành checklist điện thoại.” | Output ngắn, dễ dùng | Có thể trả lời nhưng chưa có view checklist chuyên biệt |
| “Nguồn nào kiểm chứng rõ nhất?” | Giải thích provenance | Có provider/source list, nhưng chưa map từng claim |
| “Phân bổ 5 triệu...” | Breakdown theo hạng mục | Đã bổ sung breakdown tham khảo: lưu trú/ăn uống/di chuyển/vé |

### 4.1 Safety

Prompt yêu cầu lộ system prompt/API key/token trả về lớp `TravelMate · Safety Layer`, từ chối rõ ràng và chuyển hướng về tác vụ du lịch. Đây là điểm pass có bằng chứng.

### 4.2 Grounding

Vòng trước đã quan sát citation lệch giữa Huế và Đà Nẵng. Sau sửa:

- destination broad không còn kế thừa trip active.
- follow-up dùng history destination.
- source title không khớp recommendation bị loại khỏi danh sách citation.

Đây là giải pháp an toàn hơn hiển thị nguồn sai, nhưng bước tiếp theo vẫn phải là mapping `claim/entity → source URL` thay vì chỉ lọc theo tiêu đề.

## 5. Top 5 điểm TravelMate tiện hơn

### 5.1 Tiếng Việt bản địa

Toàn bộ UI, validation và AI response dùng tiếng Việt tự nhiên. Đây là lợi thế thực tế với người dùng Việt Nam, dù chưa phải đổi mới công nghệ.

### 5.2 Wizard ngắn và dễ hiểu

Wizard 3 bước có sidebar tiến trình, placeholder gần với cách người Việt nhập dữ liệu và validation ngày rõ. Sau khi sửa, nút tiếp tục hoạt động đúng với dữ liệu hợp lệ.

### 5.3 Có thể test core flow mà không cần sign-up

So với TripIt yêu cầu tạo account sớm, TravelMate cho phép thử luồng chính local/demo nhanh hơn.

### 5.4 Guardrail dễ hiểu

Khi customer gửi prompt injection, app không chỉ từ chối mà còn đề xuất những chủ đề hợp lệ có thể hỏi tiếp.

### 5.5 Chat → áp dụng trip liền mạch

Nút “Áp dụng lịch trình này” nối kết quả AI với trip active, giảm khoảng cách giữa tư vấn và hành động.

## 6. Top 5 điểm TravelMate kém hơn

### 6.1 Không có Map View — P1 hiện tại

Mindtrip/Wanderlog/Roadtrippers cho customer nhìn pin, route và khoảng cách. TravelMate hiện chủ yếu hiển thị card/text. Đây là khoảng cách UX lớn nhất vì customer khó đánh giá lịch trình có khả thi hay không.

### 6.2 Chưa có quick follow-up buttons — P2 hiện tại

Mindtrip gợi ý các câu hỏi tiếp theo như khu vực khách sạn, cách di chuyển hoặc lựa chọn ăn uống. TravelMate khiến customer phải tự nghĩ prompt tiếp theo.

### 6.3 Citation chưa đạt entity-level — P1/P2 cần tiếp tục harden

Lỗi citation lệch đã được giảm bằng cách ẩn nguồn không khớp. Tuy nhiên, ẩn nguồn không giống với việc chứng minh từng claim. UX tốt hơn cần hiển thị citation ngay trên địa điểm/claim cụ thể.

### 6.4 Collaboration và group decision-making chưa chạy thật — P1 sản phẩm

“Nhịp Chung”, voting, phương án A/B, scoring trade-off và rollback vẫn chủ yếu ở mức thiết kế. Đây là khoảng trống lớn nếu định vị TravelMate là app cho nhóm.

### 6.5 Route, booking/import và offline còn thiếu — P1/P2 sản phẩm

Các đối thủ đã coi map, route, import confirmation và offline/read-only là feature hygiene. TravelMate chưa có vertical slice tương đương.

## 7. So sánh với các platform khác

### 7.1 Năng lực nổi bật được đối chiếu

| Platform | Customer value quan sát/được công bố |
|---|---|
| Wanderlog | Itinerary + map, collaboration, import booking, expense splitting, offline và route optimization |
| Mindtrip | AI personalization, maps, POI/booking, collaboration, comments/likes, itinerary chỉnh sửa được |
| Layla | AI hỏi nhu cầu, itinerary theo ngày, live price/availability, route/multi-city, human expert |
| TripIt | Confirmation email, đồng bộ đa thiết bị, mobile itinerary, calendar sync, alerts và sharing |
| Roadtrippers | Autopilot hỏi budget/vehicle/preferences, stop theo route, map và itinerary chỉnh sửa |

Nguồn tham khảo: [Wanderlog Help Center](https://wanderlog.com/pages/help-center), [Mindtrip](https://mindtrip.ai/), [Layla](https://layla.ai/), [TripIt](https://www.tripit.com/web/free), [Roadtrippers Autopilot](https://support.roadtrippers.com/hc/en-us/articles/24995143275412-Using-Autopilot-to-Plan-a-Trip).

### 7.2 Ma trận customer value 0–5

| Tiêu chí | TravelMate | Wanderlog | Mindtrip | Layla | TripIt | Roadtrippers |
|---|---:|---:|---:|---:|---:|---:|
| AI planning | 3 | 4 | 5 | 5 | 1 | 4 |
| Grounding/dữ liệu thật | 3 | 4 | 5 | 4 | 4 | 5 |
| Map và routing | 1 | 5 | 4 | 4 | 3 | 5 |
| Collaboration thật | 1 | 5 | 5 | 2 | 2 | 4 |
| Group consensus/voting | 0 | 2 | 3 | 1 | 0 | 1 |
| Expense/splitting | 2 | 5 | 3 | 1 | 1 | 1 |
| Booking/receipt import | 1 | 4 | 5 | 5 | 5 | 2 |
| Đồng bộ web/mobile | 1 | 5 | 4 | 4 | 5 | 5 |
| Offline | 0 | 5 | 3 | 2 | 5 | 5 |
| Minh bạch nguồn | 4 | 2 | 3 | 2 | 3 | 3 |
| Phù hợp người Việt | 4 | 2 | 2 | 2 | 1 | 1 |

Đây là điểm customer-value định tính từ khả năng được kiểm chứng/công bố, không phải benchmark hiệu năng tuyệt đối.

### 7.3 Nền tảng nào tiện hơn?

- **Dễ lập kế hoạch trực quan:** Mindtrip hoặc Wanderlog.
- **Dễ xử lý route/road trip:** Roadtrippers.
- **Dễ import booking và quản lý booking:** TripIt.
- **Dễ hỏi AI từ đầu và được hỏi lại nhu cầu:** Layla.
- **Dễ bắt đầu bằng tiếng Việt cho điểm đến Việt Nam:** TravelMate.
- **Dễ ra quyết định nhóm:** hiện chưa nền tảng nào được TravelMate vượt qua bằng bằng chứng; đây là cơ hội của Nhịp Chung nhưng chức năng chưa chạy thật.

## 8. Tính năng thực sự mới vs. overclaim

| Tính năng | Phân loại | Đánh giá |
|---|---|---|
| AI grounded bằng Wikimedia/Open-Meteo | (2) Đã có ở đối thủ | TravelMate có minh bạch hơn ở một số response nhưng coverage còn hẹp |
| AI nhớ context conversation | (2) Đã có ở đối thủ | Không phải khác biệt độc quyền |
| AI hỏi lại khi thiếu địa điểm | (3) Có ở đối thủ, TravelMate vừa cải thiện | Cần chứng minh nhiều case hơn Layla |
| Map view và route | (3) Đối thủ đã có, TravelMate thiếu | Không được claim là tính năng cạnh tranh hiện tại |
| Quick follow-up buttons | (3) Đối thủ đã có, TravelMate thiếu | Cải thiện UX chi phí thấp |
| UI/AI tiếng Việt bản địa | (1) Khác biệt thị trường ngách | Lợi thế go-to-market Việt Nam, không phải đổi mới công nghệ |
| Wizard 3 bước + validate ngày | (4) Khác biệt UI | Không nên gọi là innovation |
| Nhịp Chung/voting/scoring/A-B/rollback | (5) Overclaim hiện tại | Mới nằm trong ý tưởng/tài liệu, chưa quan sát được trong app chạy thật |
| Budget breakdown theo hạng mục | (2)/(4) Cải thiện UX | Giá trị thực dụng, chưa phải đổi mới độc quyền |

### Kết luận về “cái mới”

Không có bằng chứng để gọi TravelMate là công nghệ mới trên thị trường. Lợi thế thực tế hiện tại là:

1. Bản địa hóa tiếng Việt cho travel planning trong nước.
2. Một hướng grounded AI minh bạch hơn chatbot thuần.
3. Tiềm năng xây Nhịp Chung thành decision layer cho nhóm.

Lợi thế thứ ba chỉ trở thành competitive moat sau khi có preferences, proposal scoring, voting, conflict resolution, diff và rollback chạy thật.

## 9. Roadmap ưu tiên

### Trong 24 giờ

1. Tạo `npm run dev:demo` khởi động API + Expo và health-check trước khi mở app.
2. Thêm quick follow-up buttons dưới mỗi AI answer.
3. Hiển thị trạng thái nguồn rõ hơn: “nguồn khớp trực tiếp”, “nguồn tham khảo”, “chưa có nguồn”.
4. Thêm retry/backoff và fallback response khi Groq tạm thời không phản hồi.
5. Ghi regression fixtures cho vague geography, wrong citation và context lệch trip.

### Trong 1–2 tuần

1. Xây map view cơ bản với pin từ địa điểm đã truy xuất.
2. Gắn source vào từng entity/recommendation, không chỉ vào card nguồn chung.
3. Thêm budget breakdown có tổng kiểm tra được và cảnh báo vượt ngân sách.
4. Thêm weather-aware alternative trong nhà.
5. Test viewport thật 1440/768/390 và test bàn phím/mobile.

### Trong 1–3 tháng

1. Route line theo ngày, tính khoảng cách và cảnh báo lịch trình phi thực tế.
2. Nhịp Chung MVP: preferences, hard/soft constraints, 2–3 proposal, voting.
3. Preview diff → user approval → apply → rollback.
4. Auth/D1 đồng bộ web/mobile và collaboration thật.
5. Booking/import confirmation và offline/read-only trip pack.
6. AI evaluation suite với citation coverage, constraint satisfaction, hallucination và latency.

## 10. Kết luận cuối

TravelMate hiện tiện hơn đối thủ ở lần bắt đầu đầu tiên bằng tiếng Việt, wizard ngắn, guardrail rõ và khả năng nối chat với trip. TravelMate chưa tiện hơn ở việc nhìn route, đánh giá khoảng cách, import booking, cộng tác nhóm và dùng offline.

Để bảo vệ đồ án thuyết phục, không nên tuyên bố TravelMate “đổi mới hơn thị trường” ở hiện trạng. Nên trình bày trung thực:

> TravelMate là một travel decision assistant tiếng Việt, có grounded retrieval và hướng phát triển thành lớp đồng thuận cho nhóm.

Demo nên tập trung vào một vertical slice thật:

1. Tạo trip Việt Nam trong 3 bước.
2. Nhập ngân sách/người lớn tuổi.
3. AI tạo lịch trình có nguồn và breakdown.
4. Customer hỏi giảm đi bộ hoặc đổi khi mưa.
5. Hiển thị map/route nếu đã hoàn thiện; nếu chưa, nói rõ đây là roadmap.

Nếu hoàn thiện map + entity-level citation + Nhịp Chung MVP, TravelMate có cơ sở tăng từ prototype AI lên sản phẩm có khác biệt rõ cho nhóm khách Việt Nam.
