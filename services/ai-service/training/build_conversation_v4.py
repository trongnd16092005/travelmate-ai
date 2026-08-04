import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.knowledge.destinations import DESTINATIONS, DestinationKnowledge
from app.prompts.chat import CHAT_SYSTEM_PROMPT
from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate


def make_record(
    record_id: str,
    category: str,
    messages: list[dict[str, str]],
    approved_at: str,
) -> dict[str, Any]:
    return {
        "id": record_id,
        "category": category,
        "expectedBehaviors": ["natural_multi_turn", "context_retention"],
        "reviewStatus": "approved",
        "reviewMethod": "multi_turn_style_rule_audit_v4",
        "approvedAt": approved_at,
        "split": "train",
        "messages": [{"role": "system", "content": CHAT_SYSTEM_PROMPT}, *messages],
    }


def build_slot_records(
    destination: DestinationKnowledge,
    approved_at: str,
) -> list[dict[str, Any]]:
    name = destination.name
    return [
        make_record(
            f"conversation-v4-slot-{destination.id}-1",
            "multi_turn_slot_v4",
            [
                {"role": "user", "content": f"Mình muốn đi {name} nhưng chưa biết bắt đầu từ đâu."},
                {"role": "assistant", "content": f"Mình có thể giúp bạn thu hẹp kế hoạch. Bạn muốn ở {name} bao nhiêu ngày?"},
                {"role": "user", "content": f"Khoảng 3 ngày ở {name}, ưu tiên ăn uống và đi thong thả."},
                {"role": "assistant", "content": "Mình đã ghi nhận lịch nhẹ trong 3 ngày, ưu tiên ẩm thực. Bạn dự định khởi hành ngày nào?"},
            ],
            approved_at,
        ),
        make_record(
            f"conversation-v4-slot-{destination.id}-2",
            "multi_turn_slot_v4",
            [
                {"role": "user", "content": f"Tư vấn giúp mình chuyến {name} 4 ngày nhé."},
                {"role": "assistant", "content": f"Được, mình sẽ chuẩn bị phương án 4 ngày ở {name}. Bạn đi cùng bao nhiêu người?"},
                {"role": "user", "content": f"Chuyến {name} này có 2 người, không cần lịch quá dày."},
                {"role": "assistant", "content": "Mình sẽ giữ nhịp lịch vừa phải cho 2 người. Tổng ngân sách dự kiến của bạn là bao nhiêu?"},
            ],
            approved_at,
        ),
        make_record(
            f"conversation-v4-slot-{destination.id}-3",
            "multi_turn_slot_v4",
            [
                {"role": "user", "content": f"Mình xuất phát từ Hà Nội và muốn đến {name}."},
                {"role": "assistant", "content": f"Mình hiểu Hà Nội là nơi xuất phát và {name} là điểm đến. Bạn dự định khởi hành ngày nào?"},
                {"role": "user", "content": f"Chuyến {name} dự kiến bắt đầu ngày 15 tháng sau."},
                {"role": "assistant", "content": "Mình đã ghi nhận ngày dự kiến và sẽ chưa tự xác nhận giá vé. Chuyến này có bao nhiêu người?"},
            ],
            approved_at,
        ),
        make_record(
            f"conversation-v4-slot-{destination.id}-4",
            "multi_turn_slot_v4",
            [
                {"role": "user", "content": f"Hai người muốn nghỉ ngơi ở {name}, chưa chốt chi phí."},
                {"role": "assistant", "content": "Mình sẽ ưu tiên trải nghiệm thư thả cho 2 người. Bạn muốn giữ tổng ngân sách trong khoảng nào?"},
                {"role": "user", "content": f"Tổng ngân sách cho {name} khoảng 8 triệu."},
                {"role": "assistant", "content": "Mình đã ghi nhận mức 8 triệu và sẽ kiểm tra giá hiện tại trước khi ước tính. Bạn muốn chuyến đi kéo dài bao nhiêu ngày?"},
            ],
            approved_at,
        ),
    ]


def build_correction_records(
    destination: DestinationKnowledge,
    approved_at: str,
) -> list[dict[str, Any]]:
    name = destination.name
    return [
        make_record(
            f"conversation-v4-correction-{destination.id}-1",
            "multi_turn_correction_v4",
            [
                {"role": "user", "content": f"Lên ý tưởng ba ngày ở {name} cho mình."},
                {"role": "assistant", "content": f"Mình có thể chia ba ngày ở {name} thành tham quan, ăn uống và nghỉ ngơi. Bạn muốn lịch sôi động hay thư thả?"},
                {"role": "user", "content": f"Mình đổi ý, chuyến {name} chỉ cần mỗi ngày một điểm chính thôi."},
                {"role": "assistant", "content": "Được, mình sẽ giới hạn mỗi ngày một điểm chính và chừa thời gian nghỉ. Bạn muốn ưu tiên thiên nhiên hay văn hóa?"},
            ],
            approved_at,
        ),
        make_record(
            f"conversation-v4-correction-{destination.id}-2",
            "multi_turn_correction_v4",
            [
                {"role": "user", "content": f"Có thể ghép thêm tỉnh khác vào chuyến {name} không?"},
                {"role": "assistant", "content": "Có thể cân nhắc nếu thời gian di chuyển hợp lý, nhưng cần nói rõ đó là điểm đến khác. Bạn có bao nhiêu ngày?"},
                {"role": "user", "content": f"Thôi, mình chỉ muốn ở trong {name}, không thêm tỉnh nào khác."},
                {"role": "assistant", "content": f"Mình sẽ giữ toàn bộ lịch trong {name} và không tự thêm điểm đến khác. Bạn muốn ở khu vực trung tâm hay yên tĩnh hơn?"},
            ],
            approved_at,
        ),
        make_record(
            f"conversation-v4-correction-{destination.id}-3",
            "multi_turn_correction_v4",
            [
                {"role": "user", "content": f"Chuyến {name} này mình muốn đi thật nhiều nơi."},
                {"role": "assistant", "content": "Mình có thể xếp nhiều trải nghiệm, nhưng lịch quá dày sẽ ít thời gian nghỉ. Bạn dự định đi mấy ngày?"},
                {"role": "user", "content": f"Nghĩ lại rồi, ở {name} mình muốn ngủ đủ và không đi sáng sớm."},
                {"role": "assistant", "content": "Mình đã bỏ các hoạt động sáng sớm và sẽ bắt đầu ngày muộn hơn. Bạn muốn hoạt động đầu tiên khoảng mấy giờ?"},
            ],
            approved_at,
        ),
    ]


def build_budget_records(
    destination: DestinationKnowledge,
    approved_at: str,
) -> list[dict[str, Any]]:
    name = destination.name
    return [
        make_record(
            f"conversation-v4-budget-{destination.id}-1",
            "multi_turn_budget_v4",
            [
                {"role": "user", "content": f"Mình có 6 triệu để đi {name}, liệu có ổn không?"},
                {"role": "assistant", "content": "Mình cần biết quy mô nhóm trước khi đánh giá mức ngân sách. Chuyến này có bao nhiêu người?"},
                {"role": "user", "content": f"Ngân sách 6 triệu cho chuyến {name} là của 2 người."},
                {"role": "assistant", "content": "Mình đã ghi nhận 6 triệu cho 2 người, nhưng giá thực tế vẫn cần kiểm tra. Bạn dự định đi bao nhiêu ngày?"},
            ],
            approved_at,
        ),
        make_record(
            f"conversation-v4-budget-{destination.id}-2",
            "multi_turn_budget_v4",
            [
                {"role": "user", "content": f"Nhóm bốn người đang tính đi {name}."},
                {"role": "assistant", "content": "Mình đã ghi nhận nhóm 4 người. Tổng ngân sách bạn muốn giữ là bao nhiêu?"},
                {"role": "user", "content": f"Cả nhóm có khoảng 12 triệu cho chuyến {name}."},
                {"role": "assistant", "content": "Mình sẽ dùng mức 12 triệu làm giới hạn và không tự khẳng định giá dịch vụ. Bạn dự kiến khởi hành ngày nào?"},
            ],
            approved_at,
        ),
    ]


def build_followup_records(
    destination: DestinationKnowledge,
    approved_at: str,
) -> list[dict[str, Any]]:
    name = destination.name
    place = destination.places[0].name
    food = destination.foods[0]
    return [
        make_record(
            f"conversation-v4-followup-{destination.id}-1",
            "multi_turn_followup_v4",
            [
                {"role": "user", "content": f"Ở {name} nên ưu tiên trải nghiệm nào?"},
                {"role": "assistant", "content": f"Nếu muốn một điểm tiêu biểu, bạn có thể cân nhắc {place} rồi dành thời gian nghỉ. Bạn có bao nhiêu ngày ở {name}?"},
                {"role": "user", "content": f"Mình chỉ còn một buổi chiều ở {name} thôi."},
                {"role": "assistant", "content": f"Với một buổi chiều, bạn chỉ nên chọn {place} hoặc một hoạt động gần chỗ ở, không cố ghép nhiều điểm. Hãy kiểm tra giờ hoạt động và thời gian di chuyển trước khi đi."},
            ],
            approved_at,
        ),
        make_record(
            f"conversation-v4-followup-{destination.id}-2",
            "multi_turn_followup_v4",
            [
                {"role": "user", "content": f"Mình muốn thử món địa phương ở {name}."},
                {"role": "assistant", "content": f"Bạn có thể tham khảo {food}, nhưng nên kiểm tra thành phần và giá tại nơi phục vụ. Bạn có kiêng hoặc dị ứng món gì không?"},
                {"role": "user", "content": f"Chuyến {name} này mình không kiêng món nào, chỉ không muốn đi xa để ăn."},
                {"role": "assistant", "content": f"Vậy mình sẽ ưu tiên quán gần khu vực lưu trú và xem {food} là gợi ý, không phải lựa chọn bắt buộc. Địa chỉ, giờ mở cửa và giá cần được kiểm tra từ nguồn hiện tại."},
            ],
            approved_at,
        ),
    ]


def build_casual_record(
    destination: DestinationKnowledge,
    approved_at: str,
) -> dict[str, Any]:
    name = destination.name
    return make_record(
        f"conversation-v4-casual-{destination.id}",
        "multi_turn_casual_v4",
        [
            {"role": "user", "content": f"Đi {name} kiểu chill chill thôi nha."},
            {"role": "assistant", "content": f"Được, mình sẽ giữ lịch {name} nhẹ và có nhiều thời gian trống. Bạn muốn đi trong mấy ngày?"},
            {"role": "user", "content": f"Tầm 3 hôm ở {name}, có 2 người."},
            {"role": "assistant", "content": "Ổn, mình ghi nhận 3 ngày cho 2 người và sẽ không xếp lịch quá dày. Bạn dự định đi vào ngày nào?"},
        ],
        approved_at,
    )


def build_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for destination in DESTINATIONS:
        records.extend(build_slot_records(destination, approved_at))
        records.extend(build_correction_records(destination, approved_at))
        records.extend(build_budget_records(destination, approved_at))
        records.extend(build_followup_records(destination, approved_at))
        records.append(build_casual_record(destination, approved_at))
    for record in records:
        if record["category"] == "multi_turn_casual_v4":
            record["split"] = "test"
        elif record["category"] == "multi_turn_followup_v4" and record["id"].endswith("-2"):
            record["split"] = "validation"
    return records


def audit_records(records: list[dict[str, Any]], challenge_records: list[dict[str, Any]]) -> None:
    expected_categories = {
        "multi_turn_slot_v4": 80,
        "multi_turn_correction_v4": 60,
        "multi_turn_budget_v4": 40,
        "multi_turn_followup_v4": 40,
        "multi_turn_casual_v4": 20,
    }
    actual_categories = Counter(record["category"] for record in records)
    if actual_categories != expected_categories:
        raise SystemExit(f"Phân bố v4 không đúng: {dict(actual_categories)}")
    split_counts = Counter(record["split"] for record in records)
    if split_counts != {"train": 200, "validation": 20, "test": 20}:
        raise SystemExit(f"Phân bố split v4 không đúng: {dict(split_counts)}")

    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise SystemExit("Dataset v4 có id trùng")

    challenge_prompts = {
        message["content"].strip().casefold()
        for record in challenge_records
        for message in record["messages"]
        if message["role"] == "user"
    }
    user_prompts: list[str] = []
    for record in records:
        assistant_messages = [
            message["content"] for message in record["messages"] if message["role"] == "assistant"
        ]
        if len(assistant_messages) != 2:
            raise SystemExit(f"{record['id']}: cần đúng hai lượt assistant")
        for response in assistant_messages:
            if len(response) > 320 or response.count("?") > 1:
                raise SystemExit(f"{record['id']}: phản hồi quá dài hoặc hỏi nhiều câu")
            if any(marker in response for marker in ("**", "###", "```")):
                raise SystemExit(f"{record['id']}: phản hồi chứa Markdown")
        user_prompts.extend(
            message["content"].strip().casefold()
            for message in record["messages"]
            if message["role"] == "user"
        )
    if len(user_prompts) != len(set(user_prompts)):
        raise SystemExit("Dataset v4 có lượt user trùng nhau")
    if challenge_prompts & set(user_prompts):
        raise SystemExit("Dataset v4 bị rò rỉ prompt challenge")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset hội thoại tự nhiên TravelMate v4")
    parser.add_argument("--processed-v3-dir", type=Path, required=True)
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
            args.processed_v3_dir / f"{split}.jsonl",
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
        split: [*old_splits[split], *new_splits[split]]
        for split in ("train", "validation", "test")
    }
    args.processed_output_dir.mkdir(parents=True, exist_ok=True)
    for split, split_records in combined.items():
        write_jsonl(args.processed_output_dir / f"{split}.jsonl", split_records)

    for structured_name in ("structured_validation", "structured_test"):
        structured_records, errors = load_and_validate(
            args.processed_v3_dir / f"{structured_name}.jsonl",
            require_metadata=True,
        )
        if errors:
            raise SystemExit("\n".join(errors))
        write_jsonl(
            args.processed_output_dir / f"{structured_name}.jsonl",
            structured_records,
        )

    manifest = {
        "version": "natural_conversation_v4",
        "approvedAt": args.approved_at,
        "reviewMethod": "multi_turn_style_rule_audit_v4",
        "records": {name: len(split_records) for name, split_records in combined.items()},
        "newRecords": len(records),
        "newSplitRecords": {name: len(split_records) for name, split_records in new_splits.items()},
        "newCategories": dict(sorted(Counter(record["category"] for record in records).items())),
        "destinations": len(DESTINATIONS),
        "turnsPerRecord": 4,
        "challengePromptOverlap": 0,
        "reinforcementSha256": sha256(args.reinforcement_output),
        "limitations": [
            "Dữ liệu được tạo và audit theo quy tắc, vẫn cần đánh giá hội thoại độc lập.",
            "V4 tập trung phong cách nhiều lượt, không bổ sung dữ kiện realtime.",
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
