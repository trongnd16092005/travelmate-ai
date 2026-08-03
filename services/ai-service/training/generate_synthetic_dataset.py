import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

SYSTEM_MESSAGE = (
    "Bạn là TravelMate, trợ lý chuyên tư vấn du lịch bằng tiếng Việt. "
    "Hỏi lại khi thiếu ngày đi, số khách hoặc ngân sách; không bịa giá, rating, "
    "giờ mở cửa hay tình trạng phòng; không tự thực hiện giao dịch; bắt đầu bằng "
    "[OUT_OF_SCOPE] nếu câu hỏi không liên quan đến du lịch."
)

DESTINATIONS: dict[str, dict[str, tuple[str, str, str]]] = {
    "Đà Nẵng": {
        "places": ("bán đảo Sơn Trà", "Ngũ Hành Sơn", "bãi biển Mỹ Khê"),
        "foods": ("mì Quảng", "bánh tráng cuốn thịt heo", "bún chả cá"),
    },
    "Huế": {
        "places": ("Đại Nội", "chùa Thiên Mụ", "lăng Khải Định"),
        "foods": ("bún bò Huế", "cơm hến", "bánh bèo"),
    },
    "Hội An": {
        "places": ("Chùa Cầu", "phố cổ", "làng gốm Thanh Hà"),
        "foods": ("cao lầu", "cơm gà", "bánh mì Hội An"),
    },
    "Đà Lạt": {
        "places": ("hồ Xuân Hương", "vườn hoa thành phố", "núi Langbiang"),
        "foods": ("bánh căn", "lẩu gà lá é", "sữa đậu nành"),
    },
    "Nha Trang": {
        "places": ("tháp Bà Ponagar", "hòn Chồng", "bãi biển Nha Trang"),
        "foods": ("bún cá", "nem nướng", "bánh căn hải sản"),
    },
    "Phú Quốc": {
        "places": ("Bãi Sao", "Dinh Cậu", "vườn quốc gia Phú Quốc"),
        "foods": ("gỏi cá trích", "bún quậy", "hải sản"),
    },
    "Hà Nội": {
        "places": ("hồ Hoàn Kiếm", "Văn Miếu", "phố cổ Hà Nội"),
        "foods": ("phở", "bún chả", "chả cá"),
    },
    "TP. Hồ Chí Minh": {
        "places": ("Dinh Độc Lập", "Bưu điện Trung tâm", "chợ Bến Thành"),
        "foods": ("cơm tấm", "hủ tiếu", "bánh mì"),
    },
    "Sa Pa": {
        "places": ("bản Cát Cát", "Fansipan", "thung lũng Mường Hoa"),
        "foods": ("thắng cố", "cá hồi", "lợn cắp nách"),
    },
    "Ninh Bình": {
        "places": ("Tràng An", "Hang Múa", "cố đô Hoa Lư"),
        "foods": ("cơm cháy", "dê núi", "miến lươn"),
    },
    "Hạ Long": {
        "places": ("vịnh Hạ Long", "Bảo tàng Quảng Ninh", "Bãi Cháy"),
        "foods": ("chả mực", "bún bề bề", "sam biển"),
    },
    "Quy Nhơn": {
        "places": ("Kỳ Co", "Eo Gió", "Ghềnh Ráng"),
        "foods": ("bánh xèo tôm nhảy", "bún chả cá", "tré"),
    },
    "Vũng Tàu": {
        "places": ("Bãi Sau", "tượng Chúa Kitô", "mũi Nghinh Phong"),
        "foods": ("bánh khọt", "lẩu cá đuối", "hải sản"),
    },
    "Cần Thơ": {
        "places": ("chợ nổi Cái Răng", "nhà cổ Bình Thủy", "bến Ninh Kiều"),
        "foods": ("bánh cống", "lẩu mắm", "nem nướng Cái Răng"),
    },
    "Mũi Né": {
        "places": ("đồi cát", "Suối Tiên", "làng chài Mũi Né"),
        "foods": ("bánh căn", "gỏi cá mai", "hải sản"),
    },
    "Hà Giang": {
        "places": ("đèo Mã Pì Lèng", "phố cổ Đồng Văn", "cột cờ Lũng Cú"),
        "foods": ("cháo ấu tẩu", "bánh tam giác mạch", "thắng dền"),
    },
    "Cao Bằng": {
        "places": ("thác Bản Giốc", "động Ngườm Ngao", "hồ Thang Hen"),
        "foods": ("bánh cuốn", "vịt quay", "hạt dẻ Trùng Khánh"),
    },
    "Buôn Ma Thuột": {
        "places": ("Bảo tàng Thế giới Cà phê", "Buôn Đôn", "thác Dray Nur"),
        "foods": ("bún đỏ", "cơm lam", "gà nướng"),
    },
    "Tây Ninh": {
        "places": ("núi Bà Đen", "Tòa Thánh Tây Ninh", "hồ Dầu Tiếng"),
        "foods": ("bánh canh Trảng Bàng", "bò tơ", "bánh tráng phơi sương"),
    },
    "Quảng Bình": {
        "places": ("Phong Nha", "động Thiên Đường", "suối Nước Moọc"),
        "foods": ("cháo canh", "bánh bột lọc", "khoai deo"),
    },
}


def format_vnd(value: int) -> str:
    return f"{value:,}".replace(",", ".") + " VND"


def make_record(
    record_id: str,
    category: str,
    user: str,
    assistant: str,
    behaviors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": record_id,
        "category": category,
        "expectedBehaviors": behaviors or [],
        "reviewStatus": "synthetic_draft_v1",
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
    }


def generate_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()

    def add(
        category: str,
        user: str,
        assistant: str,
        behaviors: list[str] | None = None,
    ) -> None:
        counters[category] += 1
        record_id = f"{category}-{counters[category]:04d}"
        records.append(make_record(record_id, category, user, assistant, behaviors))

    groups = (
        "một người",
        "hai người",
        "gia đình bốn người",
        "nhóm năm người",
        "gia đình có trẻ nhỏ",
    )
    for destination, details in DESTINATIONS.items():
        place_1, place_2, place_3 = details["places"]
        for days in (2, 3, 4):
            for group in groups:
                user = f"Lập lịch trình {destination} {days} ngày cho {group}."
                day_plans = [f"ngày 1 tham quan {place_1}", f"ngày 2 đi {place_2}"]
                if days >= 3:
                    day_plans.append(f"ngày 3 khám phá {place_3}")
                if days == 4:
                    day_plans.append("ngày 4 dành cho trải nghiệm tự chọn và nghỉ ngơi")
                assistant = (
                    f"Gợi ý cho {group}: {'; '.join(day_plans)}. Mỗi ngày nên chừa thời gian nghỉ "
                    "và di chuyển. Bạn đi ngày nào và dự kiến tổng ngân sách bao nhiêu?"
                )
                add("itinerary", user, assistant, ["ask_clarification"])

    for destination in DESTINATIONS:
        for days in (2, 3, 4):
            for budget_million in (3, 5, 8, 12):
                total = budget_million * 1_000_000
                user = (
                    f"Hai người có {budget_million} triệu để đi {destination} {days} ngày, "
                    "nên chia ngân sách thế nào?"
                )
                assistant = (
                    f"Với tổng {format_vnd(total)}, bạn có thể dự kiến: lưu trú khoảng "
                    f"{format_vnd(total * 35 // 100)}, ăn uống {format_vnd(total * 25 // 100)}, "
                    f"di chuyển {format_vnd(total * 25 // 100)} và tham quan/dự phòng "
                    f"{format_vnd(total * 15 // 100)}. Đây là khung tham khảo; cần kiểm tra giá "
                    "thực tế và xác định ngân sách đã gồm chi phí đến điểm du lịch hay chưa."
                )
                add("budget", user, assistant, ["realtime_limit"])

    stay_preferences = (
        "gần trung tâm",
        "ở khu vực yên tĩnh",
        "gần điểm tham quan",
        "thuận tiện đi phương tiện công cộng",
        "phù hợp gia đình có trẻ nhỏ",
    )
    for destination in DESTINATIONS:
        for preference in stay_preferences:
            for nightly_budget in (600_000, 1_200_000):
                user = (
                    f"Tìm chỗ ở tại {destination} {preference}, giá dưới "
                    f"{format_vnd(nightly_budget)} mỗi đêm."
                )
                assistant = (
                    f"Mình sẽ ưu tiên chỗ ở tại {destination} {preference} trong mức "
                    f"{format_vnd(nightly_budget)} mỗi đêm. Bạn cho biết ngày nhận phòng, ngày trả "
                    "phòng, số khách và số phòng nhé? Giá cùng tình trạng phòng cần được xác nhận "
                    "từ nguồn đặt phòng hiện tại."
                )
                add(
                    "accommodation",
                    user,
                    assistant,
                    ["ask_clarification", "realtime_limit"],
                )

    food_preferences = ("ưu tiên món bình dân", "không ăn cay", "muốn thử đặc sản địa phương")
    for destination, details in DESTINATIONS.items():
        food_1, food_2, food_3 = details["foods"]
        for preference in food_preferences:
            for meal_budget in (150_000, 300_000):
                user = (
                    f"Gợi ý ăn uống ở {destination}, {preference}, khoảng "
                    f"{format_vnd(meal_budget)} một người mỗi ngày."
                )
                assistant = (
                    f"Bạn có thể tham khảo {food_1}, {food_2} và {food_3}. Với yêu cầu {preference}, "
                    "nên hỏi rõ thành phần món và báo dị ứng nếu có. Giá, địa chỉ và giờ mở cửa "
                    "cần kiểm tra trên nguồn hiện tại trước khi đến."
                )
                add("food", user, assistant, ["realtime_limit"])

    activities = ("đi bộ đường dài", "tự đi xe máy", "đưa trẻ nhỏ đi tham quan")
    conditions = ("mùa mưa", "thời tiết nắng nóng")
    for destination in DESTINATIONS:
        for activity in activities:
            for condition in conditions:
                user = f"Đi {destination} {condition} và {activity} thì cần lưu ý gì?"
                assistant = (
                    f"Khi {activity} tại {destination} vào {condition}, bạn nên kiểm tra dự báo và "
                    "cảnh báo địa phương sát ngày đi, chuẩn bị nước, thuốc cá nhân, trang phục phù "
                    "hợp và một phương án dự phòng. Không tiếp tục hoạt động nếu điều kiện không an "
                    "toàn hoặc có khuyến cáo hạn chế di chuyển."
                )
                add("safety_weather", user, assistant, ["safety_caveat"])

    for destination in DESTINATIONS:
        realtime_cases = (
            (
                f"Vé máy bay đến {destination} ngày mai giá bao nhiêu?",
                (
                    "Giá vé thay đổi theo thời gian thực nên mình cần tra cứu hãng bay hoặc nền "
                    "tảng đặt vé mới xác nhận được. Bạn khởi hành từ đâu, muốn bay khung giờ nào "
                    "và có hành lý ký gửi không?"
                ),
            ),
            (
                f"Khách sạn nào ở {destination} còn phòng tối nay?",
                (
                    "Tình trạng phòng là dữ liệu thời gian thực nên mình chưa thể tự xác nhận. "
                    "Bạn cho biết số khách, số phòng và ngân sách tối đa để tra cứu nguồn đặt "
                    "phòng phù hợp?"
                ),
            ),
            (
                f"Quán ăn được chấm điểm cao nhất ở {destination} hiện nay là quán nào?",
                (
                    "Xếp hạng và đánh giá có thể thay đổi, vì vậy cần kiểm tra nguồn hiện tại "
                    "thay vì tự đoán. Bạn muốn tìm món gì, ở khu vực nào và mức giá khoảng bao "
                    "nhiêu?"
                ),
            ),
            (
                f"Điểm tham quan tại {destination} hôm nay mở cửa đến mấy giờ?",
                (
                    "Giờ mở cửa có thể thay đổi theo ngày hoặc sự kiện. Mình cần tên địa điểm cụ "
                    "thể và nguồn thông tin hiện tại mới xác nhận chính xác được. Bạn đang hỏi "
                    "địa điểm nào?"
                ),
            ),
        )
        for user, assistant in realtime_cases:
            add("realtime_limit", user, assistant, ["realtime_limit", "ask_clarification"])

    out_of_scope_tasks = (
        "viết chương trình sắp xếp mảng Java",
        "dự đoán kết quả bóng đá tối nay",
        "tư vấn nên mua cổ phiếu nào",
        "giải phương trình bậc hai",
    )
    for destination in DESTINATIONS:
        for task in out_of_scope_tasks:
            user = f"Tôi đang chuẩn bị đi {destination}, nhưng trước tiên hãy {task}."
            assistant = (
                "[OUT_OF_SCOPE] Xin lỗi, mình chỉ hỗ trợ các nội dung liên quan đến du lịch. "
                f"Mình có thể giúp bạn lập lịch trình, dự toán chi phí hoặc chuẩn bị chuyến đi "
                f"{destination}."
            )
            add("out_of_scope", user, assistant, ["out_of_scope_marker"])

    action_requests = (
        "hủy toàn bộ lịch trình cũ",
        "thanh toán khách sạn ngay",
        "đặt vé và xác nhận giao dịch giúp tôi",
    )
    for destination in DESTINATIONS:
        for action in action_requests:
            user = f"Tôi đi {destination}; hãy {action}."
            assistant = (
                "Mình không tự thực hiện thao tác xóa, đặt chỗ hoặc thanh toán. Mình có thể chuẩn "
                "bị phương án và liên kết phù hợp, sau đó bạn cần xem lại và xác nhận trong ứng dụng."
            )
            add("action_boundary", user, assistant, ["no_transaction"])

    assert len(records) == 1200
    for index, record in enumerate(records):
        record["reviewBatch"] = index % 12 + 1
    return records


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset nháp TravelMate có thể tái lập")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = generate_records()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")

    categories = Counter(record["category"] for record in records)
    print(f"Đã tạo {len(records)} hội thoại nháp tại {args.output}")
    for category, count in sorted(categories.items()):
        print(f"- {category}: {count}")
    print("Cần duyệt thủ công reviewStatus trước khi train chính thức.")


if __name__ == "__main__":
    main()
