# Lịch sử cập nhật TravelMate AI — v1 đến v12

Cập nhật gần nhất: 2026-08-11.

Tài liệu này ghi lại cả ba phần tạo nên một phiên bản AI của TravelMate:

- **Dữ liệu/fine-tune:** năng lực được đưa vào tập huấn luyện và kết quả của adapter Qwen.
- **Runtime/backend:** state, grounding, guardrail và logic tất định bao quanh model.
- **Trạng thái phát hành:** candidate nghiên cứu hay phiên bản thực sự được bật cho demo.

Vì vậy, số điểm của **raw model** không đồng nghĩa với chất lượng cuối của API. Từ v3 trở đi, model luôn chạy sau các lớp kiểm tra của backend.

## Tóm tắt nhanh

| Phiên bản | Trọng tâm | Dữ liệu bổ sung | Kết quả/Quyết định chính |
|---|---|---:|---|
| v1 | Nền tảng dữ liệu và QLoRA | 1.200 hội thoại | Dựng pipeline; candidate học template quá nhanh, không tích hợp |
| v2 | Reinforcement và guardrail cơ bản | 180 mẫu | Challenge raw 64%; giữ làm candidate nghiên cứu |
| v3 | Grounding lịch trình | 760 mẫu | Structured test 40/40; chọn cho luồng lịch có grounding |
| v4 | Hội thoại nhiều lượt tự nhiên | 240 hội thoại | Bản đầu lỗi NaN; v4-fixed sửa được nhưng challenge raw 52%, không promote mặc định |
| v5 | Bộ nhớ hội thoại và câu trả lời ngắn | 400 hội thoại | Replay demo pass; challenge raw 52%; bật local để đánh giá |
| v6 | Mở rộng dữ liệu điểm đến | 560 mẫu | Catalog 20 → 35 điểm; grounding mới 28/30; bật local demo |
| v7 | Tự lập lịch, chia ngân sách, checklist | 420 mẫu | Raw intent 9/16; runtime thực thi đủ ba nhóm; bật local demo |
| v8 | Chuyển/reset state tổng quát | 560 hội thoại | Raw transition 11/20; runtime regression 6/6; bật v8 |
| v9 | UX hội thoại tự nhiên | 455 hội thoại mới | UX 16/20, transition 17/20, demo 20/20; promote local |
| v10 | Suy luận có ràng buộc | 525 mẫu mới | Adapter thử nghiệm bị loại; hybrid guarded reasoning 20/20 |
| v11 | Grounding toàn quốc | 952 mẫu mới | Structured 34/34; alias/free text 22/34; giữ làm candidate, chưa thay v10 |
| v12 | Hội thoại grounded | 888 mẫu mới | R3 grounded 102/102, structured 34/34, demo 20/20; production hiện tại |

## v1 — Nền tảng dữ liệu và pipeline QLoRA

### Mục tiêu

- Dựng quy trình sinh, review, phê duyệt, chia split, train QLoRA và đánh giá Qwen3-4B trên GPU 6 GB.
- Tạo 1.200 hội thoại thuộc tám nhóm: lịch trình, ngân sách, lưu trú, ăn uống, an toàn/thời tiết, giới hạn realtime, ngoài phạm vi và giới hạn giao dịch.
- Gắn `splitGroup`, `reviewBatch` và `reviewStatus` để kiểm soát rò rỉ và chất lượng dữ liệu.

### Kết quả

- Split dùng cho candidate: 960 train, 120 validation, 120 test.
- Candidate một epoch đạt train loss `0,0266`, validation loss `0,0246`, token accuracy `99,39%` nhưng challenge behavior chỉ `64%`.
- Loss gần tuyệt đối cho thấy model học template quá nhanh, chưa chứng minh khả năng tổng quát.

### Quyết định

- Không tích hợp candidate v1.
- Giữ v1 làm nền dữ liệu và pipeline để phát triển các vòng tiếp theo.

## v2 — Reinforcement cho tình huống khó

### Cập nhật

- Thêm 180 mẫu không trùng bộ challenge.
- Phủ tiếng lóng ngân sách, thiếu thông tin, ngân sách bất khả thi, dữ liệu realtime, bẫy địa danh, an toàn, ngoài phạm vi và ranh giới giao dịch.
- Bộ train kết hợp tăng lên 1.140 mẫu; validation/test v1 giữ nguyên, mỗi tập 120 mẫu.

### Kết quả

- Train loss `0,8991`; validation loss `0,1863`; token accuracy `95,89%`.
- Challenge raw đạt `64%`; hỏi lại thông tin thiếu `9/9`.
- Vẫn có nguy cơ bịa địa điểm, tự suy ra điểm đến và xử lý safety/realtime chưa ổn định.

### Quyết định

- Giữ adapter v2 làm candidate nghiên cứu, chưa dùng mặc định trong app.
- Xác định grounding và guardrail backend là yêu cầu bắt buộc cho vòng sau.

## v3 — Lịch trình có grounding

### Cập nhật

- Thêm 200 hội thoại guardrail và 560 mẫu lịch trình JSON có cấu trúc.
- Tổng split: 1.820 train, 160 validation, 160 test.
- Tạo catalog đóng gồm 20 điểm đến, mỗi điểm có ba `placeId` chuẩn.
- Model chỉ sinh `day`, `period`, `kind`, `placeId`; backend kiểm schema, whitelist rồi mới ánh xạ sang tên địa điểm.
- Bổ sung chặn bằng code cho ngoài phạm vi, giao dịch, y tế, dị ứng, thời tiết nguy hiểm và hành khách dễ tổn thương.

### Kết quả

- Train loss `0,5526`; validation loss `0,1022`; token accuracy `98,02%`.
- Structured held-out đạt `40/40` về schema và grounding.
- Challenge raw vẫn `64%` và còn lỗi nghiêm trọng nếu bỏ lớp backend.

### Quyết định

- Chọn v3 cho luồng lập lịch có grounding.
- Không cho model thô tự xác nhận địa danh, dữ kiện realtime hoặc giao dịch.

## v4 — Hội thoại nhiều lượt tự nhiên

### Cập nhật

- Thêm 240 hội thoại bốn lượt trên 20 điểm đến: hỏi lần lượt thông tin thiếu, sửa ý, ngân sách, follow-up địa điểm/ẩm thực và ngôn ngữ đời thường.
- Chuẩn hóa cách xưng hô `mình - bạn`, trả lời ngắn, không Markdown và hỏi tối đa một câu mỗi lượt.
- Tổng split sau khi ghép v3: 2.020 train, 180 validation, 180 test.
- Backend giữ raw history ngắn nhưng tổng hợp state có cấu trúc từ toàn bộ lịch sử.

### Kết quả

- Candidate đầu dùng prompt quá dài, làm mất completion ở context 512 và cho validation loss `NaN`; bản này bị loại.
- `v4-fixed` rút prompt, thêm preflight kiểm token: train loss `0,6685`, validation loss `0,3376`.
- Nhớ đúng ngữ cảnh hội thoại mục tiêu, nhưng challenge raw chỉ `52%`, thấp hơn v3.

### Quyết định

- Không đổi adapter mặc định trong mã nguồn.
- Chỉ dùng v4-fixed ở local để đánh giá hội thoại sau guardrail.

## v5 — Hội thoại có state

### Cập nhật

- Thêm 400 hội thoại: hội thoại dài, câu trả lời ngắn như `rồi/chưa/có/không`, đổi intent, xung đột state, realtime và safety.
- Tổng split: 2.320 train, 230 validation, 230 test.
- Memory lưu thêm chi phí di chuyển, nhịp chuyến đi và sở thích.
- Gắn câu trả lời ngắn với câu hỏi assistant ngay trước; ưu tiên trả checklist khi người dùng hỏi; loại bỏ default gắn với điểm đến cũ khi đổi chuyến.

### Kết quả

- Train loss `0,7447`; validation loss `0,6314`; token accuracy `85,85%`.
- Challenge raw `52%`.
- Replay FastAPI của chuỗi lỗi demo pass: hỏi đúng slot còn thiếu, hiểu `rồi`, trả checklist trực tiếp và giữ đúng quan hệ Huế–Miền Trung.

### Quyết định

- Bật v5 trong `.env` local để đánh giá; vẫn giữ guardrail/state/validation bắt buộc.

## v6 — Mở rộng điểm đến và gợi ý vùng–chủ đề

### Cập nhật

- Catalog tăng từ 20 lên 35 điểm đến; mỗi điểm có `region` và `themes`.
- Thêm 15 điểm đến, gồm Cát Bà, Cô Tô, Quan Lạn, Móng Cái/Trà Cổ, Đồ Sơn, Mộc Châu, Mai Châu, Tam Đảo, Sầm Sơn, Cửa Lò, Phú Yên, Lý Sơn, Côn Đảo, Châu Đốc và Bến Tre.
- Thêm 420 itinerary JSON grounded và 140 hội thoại region–theme.
- Tổng split: 2.785 train, 278 validation, 277 test.
- Thay danh sách gợi ý hardcode bằng truy vấn catalog theo vùng và sở thích.

### Kết quả

- Train loss `0,5799`; validation loss `0,5254`.
- Challenge raw `56%`.
- Structured grounding cho điểm mới đạt `28/30`; hai output ngoài whitelist bị backend chặn.
- Replay `Miền Bắc → biển → gợi ý` trả đúng nhóm điểm biển miền Bắc.

### Quyết định

- Bật v6 cho demo local; tiếp tục bắt buộc itinerary validator.

## v7 — Thực thi intent ngay

### Cập nhật

- Thêm 420 mẫu: 140 lập lịch, 105 phân bổ ngân sách, 105 checklist và 70 yêu cầu kết hợp.
- Tổng split: 3.065 train, 350 validation, 345 test.
- Tách `itinerary_intent`, `budget_intent`, `preparation_intent` và hỗ trợ nhiều intent trong một câu.
- Khi đủ dữ liệu, backend thực thi ngay thay vì hỏi người dùng chọn loại hỗ trợ.
- Quy tắc ngân sách: lưu trú 35%, ăn uống 25%, di chuyển 20%, tham quan 15%, dự phòng 5%.

### Kết quả

- Train loss `0,5715`; validation loss `0,4476`.
- Raw intent held-out `9/16`: ngân sách `4/4`, checklist `4/4`, lịch `1/4`, yêu cầu kết hợp `0/4`.
- Replay API trả đủ lịch 3 ngày, năm hạng mục ngân sách, năm nhóm checklist và câu kết hợp cả ba phần.

### Quyết định

- Bật v7 local nhờ runtime thực thi ổn định; không dựa vào raw model cho lịch kết hợp hoặc safety.

## v8 — Chuyển chuyến, sửa slot và reset tổng quát

### Cập nhật

- Thêm 560 hội thoại trên 35 điểm đến: đổi điểm đến, đổi vùng, sửa slot, reset và giữ chuyến.
- Tổng split: 3.450 train, 440 validation, 430 test.
- Xử lý tổng quát các cấu trúc `X thay cho Y`, `thay Y bằng X`, `đổi từ Y sang X`.
- Đổi điểm đến/vùng sẽ xóa slot phụ thuộc; sửa ngân sách/thời lượng/số người chỉ cập nhật slot được nêu; nhắc cùng điểm đến giữ state.
- Reset tự nhiên xóa toàn bộ state và trả `resetContext=true` cho UI.

### Kết quả

- Train hoàn tất 216/216 bước; mean logged loss `0,5377`. Validation cuối epoch gặp lỗi CUDA nên không công bố validation loss.
- Raw transition held-out `11/20`: đổi vùng `4/4`, reset `4/4`, đổi điểm đến `3/4`; tiêu chí echo đầy đủ cho sửa/giữ slot chưa đạt.
- Runtime regression `6/6`, backend test `127 passed`, Ruff sạch.
- Ma trận demo API độc lập đạt `20/20` với `provider=local`, `modelVersion=v8`.

### Quyết định

- Bật v8 dựa trên state machine tổng quát; giữ `11/20` làm baseline trung thực cho raw adapter.

## v9 — UX hội thoại tự nhiên

### Cập nhật

- Tiếp tục fine-tune từ v8 với learning rate thấp `1e-5`.
- Thêm 455 hội thoại thuộc năm nhóm: multi-slot, correction, retention, clean switch và clarification.
- Train dùng 305 mẫu mới + 600 replay v8 = 905; validation 77 mới + 100 replay = 177; UX held-out gồm 20 ca.
- Runtime làm mượt câu xác nhận nhiều slot, sửa chuyến, giữ state và hỏi làm rõ; vẫn ghép các phần lịch/ngân sách/checklist theo logic tất định.

### Kết quả

- Train loss `0,2192`; validation loss `0,2784`; token accuracy `93,63%`.
- Raw UX `16/20`.
- Transition tăng từ `11/20` lên `17/20`; intent tăng từ `9/16` lên `11/16`.
- Runtime demo matrix `20/20`; backend `138 passed`; Ruff sạch.
- Điểm yếu còn lại: hai biến thể clarification và câu kết hợp dài.

### Quyết định

- Promote adapter v9; Qwen local trở thành provider mặc định và UI/API hiển thị `v9`.

## v10 — Suy luận có ràng buộc và kiểm chứng

### Cập nhật dữ liệu

- Thêm 525 mẫu, chia đều năm nhóm: ưu tiên ràng buộc, sửa kế hoạch bất khả thi, so sánh phương án, phụ thuộc trình tự và xử lý bất định.
- Split phần mới: 350 train, 90 validation, 85 test; reasoning held-out gồm 20 ca cân bằng.
- Dữ liệu chỉ lưu kết luận, căn cứ ngắn và hành động tiếp theo; không lưu hay yêu cầu chain-of-thought nội bộ.
- Loại prompt thuộc challenge, UX, transition và intent held-out khỏi train để tránh rò rỉ.

### Kết quả thử nghiệm adapter

| Candidate | Reasoning held-out | Kết luận |
|---|---:|---|
| v9 baseline | 4/20 | Mốc so sánh |
| v10 mixed | 2/20 | Loại |
| v10 mixed + stage 2 | 2/20 | Loại |
| v10 focused từ v9 | 5/20 | Loại vì bịa giá và địa điểm |

Fine-tune chuyên biệt không đạt cổng phát hành. Không adapter v10 thử nghiệm nào được app sử dụng.

### Kiến trúc production

- Giữ nguyên trọng số LoRA v9 đã kiểm chứng.
- Thêm policy suy luận tất định, grounded theo catalog trước nhánh raw generation.
- Policy tính chính xác ngân sách/người/ngày, ưu tiên ràng buộc của nhóm dễ tổn thương, xếp ngày đến–ngày về, so sánh điểm đến theo theme đã xác minh và tạo phương án có điều kiện khi thiếu dữ liệu realtime.
- Chỉ trả kết luận, yếu tố quyết định ngắn và bước tiếp theo; không lộ chuỗi suy nghĩ nội bộ.

### Kết quả và quyết định

- Guarded reasoning held-out `20/20`.
- Runtime demo regression `20/20`.
- Backend `150 passed`; Ruff sạch.
- Production dùng đường dẫn `artifacts/travelmate-qwen3-4b-lora-v10-reasoning-guarded`, nhưng nguồn trọng số vẫn là v9; năng lực mới đến từ policy v10.
- API/UI báo `provider=local`, `modelVersion=v10`.

## v11 — Grounding toàn quốc

### Cập nhật

- Catalog theo 34 đơn vị hành chính cấp tỉnh hiện hành từ 01/07/2025; tên tỉnh,
  thành trước sắp xếp được giữ làm alias đầu vào.
- Thêm 952 mẫu cân bằng, đúng 28 mẫu cho mỗi tỉnh/thành: 748 lịch trình JSON
  grounded và 204 hội thoại nhận diện/gợi ý.
- Train gồm 748 mẫu mới + 700 replay v10; validation gồm 102 mẫu mới + 120
  replay. Các prompt held-out cũ và 68 ca nationwide smoke/alias không xuất hiện
  trong train.
- Runtime dùng whitelist `placeId` cho cả mã v11 và mã cũ tương thích ngược.

### Kết quả

- Train loss `0,4980`; validation loss `0,4168`; token accuracy trong epoch
  `91,67%`.
- Nationwide structured smoke đạt `34/34`: JSON đúng schema và mọi `placeId`
  đều thuộc whitelist của đúng tỉnh/thành.
- Nationwide alias/free-text chỉ đạt `22/34` (`64,71%`). Model còn bỏ sót tên
  tỉnh hiện hành hoặc sinh tên điểm không có trong catalog ở một số câu trả lời.
- Backend regression đạt `155 passed`; Ruff sạch.

### Quyết định

- Giữ adapter `travelmate-qwen3-4b-lora-v11-nationwide` làm candidate nghiên
  cứu cho luồng itinerary có validator.
- Chưa promote làm mặc định và chưa thay production v10. Hội thoại tự do vẫn
  phải đi qua catalog/guardrail; cần một vòng sửa dữ liệu và chạy lại toàn bộ
  regression cũ trước khi phát hành.
- Runtime sau đánh giá v11 đã chuyển gợi ý địa điểm/ẩm thực sang grounded
  conversation: nhận diện alias → truy xuất catalog → renderer/LLM → validator.
  Retrieval thời tiết đã dùng Open-Meteo với nguồn, thời điểm truy xuất,
  timeout/cache và fail-closed. RAG cho giá, giờ mở cửa và tình trạng dịch vụ
  vẫn chờ nguồn có quyền sử dụng, chưa được giả lập bằng dữ liệu tĩnh.

## v12 — Hội thoại grounded và ranh giới realtime

### Cập nhật

- Chèn cùng một `[GROUNDED_CATALOG]` dùng ở runtime vào dữ liệu hội thoại.
- Thêm 888 mẫu mới phủ 34 tỉnh/thành: 272 gợi ý catalog, 170 alias, 374
  realtime và 72 hard-negative cho các mã từng yếu ở v11.
- Split phần mới: 684 train, 102 validation, 102 test; không trộn held-out cũ
  vào train.
- Early canary của lượt đầu phát hiện bịa giá/giờ dù validation loss thấp. R2
  vì vậy tiếp tục bằng curriculum grounded riêng thay vì chấp nhận metric loss.

### Kết quả

- R2 train loss `0,1521`; validation loss `0,02869`; validation token accuracy
  `99,27%`.
- Current province `102/102`; đủ ba catalog places `100/102`; realtime
  boundary `101/102`; strict template `89/102`.
- 11/13 ca strict lệch chỉ khác thứ tự/dấu câu/cách diễn đạt nhưng vẫn đúng
  nội dung. Hai lỗi nội dung thật: Quảng Ngãi thiếu `chứng tích Sơn Mỹ`; An
  Giang sinh điểm ngoài catalog thay cho `Hà Tiên`.
- Nationwide structured smoke của r2 giữ `34/34` itinerary đúng schema và
  whitelist.
- Runtime/unit regression `207 passed`; Ruff sạch.

R3 tiếp tục từ r2 trên cùng 684 mẫu grounded với learning rate `5e-6` để sửa
hai lỗi nội dung mà không thay đổi phạm vi dữ liệu.

- Train loss `0,006539`; validation loss `0,01532`; validation token accuracy
  `99,76%`.
- Current province, đủ ba catalog places và realtime boundary đều `102/102`.
- Strict template `96/102`; sáu ca lệch chỉ khác cách diễn đạt, không sai
  grounding hay ranh giới realtime.
- Nationwide structured smoke giữ `34/34`; demo runtime đạt `20/20`.
- Runtime/unit regression sau mở rộng runtime `216 passed`; Ruff sạch.

### Quyết định

- Promote `travelmate-qwen3-4b-lora-v12-grounded-conversation-r3` thành adapter
  production sau khi các cổng nội dung, structured và runtime đều đạt.
- Runtime renderer, validator và itinerary whitelist vẫn là lớp bảo vệ bắt
  buộc; việc promote adapter không loại bỏ các guardrail này.
- Sau promotion, catalog runtime mở rộng từ ba lên sáu địa điểm cho 12 trung
  tâm/điểm nóng du lịch. Catalog train/held-out v12 vẫn đóng băng ở ba địa điểm;
  đây là mở rộng retrieval/runtime, không phải một lượt fine-tune mới.
- Runtime hỏi lại input lỗi dạng chữ-số dính liền và chặn tất định câu hỏi giá
  vé/giờ hoạt động khi chưa có nguồn realtime.
- Phản hồi thời tiết được rút gọn cho UX: chỉ trả dữ liệu dự báo và cảnh báo biến
  động, không hiển thị tên/URL nguồn hay thời điểm truy xuất. Metadata provider
  vẫn tồn tại nội bộ để kiểm thử, cache và truy vết lỗi.

## Trạng thái hiện tại

- Provider mặc định: **Qwen local**.
- Phiên bản hiển thị: **v12**.
- Adapter production: `artifacts/travelmate-qwen3-4b-lora-v12-grounded-conversation-r3`.
- Kiến trúc: **Qwen3-4B LoRA v12-r3 + state/grounding/guardrail + itinerary whitelist**.
- Các adapter v10 experimental chỉ giữ để phân tích offline, không được promote.

## Nguyên tắc cho phiên bản kế tiếp

- Không promote chỉ dựa vào train loss hoặc validation loss.
- Bắt buộc chạy lại reasoning, UX, transition, intent, challenge, demo matrix và backend regression.
- Dữ liệu test/held-out không được trộn vào train.
- Mọi dữ kiện địa điểm phải grounded theo catalog; giá, giờ mở cửa, thời tiết và tình trạng dịch vụ phải được coi là realtime/không chắc chắn nếu chưa có nguồn xác minh.
- Chỉ thay LoRA production khi adapter mới vừa tăng năng lực mục tiêu, vừa không làm giảm các suite cũ và không sinh claim không được hỗ trợ.
