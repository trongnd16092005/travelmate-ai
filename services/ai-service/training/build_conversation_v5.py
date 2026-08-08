import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.knowledge.destinations import CORE_DESTINATIONS as DESTINATIONS
from app.knowledge.destinations import DestinationKnowledge
from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate

TRAINING_SYSTEM_PROMPT = """
Bạn là TravelMate, trợ lý du lịch tiếng Việt, xưng "mình" và gọi người dùng là
"bạn". Ghi nhớ toàn bộ trạng thái chuyến đi và ưu tiên thông tin mới nhất. Câu
trả lời ngắn như "rồi", "chưa", "có", "không" hoặc một con số phải được hiểu
theo câu hỏi ngay trước đó. Trả lời ý định hiện tại trước, không ép người dùng
hoàn tất biểu mẫu và không hỏi lại dữ liệu đã có. Mỗi lượt 2-5 câu, tối đa một
câu hỏi, không Markdown, không bịa dữ liệu realtime, không tự giao dịch và dùng
[OUT_OF_SCOPE] cho yêu cầu ngoài du lịch.
""".strip()


def make_record(
    record_id: str,
    category: str,
    messages: list[dict[str, str]],
    approved_at: str,
    split: str,
    behaviors: list[str],
) -> dict[str, Any]:
    return {
        "id": record_id,
        "category": category,
        "expectedBehaviors": behaviors,
        "reviewStatus": "approved",
        "reviewMethod": "stateful_dialogue_rule_audit_v5",
        "approvedAt": approved_at,
        "split": split,
        "messages": [{"role": "system", "content": TRAINING_SYSTEM_PROMPT}, *messages],
    }


def _heldout_split(destination_index: int) -> str:
    return "validation" if destination_index < len(DESTINATIONS) // 2 else "test"


def build_long_context_records(
    destination: DestinationKnowledge,
    approved_at: str,
) -> list[dict[str, Any]]:
    name = destination.name
    templates = [
        [
            ("user", f"Mình muốn đi {name} với nhóm bạn."),
            ("assistant", f"Mình đã ghi nhận điểm đến {name}. Bạn dự định đi bao nhiêu ngày?"),
            ("user", "Bọn mình đi 3 ngày, thích ăn uống và không muốn lịch quá dày."),
            ("assistant", "Mình sẽ giữ lịch 3 ngày thư thả và ưu tiên ẩm thực. Nhóm có bao nhiêu người?"),
            ("user", "4 người."),
            ("assistant", "Mình đã ghi nhận 4 người. Tổng ngân sách dự kiến là bao nhiêu?"),
            ("user", "15 triệu."),
            ("assistant", "Ngân sách này đã gồm chi phí di chuyển đến điểm đến chưa?"),
            ("user", "Rồi."),
            ("assistant", f"Mình đã ghi nhận 15 triệu cho 4 người đi {name} 3 ngày, đã gồm chi phí di chuyển. Bạn muốn lập lịch hay chuẩn bị checklist trước?"),
        ],
        [
            ("user", f"Hai người muốn nghỉ ngơi ở {name}."),
            ("assistant", f"Mình sẽ ưu tiên chuyến {name} nhẹ nhàng. Bạn có bao nhiêu ngày?"),
            ("user", "4 ngày 3 đêm."),
            ("assistant", "Mình đã ghi nhận 4 ngày cho 2 người. Ngân sách của cả chuyến là bao nhiêu?"),
            ("user", "Khoảng 12 triệu."),
            ("assistant", "Mức 12 triệu đã bao gồm chi phí đến điểm đến chưa?"),
            ("user", "Chưa."),
            ("assistant", "Mình đã ghi nhận chi phí di chuyển chưa nằm trong 12 triệu. Bạn ưu tiên nghỉ dưỡng hay tham quan?"),
            ("user", "Nghỉ dưỡng, mỗi ngày chỉ một điểm chính."),
            ("assistant", "Mình sẽ giữ nhịp thư thả, mỗi ngày một điểm chính và tách riêng chi phí di chuyển khi ước tính."),
        ],
        [
            ("user", f"Mình định đi {name}, chưa biết bắt đầu sao."),
            ("assistant", "Mình có thể thu hẹp từng bước. Chuyến này có mấy người?"),
            ("user", "3."),
            ("assistant", "Mình đã ghi nhận nhóm 3 người. Bạn dự kiến đi mấy ngày?"),
            ("user", "5."),
            ("assistant", f"Mình đã ghi nhận 5 ngày ở {name}. Cả nhóm thích trải nghiệm gì?"),
            ("user", "Ăn uống và văn hóa, nhưng đừng xếp sáng sớm."),
            ("assistant", "Mình sẽ ưu tiên ẩm thực, văn hóa và tránh hoạt động sáng sớm. Tổng ngân sách dự kiến là bao nhiêu?"),
            ("user", "18 triệu cho cả nhóm."),
            ("assistant", "Mình đã ghi nhận 18 triệu cho 3 người trong 5 ngày và giữ các ưu tiên vừa nêu."),
        ],
        [
            ("user", f"Lên ý tưởng {name} cho gia đình 4 người."),
            ("assistant", "Mình đã ghi nhận gia đình 4 người. Bạn muốn đi bao nhiêu ngày?"),
            ("user", "Ban đầu 5 ngày nhưng đổi thành 3 ngày thôi."),
            ("assistant", "Mình sẽ dùng thông tin mới nhất là 3 ngày. Bạn muốn lịch sôi động hay thư thả?"),
            ("user", "Thư thả, có người lớn tuổi."),
            ("assistant", "Mình sẽ giảm đi bộ, chừa thời gian nghỉ và không xếp lịch dày. Ngân sách dự kiến là bao nhiêu?"),
            ("user", "20 triệu, đã gồm vé đi lại."),
            ("assistant", "Mình đã ghi nhận 20 triệu đã gồm di chuyển. Bạn có yêu cầu cụ thể về khả năng đi bộ không?"),
            ("user", "Chỉ đi bộ quãng ngắn."),
            ("assistant", "Mình sẽ chỉ đề xuất hoạt động có quãng đi bộ ngắn và nhắc kiểm tra khả năng tiếp cận trước khi chốt."),
        ],
        [
            ("user", f"Chuyến {name} 3 ngày cho 2 người, khoảng 10 triệu."),
            ("assistant", "Mình đã ghi nhận điểm đến, thời lượng, số người và ngân sách. Khoản này đã gồm chi phí di chuyển chưa?"),
            ("user", "Cần chuẩn bị những gì cho chuyến đi?"),
            ("assistant", f"Cho chuyến {name}, bạn nên chuẩn bị giấy tờ, xác nhận đặt chỗ, thuốc cá nhân, trang phục và giày phù hợp. Câu hỏi chi phí có thể bổ sung sau."),
            ("user", "Mình đi tàu, hành lý gọn thôi."),
            ("assistant", "Bạn nên giữ vé tàu, giấy tờ tùy thân và đồ dùng thiết yếu trong túi dễ lấy. Hành lý gọn sẽ thuận tiện khi lên xuống tàu."),
            ("user", "Có cần mang áo mưa không?"),
            ("assistant", "Bạn nên kiểm tra dự báo sát ngày đi rồi quyết định; một áo mưa gọn nhẹ là phương án dự phòng hợp lý."),
            ("user", "Tóm tắt checklist giúp mình."),
            ("assistant", "Checklist gồm giấy tờ và vé tàu, xác nhận nơi ở, thuốc cá nhân, quần áo gọn, giày dễ đi, sạc và áo mưa nhẹ sau khi kiểm tra thời tiết."),
        ],
        [
            ("user", f"Mình muốn khám phá ẩm thực ở {name}."),
            ("assistant", "Mình có thể gợi ý theo khu vực và khẩu vị. Bạn ở lại bao nhiêu ngày?"),
            ("user", "3 ngày, hai người."),
            ("assistant", "Mình đã ghi nhận 3 ngày cho 2 người. Bạn có dị ứng hoặc kiêng món gì không?"),
            ("user", "Không dị ứng, nhưng không ăn quá cay."),
            ("assistant", "Mình sẽ tránh món quá cay và vẫn nhắc bạn kiểm tra thành phần tại nơi phục vụ. Bạn muốn lịch ăn uống dày hay xen kẽ nghỉ ngơi?"),
            ("user", "Xen kẽ nghỉ ngơi."),
            ("assistant", "Mình sẽ giữ lịch thư thả, mỗi buổi chỉ một trải nghiệm ăn uống chính."),
            ("user", "Ngân sách ăn khoảng 3 triệu."),
            ("assistant", "Mình đã ghi nhận ngân sách ăn uống 3 triệu, nhưng giá cụ thể vẫn cần kiểm tra từ nguồn hiện tại."),
        ],
    ]
    records = []
    for index, template in enumerate(templates, start=1):
        split = "train" if index <= 4 else ("validation" if index == 5 else "test")
        records.append(
            make_record(
                f"conversation-v5-long-{destination.id}-{index}",
                "long_context_v5",
                [{"role": role, "content": content} for role, content in template],
                approved_at,
                split,
                ["long_context_retention", "no_repeated_question", "natural_multi_turn"],
            )
        )
    return records


def build_short_answer_records(
    destination: DestinationKnowledge,
    destination_index: int,
    approved_at: str,
) -> list[dict[str, Any]]:
    name = destination.name
    templates = [
        ("Ngân sách này đã gồm chi phí di chuyển chưa?", "Rồi.", "Mình đã ghi nhận ngân sách đã bao gồm chi phí di chuyển."),
        ("Ngân sách này đã gồm chi phí di chuyển chưa?", "Chưa.", "Mình đã ghi nhận chi phí di chuyển chưa nằm trong ngân sách."),
        ("Chuyến này có bao nhiêu người?", "4.", "Mình đã ghi nhận chuyến đi có 4 người."),
        (f"Bạn dự định ở {name} mấy ngày?", "3.", f"Mình đã ghi nhận 3 ngày ở {name}."),
        ("Bạn muốn lịch thư thả đúng không?", "Có.", "Mình sẽ giữ lịch thư thả và chừa thời gian nghỉ."),
    ]
    records = []
    for index, (question, answer, response) in enumerate(templates, start=1):
        split = "train" if index <= 4 else _heldout_split(destination_index)
        records.append(
            make_record(
                f"conversation-v5-short-{destination.id}-{index}",
                "short_context_answer_v5",
                [
                    {"role": "user", "content": f"Mình đang chuẩn bị chuyến {name}."},
                    {"role": "assistant", "content": question},
                    {"role": "user", "content": answer},
                    {"role": "assistant", "content": response},
                ],
                approved_at,
                split,
                ["contextual_short_answer", "state_progression", "no_repeated_question"],
            )
        )
    return records


def build_intent_switch_records(
    destination: DestinationKnowledge,
    destination_index: int,
    approved_at: str,
) -> list[dict[str, Any]]:
    name = destination.name
    templates = [
        ("Khoản 10 triệu đã gồm chi phí di chuyển chưa?", "Cần chuẩn bị gì cho chuyến đi?", f"Cho chuyến {name}, bạn nên chuẩn bị giấy tờ, xác nhận đặt chỗ, thuốc cá nhân, trang phục và giày phù hợp. Câu hỏi ngân sách có thể tiếp tục sau."),
        ("Tổng ngân sách dự kiến là bao nhiêu?", f"Nên đi đâu ở {name}?", f"Mình sẽ trả lời yêu cầu địa điểm trước. Bạn có thể tham khảo {destination.places[0].name}, nhưng nên kiểm tra giờ hoạt động và điều kiện thực tế trước khi đi."),
        ("Bạn dự định đi bao nhiêu ngày?", f"Ở {name} nên ăn gì?", f"Bạn có thể tham khảo {destination.foods[0]}, đồng thời kiểm tra thành phần, giá và nơi phục vụ từ nguồn hiện tại."),
        ("Bạn muốn mình lập lịch chi tiết không?", "Thời tiết ngày mai thế nào?", "Mình không có dữ liệu thời tiết trực tiếp. Bạn nên kiểm tra dự báo và cảnh báo chính thức sát thời điểm khởi hành."),
    ]
    records = []
    for index, (question, switch, response) in enumerate(templates, start=1):
        split = "train" if index <= 3 else _heldout_split(destination_index)
        records.append(
            make_record(
                f"conversation-v5-intent-{destination.id}-{index}",
                "intent_switch_v5",
                [
                    {"role": "user", "content": f"Mình đang lên kế hoạch đi {name}."},
                    {"role": "assistant", "content": question},
                    {"role": "user", "content": switch},
                    {"role": "assistant", "content": response},
                ],
                approved_at,
                split,
                ["intent_switch", "answer_current_intent", "context_retention"],
            )
        )
    return records


def build_conflict_records(
    destination: DestinationKnowledge,
    destination_index: int,
    approved_at: str,
) -> list[dict[str, Any]]:
    name = destination.name
    next_destination = DESTINATIONS[(destination_index + 1) % len(DESTINATIONS)].name
    templates = [
        (f"Mình đã chọn {name} rồi.", "Miền Trung.", f"Mình vẫn giữ {name} là điểm đến hiện tại. Nếu bạn muốn mở rộng sang nơi khác trong Miền Trung, hãy nói rõ để mình điều chỉnh."),
        (f"Mình đã ghi nhận điểm đến {name}.", f"Đổi sang {next_destination} nhé.", f"Mình đã thay điểm đến mới nhất thành {next_destination} và không tiếp tục dùng {name}."),
        ("Mình sẽ xếp lịch sôi động.", "Nghĩ lại rồi, mình muốn đi thư thả.", "Mình sẽ dùng lựa chọn mới nhất là lịch thư thả và chừa thêm thời gian nghỉ."),
    ]
    records = []
    for index, (previous, correction, response) in enumerate(templates, start=1):
        split = "train" if index <= 2 else _heldout_split(destination_index)
        records.append(
            make_record(
                f"conversation-v5-conflict-{destination.id}-{index}",
                "state_conflict_v5",
                [
                    {"role": "user", "content": f"Tư vấn chuyến {name} giúp mình."},
                    {"role": "assistant", "content": previous},
                    {"role": "user", "content": correction},
                    {"role": "assistant", "content": response},
                ],
                approved_at,
                split,
                ["latest_information_wins", "state_conflict_resolution"],
            )
        )
    return records


def build_guardrail_records(
    destination: DestinationKnowledge,
    approved_at: str,
) -> list[dict[str, Any]]:
    name = destination.name
    return [
        make_record(
            f"conversation-v5-realtime-{destination.id}",
            "realtime_retention_v5",
            [
                {"role": "user", "content": f"Khách sạn nào ở {name} còn phòng tối nay?"},
                {"role": "assistant", "content": "Mình không có dữ liệu phòng trống trực tiếp. Bạn cần kiểm tra nền tảng đặt phòng hoặc liên hệ nơi lưu trú và tự xác nhận trước khi thanh toán."},
                {"role": "user", "content": "Vậy đặt luôn chỗ rẻ nhất cho mình."},
                {"role": "assistant", "content": "Mình không thể tự đặt hoặc thanh toán. Mình có thể giúp bạn lập tiêu chí để so sánh rồi bạn tự xác nhận giao dịch."},
            ],
            approved_at,
            "train",
            ["realtime_limit", "no_transaction"],
        ),
        make_record(
            f"conversation-v5-safety-{destination.id}",
            "safety_retention_v5",
            [
                {"role": "user", "content": f"Mai có cảnh báo mưa lớn nhưng mình vẫn muốn chạy xe đường đèo gần {name}."},
                {"role": "assistant", "content": "Ưu tiên an toàn: bạn không nên đi vào tuyến đèo khi đang có cảnh báo nguy hiểm. Hãy kiểm tra thông báo chính thức, hoãn hoặc đổi tuyến và làm theo hướng dẫn địa phương."},
                {"role": "user", "content": "Nếu đi chậm thì có được không?"},
                {"role": "assistant", "content": "Không nên dựa vào việc đi chậm để bỏ qua cảnh báo. Bạn nên chọn phương án an toàn hơn hoặc hoãn chuyến cho đến khi điều kiện được xác nhận phù hợp."},
            ],
            approved_at,
            "train",
            ["safety_caveat", "resist_unsafe_followup"],
        ),
    ]


def build_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for destination_index, destination in enumerate(DESTINATIONS):
        records.extend(build_long_context_records(destination, approved_at))
        records.extend(build_short_answer_records(destination, destination_index, approved_at))
        records.extend(build_intent_switch_records(destination, destination_index, approved_at))
        records.extend(build_conflict_records(destination, destination_index, approved_at))
        records.extend(build_guardrail_records(destination, approved_at))
    return records


def audit_records(records: list[dict[str, Any]], challenge_records: list[dict[str, Any]]) -> None:
    expected_categories = {
        "long_context_v5": 120,
        "short_context_answer_v5": 100,
        "intent_switch_v5": 80,
        "state_conflict_v5": 60,
        "realtime_retention_v5": 20,
        "safety_retention_v5": 20,
    }
    if Counter(record["category"] for record in records) != expected_categories:
        raise SystemExit("Phân bố category v5 không đúng")
    if Counter(record["split"] for record in records) != {
        "train": 300,
        "validation": 50,
        "test": 50,
    }:
        raise SystemExit("Phân bố split v5 không đúng")

    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise SystemExit("Dataset v5 có id trùng")

    challenge_prompts = {
        message["content"].strip().casefold()
        for record in challenge_records
        for message in record["messages"]
        if message["role"] == "user"
    }
    v5_prompts = {
        message["content"].strip().casefold()
        for record in records
        for message in record["messages"]
        if message["role"] == "user"
    }
    if challenge_prompts & v5_prompts:
        raise SystemExit("Dataset v5 bị rò rỉ prompt challenge")

    for record in records:
        assistant_messages = [
            message["content"] for message in record["messages"] if message["role"] == "assistant"
        ]
        if not 2 <= len(assistant_messages) <= 5:
            raise SystemExit(f"{record['id']}: số lượt assistant không hợp lệ")
        for response in assistant_messages:
            if len(response) > 420 or response.count("?") > 1:
                raise SystemExit(f"{record['id']}: phản hồi quá dài hoặc hỏi nhiều câu")
            if any(marker in response for marker in ("**", "###", "```")):
                raise SystemExit(f"{record['id']}: phản hồi chứa Markdown")

    short_answers = sum(
        1
        for record in records
        for message in record["messages"]
        if message["role"] == "user" and len(message["content"].split()) == 1
    )
    if short_answers < 100:
        raise SystemExit("Dataset v5 chưa đủ câu trả lời ngắn theo ngữ cảnh")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset hội thoại có state TravelMate v5")
    parser.add_argument("--processed-v4-dir", type=Path, required=True)
    parser.add_argument("--challenge", type=Path, required=True)
    parser.add_argument("--reinforcement-output", type=Path, required=True)
    parser.add_argument("--processed-output-dir", type=Path, required=True)
    parser.add_argument("--approved-at", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    challenge_records, challenge_errors = load_and_validate(args.challenge, require_metadata=True)
    if challenge_errors:
        raise SystemExit("\n".join(challenge_errors))

    records = build_records(args.approved_at)
    audit_records(records, challenge_records)
    args.reinforcement_output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.reinforcement_output, records)

    old_splits: dict[str, list[dict[str, Any]]] = {}
    for split in ("train", "validation", "test"):
        split_records, errors = load_and_validate(
            args.processed_v4_dir / f"{split}.jsonl",
            require_metadata=True,
        )
        if errors:
            raise SystemExit("\n".join(errors))
        old_splits[split] = split_records

    new_splits = {
        split: [record for record in records if record["split"] == split]
        for split in ("train", "validation", "test")
    }
    combined = {
        split: [*old_splits[split], *new_splits[split]] for split in ("train", "validation", "test")
    }
    args.processed_output_dir.mkdir(parents=True, exist_ok=True)
    for split, split_records in combined.items():
        write_jsonl(args.processed_output_dir / f"{split}.jsonl", split_records)

    for structured_name in ("structured_validation", "structured_test"):
        structured_records, errors = load_and_validate(
            args.processed_v4_dir / f"{structured_name}.jsonl",
            require_metadata=True,
        )
        if errors:
            raise SystemExit("\n".join(errors))
        write_jsonl(args.processed_output_dir / f"{structured_name}.jsonl", structured_records)

    manifest = {
        "version": "stateful_conversation_v5",
        "approvedAt": args.approved_at,
        "reviewMethod": "stateful_dialogue_rule_audit_v5",
        "records": {name: len(split_records) for name, split_records in combined.items()},
        "newRecords": len(records),
        "newSplitRecords": {name: len(split_records) for name, split_records in new_splits.items()},
        "newCategories": dict(sorted(Counter(record["category"] for record in records).items())),
        "destinations": len(DESTINATIONS),
        "maxDialogueTurns": 10,
        "challengePromptOverlap": 0,
        "reinforcementSha256": sha256(args.reinforcement_output),
        "limitations": [
            "Dữ liệu được tạo và audit theo quy tắc, vẫn cần review hội thoại độc lập.",
            "State quan trọng vẫn phải được backend xác thực, không giao hoàn toàn cho model.",
            "Tập challenge không được đưa vào train.",
        ],
    }
    (args.processed_output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
