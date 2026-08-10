"""Catalog 34 đơn vị hành chính cấp tỉnh Việt Nam, hiệu lực từ 01/07/2025.

Mỗi mục giữ tên tỉnh/thành cũ trong aliases để người dùng vẫn tra cứu được sau
sắp xếp. Địa điểm là tập grounding đóng cho demo, không thay thế dữ liệu realtime.
"""

NATIONWIDE_RAW_PROVINCES: tuple[
    tuple[
        str,
        str,
        tuple[str, ...],
        tuple[str, str, str],
        tuple[str, str, str],
        str,
        tuple[str, ...],
    ],
    ...,
] = (
    ("01", "Hà Nội", ("Ha Noi",), ("hồ Hoàn Kiếm", "Văn Miếu", "phố cổ Hà Nội"), ("phở", "bún chả", "chả cá"), "Miền Bắc", ("văn hóa", "lịch sử", "đô thị", "ẩm thực")),
    ("04", "Cao Bằng", ("Cao Bang",), ("thác Bản Giốc", "động Ngườm Ngao", "hồ Thang Hen"), ("bánh cuốn", "vịt quay", "hạt dẻ Trùng Khánh"), "Miền Bắc", ("núi", "thiên nhiên", "văn hóa")),
    ("08", "Tuyên Quang", ("Tuyen Quang", "Hà Giang", "Ha Giang"), ("khu di tích Tân Trào", "đèo Mã Pì Lèng", "phố cổ Đồng Văn"), ("cháo ấu tẩu", "bánh tam giác mạch", "cam sành"), "Miền Bắc", ("núi", "lịch sử", "thiên nhiên", "văn hóa")),
    ("11", "Điện Biên", ("Dien Bien",), ("đồi A1", "hầm Đờ Cát", "hồ Pá Khoang"), ("xôi nếp nương", "pa pỉnh tộp", "gà nướng mắc khén"), "Miền Bắc", ("lịch sử", "núi", "văn hóa")),
    ("12", "Lai Châu", ("Lai Chau",), ("đèo Ô Quy Hồ", "cao nguyên Sìn Hồ", "động Pu Sam Cáp"), ("lợn cắp nách", "cá bống vùi tro", "xôi tím"), "Miền Bắc", ("núi", "thiên nhiên", "văn hóa")),
    ("14", "Sơn La", ("Son La",), ("cao nguyên Mộc Châu", "Tà Xùa", "nhà tù Sơn La"), ("bê chao", "cá suối", "sữa Mộc Châu"), "Miền Bắc", ("núi", "thiên nhiên", "văn hóa")),
    ("15", "Lào Cai", ("Lao Cai", "Yên Bái", "Yen Bai", "Sa Pa", "Sapa"), ("Fansipan", "thung lũng Mường Hoa", "Mù Cang Chải"), ("thắng cố", "cá hồi", "xôi ngũ sắc"), "Miền Bắc", ("núi", "thiên nhiên", "văn hóa")),
    ("19", "Thái Nguyên", ("Thai Nguyen", "Bắc Kạn", "Bac Kan"), ("hồ Núi Cốc", "ATK Định Hóa", "hồ Ba Bể"), ("chè Tân Cương", "bánh chưng Bờ Đậu", "miến dong"), "Miền Bắc", ("thiên nhiên", "lịch sử", "văn hóa")),
    ("20", "Lạng Sơn", ("Lang Son",), ("đỉnh Mẫu Sơn", "động Tam Thanh", "ải Chi Lăng"), ("vịt quay", "khâu nhục", "phở chua"), "Miền Bắc", ("núi", "lịch sử", "ẩm thực")),
    ("22", "Quảng Ninh", ("Quang Ninh", "Hạ Long", "Ha Long"), ("vịnh Hạ Long", "Yên Tử", "đảo Cô Tô"), ("chả mực", "sá sùng", "bún bề bề"), "Miền Bắc", ("biển", "đảo", "thiên nhiên", "tâm linh")),
    ("24", "Bắc Ninh", ("Bac Ninh", "Bắc Giang", "Bac Giang"), ("chùa Dâu", "đền Đô", "chùa Vĩnh Nghiêm"), ("bánh phu thê", "nem Bùi", "mỳ Chũ"), "Miền Bắc", ("văn hóa", "lịch sử", "tâm linh")),
    ("25", "Phú Thọ", ("Phu Tho", "Vĩnh Phúc", "Vinh Phuc", "Hòa Bình", "Hoa Binh"), ("đền Hùng", "Tam Đảo", "hồ Hòa Bình"), ("thịt chua", "cá thính", "cơm lam"), "Miền Bắc", ("lịch sử", "núi", "văn hóa", "thiên nhiên")),
    ("31", "Hải Phòng", ("Hai Phong", "Hải Dương", "Hai Duong"), ("quần đảo Cát Bà", "bãi biển Đồ Sơn", "Côn Sơn - Kiếp Bạc"), ("bánh đa cua", "nem cua bể", "bánh đậu xanh"), "Miền Bắc", ("biển", "đảo", "lịch sử", "ẩm thực")),
    ("33", "Hưng Yên", ("Hung Yen", "Thái Bình", "Thai Binh"), ("phố Hiến", "chùa Keo", "biển Cồn Vành"), ("nhãn lồng", "bánh cáy", "canh cá Quỳnh Côi"), "Miền Bắc", ("văn hóa", "lịch sử", "biển")),
    ("37", "Ninh Bình", ("Ninh Binh", "Hà Nam", "Ha Nam", "Nam Định", "Nam Dinh"), ("Tràng An", "chùa Tam Chúc", "Phủ Dầy"), ("cơm cháy", "dê núi", "phở bò Nam Định"), "Miền Bắc", ("thiên nhiên", "văn hóa", "lịch sử", "tâm linh")),
    ("38", "Thanh Hóa", ("Thanh Hoa",), ("biển Sầm Sơn", "Thành Nhà Hồ", "Pù Luông"), ("nem chua", "chả tôm", "bánh răng bừa"), "Miền Trung", ("biển", "lịch sử", "thiên nhiên")),
    ("40", "Nghệ An", ("Nghe An",), ("quê Bác ở Kim Liên", "biển Cửa Lò", "Vườn quốc gia Pù Mát"), ("cháo lươn", "nhút Thanh Chương", "bánh mướt"), "Miền Trung", ("lịch sử", "biển", "thiên nhiên")),
    ("42", "Hà Tĩnh", ("Ha Tinh",), ("Ngã ba Đồng Lộc", "biển Thiên Cầm", "chùa Hương Tích"), ("kẹo cu đơ", "ram bánh mướt", "gỏi cá đục"), "Miền Trung", ("lịch sử", "biển", "tâm linh")),
    ("44", "Quảng Trị", ("Quang Tri", "Quảng Bình", "Quang Binh"), ("Thành cổ Quảng Trị", "địa đạo Vịnh Mốc", "Phong Nha"), ("cháo canh", "bánh bột lọc", "bún hến"), "Miền Trung", ("lịch sử", "hang động", "biển", "thiên nhiên")),
    ("46", "Huế", ("Thừa Thiên Huế", "Thua Thien Hue", "Hue"), ("Đại Nội", "chùa Thiên Mụ", "lăng Khải Định"), ("bún bò Huế", "cơm hến", "bánh bèo"), "Miền Trung", ("văn hóa", "lịch sử", "ẩm thực")),
    ("48", "Đà Nẵng", ("Da Nang", "Quảng Nam", "Quang Nam", "Hội An", "Hoi An"), ("bán đảo Sơn Trà", "phố cổ Hội An", "thánh địa Mỹ Sơn"), ("mì Quảng", "cao lầu", "bánh tráng cuốn thịt heo"), "Miền Trung", ("biển", "văn hóa", "lịch sử", "đô thị")),
    ("51", "Quảng Ngãi", ("Quang Ngai", "Kon Tum"), ("đảo Lý Sơn", "Măng Đen", "chứng tích Sơn Mỹ"), ("don", "kẹo gương", "gỏi tỏi Lý Sơn"), "Miền Trung", ("biển", "đảo", "núi", "lịch sử")),
    ("52", "Gia Lai", ("Bình Định", "Binh Dinh"), ("Biển Hồ", "Kỳ Co", "Eo Gió"), ("phở khô", "bánh xèo tôm nhảy", "tré"), "Tây Nguyên", ("núi", "biển", "văn hóa", "ẩm thực")),
    ("56", "Khánh Hòa", ("Khanh Hoa", "Ninh Thuận", "Ninh Thuan", "Nha Trang"), ("tháp Bà Ponagar", "vịnh Vĩnh Hy", "Vườn quốc gia Núi Chúa"), ("bún cá", "nem nướng", "nho Ninh Thuận"), "Miền Trung", ("biển", "đảo", "văn hóa", "thiên nhiên")),
    ("66", "Đắk Lắk", ("Dak Lak", "Đắc Lắc", "Phú Yên", "Phu Yen", "Buôn Ma Thuột", "Buon Ma Thuot"), ("Bảo tàng Thế giới Cà phê", "Gành Đá Đĩa", "Bãi Xép"), ("bún đỏ", "mắt cá ngừ đại dương", "bánh hỏi lòng heo"), "Tây Nguyên", ("văn hóa", "biển", "thiên nhiên", "ẩm thực")),
    ("68", "Lâm Đồng", ("Lam Dong", "Đắk Nông", "Dak Nong", "Bình Thuận", "Binh Thuan", "Đà Lạt", "Da Lat"), ("hồ Xuân Hương", "Tà Đùng", "Mũi Né"), ("bánh căn", "lẩu gà lá é", "thanh long"), "Tây Nguyên", ("núi", "biển", "thiên nhiên", "nghỉ dưỡng")),
    ("75", "Đồng Nai", ("Dong Nai", "Bình Phước", "Binh Phuoc"), ("Vườn quốc gia Cát Tiên", "hồ Trị An", "núi Bà Rá"), ("gỏi cá Biên Hòa", "hạt điều", "cơm lam"), "Miền Nam", ("thiên nhiên", "sinh thái", "văn hóa")),
    ("79", "TP. Hồ Chí Minh", ("Thành phố Hồ Chí Minh", "Hồ Chí Minh", "TP.HCM", "TP HCM", "Sài Gòn", "Sai Gon", "Bình Dương", "Binh Duong", "Bà Rịa - Vũng Tàu", "Ba Ria Vung Tau", "Vũng Tàu", "Vung Tau"), ("Dinh Độc Lập", "Bãi Sau Vũng Tàu", "Côn Đảo"), ("cơm tấm", "bánh khọt", "lẩu cá đuối"), "Miền Nam", ("đô thị", "biển", "lịch sử", "ẩm thực")),
    ("80", "Tây Ninh", ("Tay Ninh", "Long An"), ("núi Bà Đen", "Tòa Thánh Tây Ninh", "làng nổi Tân Lập"), ("bánh canh Trảng Bàng", "bò tơ", "lạp xưởng tươi"), "Miền Nam", ("núi", "văn hóa", "tâm linh", "sinh thái")),
    ("82", "Đồng Tháp", ("Dong Thap", "Tiền Giang", "Tien Giang"), ("Vườn quốc gia Tràm Chim", "làng hoa Sa Đéc", "chợ nổi Cái Bè"), ("hủ tiếu Mỹ Tho", "nem Lai Vung", "cá lóc nướng trui"), "Miền Nam", ("sông nước", "sinh thái", "văn hóa", "ẩm thực")),
    ("86", "Vĩnh Long", ("Vinh Long", "Bến Tre", "Ben Tre", "Trà Vinh", "Tra Vinh"), ("cù lao An Bình", "cồn Phụng", "Ao Bà Om"), ("cá tai tượng chiên xù", "kẹo dừa", "bún nước lèo"), "Miền Nam", ("sông nước", "văn hóa", "ẩm thực")),
    ("91", "An Giang", ("Kien Giang", "Kiên Giang", "Châu Đốc", "Chau Doc", "Phú Quốc", "Phu Quoc"), ("miếu Bà Chúa Xứ", "đảo Phú Quốc", "Hà Tiên"), ("bún cá Châu Đốc", "gỏi cá trích", "bún quậy"), "Miền Nam", ("biển", "đảo", "sông nước", "tâm linh")),
    ("92", "Cần Thơ", ("Can Tho", "Sóc Trăng", "Soc Trang", "Hậu Giang", "Hau Giang"), ("chợ nổi Cái Răng", "chùa Dơi", "khu bảo tồn Lung Ngọc Hoàng"), ("bánh cống", "bún nước lèo", "lẩu mắm"), "Miền Nam", ("sông nước", "văn hóa", "sinh thái", "ẩm thực")),
    ("96", "Cà Mau", ("Ca Mau", "Bạc Liêu", "Bac Lieu"), ("Mũi Cà Mau", "nhà Công tử Bạc Liêu", "cánh đồng điện gió Bạc Liêu"), ("cua Cà Mau", "bún bò cay", "ba khía"), "Miền Nam", ("biển", "sinh thái", "văn hóa", "ẩm thực")),
)

# Phần mở rộng chỉ dùng ở runtime. Bộ ba trong NATIONWIDE_RAW_PROVINCES được
# giữ nguyên để tái lập chính xác dữ liệu train/evaluation v11-v12 đã audit.
RUNTIME_TOURISM_PLACE_EXPANSIONS: dict[str, tuple[str, ...]] = {
    "Hà Nội": ("Lăng Chủ tịch Hồ Chí Minh", "Nhà tù Hỏa Lò", "Hồ Tây"),
    "Lào Cai": ("bản Cát Cát", "đèo Ô Quy Hồ", "nhà thờ đá Sa Pa"),
    "Quảng Ninh": ("Bảo tàng Quảng Ninh", "Bãi Cháy", "đảo Quan Lạn"),
    "Hải Phòng": ("vịnh Lan Hạ", "Vườn quốc gia Cát Bà", "đảo Hòn Dấu"),
    "Ninh Bình": ("Hang Múa", "cố đô Hoa Lư", "Tam Cốc - Bích Động"),
    "Huế": ("lăng Minh Mạng", "lăng Tự Đức", "cầu Trường Tiền"),
    "Đà Nẵng": ("Ngũ Hành Sơn", "bãi biển Mỹ Khê", "Cầu Rồng"),
    "Khánh Hòa": ("bãi biển Nha Trang", "Hòn Chồng", "vịnh Nha Trang"),
    "Lâm Đồng": ("núi Langbiang", "thác Datanla", "vườn hoa Đà Lạt"),
    "TP. Hồ Chí Minh": ("chợ Bến Thành", "Bưu điện Trung tâm", "địa đạo Củ Chi"),
    "An Giang": ("Bãi Sao", "Dinh Cậu", "rừng tràm Trà Sư"),
    "Cần Thơ": ("bến Ninh Kiều", "nhà cổ Bình Thủy", "thiền viện Trúc Lâm Phương Nam"),
}
