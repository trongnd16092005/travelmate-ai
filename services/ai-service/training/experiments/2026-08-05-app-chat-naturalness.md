# Đánh giá độ tự nhiên của chat trong app — 2026-08-05

## Phạm vi

Đánh giá trực tiếp giao diện Expo Web tại `/ai`, FastAPI và provider Gemini với
ngữ cảnh Đà Nẵng, 2 người, ngân sách 5 triệu. Bài thử tập trung vào hội thoại
nhiều lượt thay vì loss/token accuracy.

## Phát hiện ban đầu

1. Frontend đang gọi cổng 8001, nơi một service cũ dùng provider mock. Phản hồi
   mẫu lặp lại nguyên câu hỏi nên trông máy móc; đây là lỗi cấu hình runtime,
   không liên quan dữ liệu train.
2. Sau khi nối đúng Gemini, lượt đầu hỏi thông tin thiếu khá tự nhiên. Lượt hai
   đôi lúc tự viết lịch trình dài dù người dùng chỉ vừa bổ sung thời lượng.
3. Gemini dùng Markdown nhưng `ChatBubble` chỉ render text thường, làm lộ dấu
   `**`, tiêu đề và bullet Markdown.
4. Guardrail cũ chặn cả gợi ý hợp lệ “đi phố cổ Hội An rồi về Đà Nẵng” vì thấy
   địa điểm thuộc một destination khác.
5. Cách xưng hô có thể đổi giữa `em`, `mình`, `anh/chị`; một lượt đôi lúc hỏi hai
   trường thông tin cùng lúc.

## Điều chỉnh

- Prompt buộc dùng `mình - bạn`, không chào lại mỗi lượt, trả lời 2-5 câu, hỏi
  đúng một thông tin còn thiếu và không tự lập lịch dài khi chưa được yêu cầu.
- Prompt không cho Markdown; backend vẫn chuẩn hóa heading, bold, code và bullet
  sang text thường để phòng provider không tuân thủ.
- Guardrail cho phép địa điểm ngoài destination chính khi phản hồi ghi rõ tên
  destination thật; địa điểm bị gán sai mà không nêu địa giới vẫn bị chặn.
- Thêm test cho chuyến đi lân cận hợp lệ, địa điểm sai tỉnh, Markdown và phản
  hồi lặp nguyên câu hỏi.

## Kết quả kiểm thử lại

Hội thoại hai lượt sau sửa:

1. Người dùng chỉ xác nhận muốn đi Đà Nẵng. AI tóm tắt ngắn ngữ cảnh hiện có và
   chỉ hỏi số ngày.
2. Người dùng trả lời 3 ngày 2 đêm, thích ăn uống và không muốn lịch dày. AI nhớ
   đúng các yêu cầu, xác nhận trong một câu rồi chỉ hỏi thời gian khởi hành.

Không còn Markdown thô, đổi đại từ, bài tư vấn dài ngoài yêu cầu hoặc false
positive về Hội An trong lần kiểm thử cuối. Guardrail an toàn/ngoài phạm vi vẫn
được kiểm tra bằng unit test.

## Dữ liệu v4

V3 chủ yếu gồm hội thoại một lượt nên chưa đủ để Qwen học phong cách trên. Bộ v4
bổ sung 240 hội thoại bốn lượt trên 20 điểm đến:

- 80 ca hỏi lần lượt các tham số còn thiếu.
- 60 ca người dùng sửa ý hoặc thu hẹp phạm vi.
- 40 ca trao đổi ngân sách.
- 40 ca câu hỏi nối tiếp về địa điểm/ẩm thực.
- 20 ca ngôn ngữ đời thường, giữ riêng làm test.

Split mới là 200 train, 20 validation và 20 test; không trùng prompt challenge.
Dataset đã sẵn sàng nhưng chưa train adapter v4. Gemini hiện tại đã cải thiện từ
prompt/backend; Qwen chỉ nhận được thay đổi phong cách sau khi fine-tune v4 và
vượt lại toàn bộ bài đánh giá v3.
