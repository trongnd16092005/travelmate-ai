ĐÂY LÀ AI DỰ KIẾN-Mô tả chức năng
Người dùng nhập yêu cầu bằng ngôn ngữ tự nhiên (ví dụ: "tìm homestay Đà Nẵng giá dưới 500k, gần biển, yên tĩnh"), AI sẽ phân tích yêu cầu thành các tiêu chí có cấu trúc, sau đó tìm kiếm và tổng hợp kết quả từ Booking.com Affiliate để trả về danh sách gợi ý kèm lý do phù hợp. Đây là lớp "AI Search Layer" nằm giữa người dùng và nguồn dữ liệu OTA (Online Travel Agency), giúp thay thế việc người dùng phải tự lọc thủ công trên Booking.com.[booking]
Luồng xử lý (Workflow)
Người dùng nhập yêu cầu tự nhiên qua chatbot hoặc form tìm kiếm trong app React Native.[ppl-ai-file-upload.s3.amazonaws]
AI Service (FastAPI) dùng LLM để trích xuất tiêu chí có cấu trúc từ câu nói tự nhiên (Prompt Engineering/Function Calling).
Backend gọi Booking.com Affiliate link/API (qua Awin hoặc CJ network) với các tham số đã trích xuất để lấy danh sách chỗ nghỉ phù hợp.[booking]
AI tổng hợp lại kết quả (giá, vị trí, rating) thành mô tả tự nhiên, xếp hạng theo mức độ phù hợp với yêu cầu người dùng.
Trả kết quả về app kèm deep link đặt phòng qua Booking.com (nguồn thu affiliate).[ecomobi]
Tiêu chí trích xuất từ yêu cầu người dùng
Tiêu chí
Ví dụ giá trị
Cách AI xử lý
Khoảng giá
"dưới 500k/đêm", "tầm 1 triệu"
Parse thành price_min, price_max
Vị trí ưu tiên
"trung tâm", "gần biển", "yên tĩnh"
Map sang khu vực/tọa độ + tag loại địa điểm
Loại chỗ nghỉ
Homestay, khách sạn, villa
Map sang property_type filter
Thời gian
Ngày check-in/check-out
Parse ngày từ câu nói ("cuối tuần này")
Số người/phòng
"2 người 1 phòng"
Map sang adults, rooms
Tiện ích mong muốn
"có hồ bơi", "gần chợ đêm"
Đối chiếu với amenities trong dữ liệu trả về

Kiến trúc kỹ thuật đề xuất
Input layer: Chatbot/form trong React Native gửi câu yêu cầu thô lên AI Service.[ppl-ai-file-upload.s3.amazonaws]
NLU layer (FastAPI + LLM): Trích xuất entity (giá, vị trí, loại phòng) bằng prompt có cấu trúc JSON output.
Data layer: Gọi Booking.com Affiliate qua Awin/CJ network để lấy danh sách chỗ nghỉ khớp tiêu chí; lưu ý Booking.com cấm dùng dữ liệu để so sánh giá đa nền tảng, nên chỉ nên hiển thị nguồn Booking.com.[booking]
Ranking layer: AI xếp hạng lại kết quả theo độ phù hợp (không chỉ theo giá/rating mặc định của Booking).
Output layer: Trả JSON gồm tên chỗ nghỉ, giá, ảnh, rating, lý do gợi ý, và deep link đặt phòng (tracking link affiliate).[ecomobi]
Giới hạn và rủi ro cần ghi trong báo cáo
Booking.com Affiliate chỉ cho hiển thị dữ liệu để dẫn link đặt phòng, không được dùng để xây dựng công cụ so sánh giá độc lập giữa nhiều OTA khác nhau.[legacy.developers.booking]
Cần đăng ký qua mạng affiliate (Awin cho châu Á-Thái Bình Dương) và chờ duyệt trước khi có tracking link thật, nên trong giai đoạn demo có thể dùng dữ liệu mẫu (mock data).[youtube][cj]
Độ chính xác của bước trích xuất tiêu chí ("yên tĩnh", "trung tâm") phụ thuộc vào chất lượng prompt và có thể cần kết hợp thêm dữ liệu vị trí từ Google Places để xác định "gần biển"/"trung tâm" chính xác hơn là chỉ dựa vào text mô tả của Booking.


