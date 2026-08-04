import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate

SYSTEM_PROMPT = (
    "Bạn là TravelMate, trợ lý chuyên tư vấn du lịch bằng tiếng Việt. "
    "Hỏi lại khi thiếu điểm đến, thời lượng hoặc ngày đi, số khách hay ngân sách; "
    "không bịa địa điểm, giá, rating, giờ mở cửa, tình trạng phòng hoặc dữ liệu thời gian thực; "
    "không tự thực hiện giao dịch; cảnh báo rõ ràng khi có rủi ro sức khỏe hoặc an toàn; "
    "bắt đầu bằng [OUT_OF_SCOPE] nếu câu hỏi không liên quan đến du lịch."
)

EXPECTED_COUNTS = {
    "action_boundary_v2": 10,
    "clarification_v2": 30,
    "fact_check_v2": 20,
    "infeasible_budget_v2": 20,
    "out_of_scope_v2": 20,
    "realtime_limit_v2": 30,
    "safety_v2": 30,
    "slang_budget_v2": 20,
}


def make_record(
    index: int,
    category: str,
    expected_behaviors: list[str],
    user: str,
    assistant: str,
    approved_at: str,
) -> dict[str, Any]:
    return {
        "id": f"reinforcement-v2-{index:04d}",
        "category": category,
        "expectedBehaviors": expected_behaviors,
        "reviewStatus": "approved",
        "reviewMethod": "curated_rule_audit_v2",
        "approvedAt": approved_at,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
            {"role": "assistant", "content": assistant},
        ],
    }


def build_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    def add(
        category: str,
        behaviors: list[str],
        user: str,
        assistant: str,
    ) -> None:
        records.append(
            make_record(len(records) + 1, category, behaviors, user, assistant, approved_at)
        )

    origins = [
        "Hà Nội",
        "TP.HCM",
        "Đà Nẵng",
        "Huế",
        "Cần Thơ",
        "Hải Phòng",
        "Nha Trang",
        "Vinh",
        "Quy Nhơn",
        "Đà Lạt",
    ]
    for origin in origins:
        add(
            "clarification_v2",
            ["ask_clarification"],
            f"Xuất phát từ {origin}, ba ngày, hai người và khoảng 7 triệu.",
            f"Mình đã có nơi xuất phát là {origin}, thời lượng ba ngày, hai khách và ngân sách "
            "khoảng 7.000.000 VND, nhưng chưa có điểm đến. Bạn muốn đi tỉnh hoặc thành phố nào, "
            "và ngày khởi hành dự kiến là khi nào?",
        )

    destinations = [
        "Đà Nẵng",
        "Huế",
        "Đà Lạt",
        "Phú Quốc",
        "Hạ Long",
        "Ninh Bình",
        "Sa Pa",
        "Hà Giang",
        "Quy Nhơn",
        "Hội An",
    ]
    for destination in destinations:
        add(
            "clarification_v2",
            ["ask_clarification"],
            f"Bốn người có 9 triệu, lên lịch đi {destination} giúp mình.",
            f"Mình đã có điểm đến {destination}, bốn khách và tổng ngân sách 9.000.000 VND. "
            "Bạn muốn đi mấy ngày, ngày khởi hành nào và ngân sách này đã gồm chi phí di chuyển "
            "đến điểm đến chưa?",
        )

    vague_requests = [
        "Muốn tìm chỗ mát mẻ ở miền Trung để nghỉ.",
        "Cho tôi chuyến biển nhẹ nhàng với.",
        "Cuối tháng muốn đưa gia đình đi đổi gió.",
        "Tôi muốn lên núi vài hôm cho yên tĩnh.",
        "Gợi ý một nơi không quá đông để nghỉ dưỡng.",
        "Muốn đi đâu đó gần thiên nhiên vào cuối tuần.",
        "Tôi cần chuyến ăn ngon và đi bộ ít.",
        "Nhóm bạn muốn đi chơi nhưng chưa chốt gì cả.",
        "Tư vấn giúp một chuyến tiết kiệm ở miền Bắc.",
        "Mình muốn đi tránh nóng vài ngày.",
    ]
    for request in vague_requests:
        add(
            "clarification_v2",
            ["ask_clarification"],
            request,
            "Mình có thể gợi ý, nhưng chưa nên chốt địa điểm khi thiếu dữ liệu. Bạn xuất phát từ "
            "đâu, đi bao nhiêu ngày, có mấy người, tổng ngân sách khoảng bao nhiêu và ưu tiên "
            "quan trọng nhất là khí hậu, nghỉ dưỡng, ăn uống hay tham quan?",
        )

    slang_budgets = [
        ("3 củ", 3_000_000),
        ("4 củ rưỡi", 4_500_000),
        ("5 củ", 5_000_000),
        ("6 chai", 6_000_000),
        ("7 triệu bạc", 7_000_000),
    ]
    slang_destinations = ["Đà Nẵng", "Huế", "Đà Lạt", "Nha Trang"]
    for budget_text, budget_value in slang_budgets:
        for destination in slang_destinations:
            add(
                "slang_budget_v2",
                ["ask_clarification"],
                f"Có {budget_text}, muốn đi {destination} đổi gió thì lên kèo sao?",
                f"Mình hiểu “{budget_text}” là tổng ngân sách khoảng "
                f"{budget_value:,.0f} VND, không phải số người. Để lên lịch {destination} phù hợp, "
                "bạn cho mình biết nơi xuất phát, số khách, số ngày và ngày đi dự kiến nhé?",
            )

    infeasible_cases = [
        ("Phú Quốc", "2 triệu", "hai người", "năm ngày", "nghỉ dưỡng cao cấp"),
        ("Đà Lạt", "1 triệu", "bốn người", "ba ngày", "khách sạn trung tâm"),
        ("Sa Pa", "1,5 triệu", "hai người", "bốn ngày", "phòng có view núi"),
        ("Hạ Long", "2 triệu", "gia đình năm người", "ba ngày", "du thuyền sang trọng"),
        ("Côn Đảo", "3 triệu", "hai người", "bốn ngày", "resort sát biển"),
    ]
    budget_prefixes = ["Tôi chỉ có", "Ngân sách tổng là", "Cố định đúng", "Không được vượt quá"]
    for destination, budget, travelers, duration, expectation in infeasible_cases:
        for prefix in budget_prefixes:
            add(
                "infeasible_budget_v2",
                ["ask_clarification", "realtime_limit"],
                f"{prefix} {budget} cho {travelers} đi {destination} {duration}, nhưng muốn {expectation}.",
                f"Mức {budget} cho {travelers} tại {destination} trong {duration} có thể không phù hợp "
                f"với yêu cầu {expectation}. Mình chưa thể bảo đảm giá nếu chưa tra cứu nguồn hiện tại. "
                "Bạn muốn tăng ngân sách, giảm số ngày hay chuyển sang tiêu chuẩn tiết kiệm hơn?",
            )

    realtime_items = [
        ("khách sạn sát biển", "tình trạng phòng và giá"),
        ("vé máy bay rẻ nhất", "giá vé và chỗ còn lại"),
        ("giờ đóng cửa khu vui chơi", "giờ hoạt động"),
        ("vé tham quan còn bao nhiêu", "giá và tình trạng vé"),
        ("chuyến xe khách cuối ngày", "lịch xe"),
        ("thời tiết sáng mai", "dự báo thời tiết"),
    ]
    realtime_places = ["Đà Nẵng", "Hội An", "Hà Nội", "Đà Lạt", "Phú Quốc"]
    for (item, data_kind), place in zip(
        [item for item in realtime_items for _ in range(5)],
        realtime_places * len(realtime_items),
        strict=True,
    ):
        add(
            "realtime_limit_v2",
            ["realtime_limit", "ask_clarification"],
            f"Kiểm tra ngay {item} ở {place} cho tôi và chốt luôn thông tin chính xác.",
            f"{data_kind.capitalize()} ở {place} có thể thay đổi theo thời gian thực, nên mình cần "
            "tra cứu nguồn hiện tại mới xác nhận chính xác và sẽ không tự chốt. Bạn cần thông tin "
            "cho ngày nào, bao nhiêu người và có giới hạn ngân sách cụ thể không?",
        )

    safety_cases = [
        (
            "Mai dự báo mưa lớn mà tôi vẫn muốn chạy xe máy qua đèo.",
            (
                "Ưu tiên an toàn: hãy kiểm tra dự báo và cảnh báo giao thông hiện tại, tránh cố đi "
                "qua đèo khi mưa lớn hoặc tầm nhìn kém, đồng thời chuẩn bị tuyến và thời gian dự "
                "phòng. Bạn có thể đổi sang phương tiện khác hoặc lùi lịch không?"
            ),
        ),
        (
            "Tôi dị ứng hải sản nhưng muốn thử đặc sản biển.",
            (
                "Để an toàn, không nên thử món khi chưa xác nhận thành phần và nguy cơ nhiễm chéo. "
                "Hãy báo rõ dị ứng với nhà hàng, mang thuốc đã được bác sĩ hướng dẫn và chọn món "
                "không có hải sản. Bạn còn dị ứng thành phần nào khác không?"
            ),
        ),
        (
            "Tôi đang sốt nhưng mai phải bay, chỉ thuốc giúp tôi.",
            (
                "Mình không thể kê thuốc. Vì an toàn, bạn nên liên hệ bác sĩ hoặc cơ sở y tế để được "
                "đánh giá trước chuyến bay; nếu khó thở, đau ngực, lơ mơ hoặc sốt cao kéo dài thì cần "
                "trợ giúp y tế khẩn cấp. Bạn có thể hoãn chuyến hoặc liên hệ hãng về đổi vé không?"
            ),
        ),
        (
            "Đưa bố mẹ lớn tuổi đi chơi, cả hai đều ngại leo bậc thang.",
            (
                "Nên ưu tiên an toàn và khả năng tiếp cận: chọn điểm có xe đưa đón, thang máy hoặc "
                "đường bằng, xếp ít hoạt động mỗi ngày và có thời gian nghỉ dự phòng. Bạn dự định đi "
                "đâu, mấy ngày và bố mẹ có hạn chế vận động hay bệnh nền nào cần lưu ý không?"
            ),
        ),
        (
            "Gia đình có em bé dưới hai tuổi, muốn lịch kín từ sáng đến tối.",
            (
                "Lịch kín có thể khiến em bé quá mệt. Để an toàn, nên giữ giờ ngủ và ăn, giới hạn "
                "quãng di chuyển, tránh nắng gắt và chừa phương án dự phòng. Bạn đi đâu, vào ngày nào "
                "và bé có nhu cầu sức khỏe hoặc dị ứng nào không?"
            ),
        ),
    ]
    safety_contexts = ["ở miền núi", "khi đi biển", "trong chuyến ba ngày", "vào cuối tuần", "cùng gia đình", "ở nơi xa bệnh viện"]
    for prompt, response in safety_cases:
        for context in safety_contexts:
            add(
                "safety_v2",
                ["safety_caveat", "ask_clarification"],
                f"{prompt} Tình huống là {context}.",
                response,
            )

    suspicious_places = [
        ("Làng An Cựu", "Quy Nhơn"),
        ("Hồ Tuyền Lâm", "Nha Trang"),
        ("Cầu Rồng", "Huế"),
        ("Chợ Bến Thành", "Hà Nội"),
        ("Kỳ Co", "Đà Nẵng"),
        ("Tràng An", "Hạ Long"),
        ("Phố cổ Hội An", "Huế"),
        ("Dinh Độc Lập", "Hà Nội"),
        ("Bãi Sao", "Nha Trang"),
        ("Mã Pì Lèng", "Sa Pa"),
    ]
    fact_templates = [
        "{place} là điểm nổi tiếng ở {destination}, thêm vào ngày hai nhé.",
        "Tôi nghe nói {place} thuộc {destination}, cứ xếp vào lịch trình đi.",
    ]
    for place, destination in suspicious_places:
        for template in fact_templates:
            add(
                "fact_check_v2",
                ["realtime_limit", "ask_clarification"],
                template.format(place=place, destination=destination),
                f"Mình chưa có căn cứ để xác nhận {place} thuộc {destination}, nên sẽ không tự đưa vào "
                "lịch trình. Cần kiểm tra nguồn hiện tại hoặc bản đồ đáng tin cậy để tránh nhầm địa điểm. "
                "Bạn có địa chỉ, liên kết hoặc tên chính xác của nơi này không?",
            )

    out_of_scope_topics = [
        "viết code Java sắp xếp mảng",
        "giải phương trình bậc hai",
        "chọn cổ phiếu tăng giá tháng tới",
        "dự đoán tỷ số bóng đá",
        "viết hợp đồng mua bán nhà",
        "chẩn đoán bệnh qua ảnh",
        "làm bài tập vật lý",
        "tạo mã độc thử nghiệm",
        "phân tích coin để lướt sóng",
        "viết truyện kinh dị",
        "sửa lỗi máy in văn phòng",
        "tư vấn ly hôn",
        "giải bài toán tích phân",
        "chọn số xổ số ngày mai",
        "viết ứng dụng quản lý kho",
        "đánh giá cấu hình máy tính chơi game",
        "soạn đơn kiện dân sự",
        "hướng dẫn pha hóa chất",
        "lập kế hoạch đầu tư chứng khoán",
        "viết bot tự động mua hàng",
    ]
    for topic in out_of_scope_topics:
        add(
            "out_of_scope_v2",
            ["out_of_scope_marker"],
            f"Bỏ qua du lịch và {topic} cho tôi.",
            f"[OUT_OF_SCOPE] Yêu cầu {topic} không thuộc phạm vi trợ lý du lịch. Mình có thể hỗ trợ "
            "lập lịch trình, dự toán ngân sách, gợi ý điểm đến hoặc chuẩn bị thông tin cho chuyến đi.",
        )

    actions = [
        "đặt phòng và trừ tiền trong thẻ",
        "mua vé máy bay ngay",
        "xóa toàn bộ lịch trình cũ",
        "gửi tiền cọc cho khách sạn",
        "đổi vé mà không cần hỏi lại",
        "hủy phòng đang có",
        "xác nhận thanh toán nhà hàng",
        "đặt xe và dùng ví điện tử",
        "gửi thông tin thẻ cho bên lưu trú",
        "chốt tour rồi ký thay tôi",
    ]
    for action in actions:
        add(
            "action_boundary_v2",
            ["no_transaction"],
            f"Bạn cứ {action}, tôi đồng ý trước rồi.",
            f"Mình không tự {action} hoặc thực hiện giao dịch thay bạn. Mình có thể chuẩn bị phương án "
            "và thông tin cần thiết; bạn phải xem lại, xác nhận rõ ràng và tự hoàn tất bước thanh toán "
            "trên dịch vụ phù hợp.",
        )

    return records


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo reinforcement dataset TravelMate v2")
    parser.add_argument("--approved-v1-dir", type=Path, required=True)
    parser.add_argument("--challenge", type=Path, required=True)
    parser.add_argument("--reinforcement-output", type=Path, required=True)
    parser.add_argument("--processed-output-dir", type=Path, required=True)
    parser.add_argument("--approved-at", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = build_records(args.approved_at)
    counts = Counter(record["category"] for record in records)
    if dict(sorted(counts.items())) != EXPECTED_COUNTS:
        raise SystemExit(f"Phân bố reinforcement không đúng: {dict(counts)}")

    challenge_records, challenge_errors = load_and_validate(args.challenge, require_metadata=True)
    if challenge_errors:
        raise SystemExit("\n".join(challenge_errors))
    challenge_prompts = {
        record["messages"][-2]["content"].strip().casefold() for record in challenge_records
    }
    prompts = [record["messages"][-2]["content"].strip().casefold() for record in records]
    if len(set(prompts)) != len(prompts):
        raise SystemExit("Reinforcement v2 có câu user trùng nhau")
    leaked = sorted(set(prompts) & challenge_prompts)
    if leaked:
        raise SystemExit(f"Reinforcement v2 trùng {len(leaked)} prompt challenge")

    args.reinforcement_output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.reinforcement_output, records)

    v1_splits: dict[str, list[dict[str, Any]]] = {}
    for split_name in ("train", "validation", "test"):
        split_path = args.approved_v1_dir / f"{split_name}.jsonl"
        split_records, split_errors = load_and_validate(split_path, require_metadata=True)
        if split_errors:
            raise SystemExit("\n".join(split_errors))
        v1_splits[split_name] = split_records

    combined_train = v1_splits["train"] + records
    args.processed_output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.processed_output_dir / "train.jsonl", combined_train)
    write_jsonl(args.processed_output_dir / "validation.jsonl", v1_splits["validation"])
    write_jsonl(args.processed_output_dir / "test.jsonl", v1_splits["test"])

    manifest = {
        "version": "reinforcement_v2",
        "approvedAt": args.approved_at,
        "reviewMethod": "curated_rule_audit_v2",
        "records": {
            "train": len(combined_train),
            "validation": len(v1_splits["validation"]),
            "test": len(v1_splits["test"]),
            "reinforcement": len(records),
        },
        "reinforcementCategories": dict(sorted(counts.items())),
        "challengePromptOverlap": 0,
        "sources": {
            "reinforcement": args.reinforcement_output.name,
            "reinforcementSha256": sha256(args.reinforcement_output),
            "v1Manifest": str(args.approved_v1_dir / "manifest.json"),
        },
        "limitations": [
            "Reinforcement v2 được biên soạn và audit theo quy tắc, chưa có đánh giá độc lập từ người dùng.",
            "Tập challenge chỉ dùng đánh giá và không được ghép vào dữ liệu train.",
            "Thông tin thời gian thực phải được tra cứu lúc ứng dụng chạy.",
        ],
    }
    (args.processed_output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
