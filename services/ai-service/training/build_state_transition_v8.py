import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.knowledge.destinations import DESTINATIONS, DestinationKnowledge
from training.build_conversation_v5 import TRAINING_SYSTEM_PROMPT
from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate

REGIONS = ("Miền Bắc", "Miền Trung", "Miền Nam", "Tây Nguyên")


def make_record(
    record_id: str,
    category: str,
    dialogue: list[dict[str, str]],
    approved_at: str,
    split: str,
    behaviors: list[str],
) -> dict[str, Any]:
    return {
        "id": record_id,
        "category": category,
        "expectedBehaviors": behaviors,
        "reviewStatus": "approved",
        "reviewMethod": "state_transition_rule_audit_v8",
        "approvedAt": approved_at,
        "split": split,
        "messages": [{"role": "system", "content": TRAINING_SYSTEM_PROMPT}, *dialogue],
    }


def current_trip(destination: DestinationKnowledge) -> list[dict[str, str]]:
    return [
        {
            "role": "user",
            "content": f"Mình đang đi {destination.name} 3 ngày, 2 người, ngân sách 10 triệu.",
        },
        {
            "role": "assistant",
            "content": (
                f"Mình đã ghi nhận chuyến {destination.name} 3 ngày cho 2 người, ngân sách "
                "10 triệu. Bạn cần hỗ trợ gì tiếp?"
            ),
        },
    ]


def heldout_split(destination_index: int) -> str:
    return "validation" if destination_index % 2 == 0 else "test"


def build_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for destination_index, old_destination in enumerate(DESTINATIONS):
        new_destination = DESTINATIONS[(destination_index + 7) % len(DESTINATIONS)]
        region = next(region for region in REGIONS if region != old_destination.region)
        heldout = heldout_split(destination_index)
        context = current_trip(old_destination)

        switch_templates = (
            (f"Đổi sang {new_destination.name}.", "train", False),
            (f"Giờ mình muốn đi {new_destination.name}.", "train", False),
            (
                f"Chuyển kế hoạch qua {new_destination.name} 4 ngày, 3 người, 12 triệu.",
                "train",
                True,
            ),
            (f"Thôi, chọn {new_destination.name} thay cho {old_destination.name}.", heldout, False),
        )
        for index, (prompt, split, includes_slots) in enumerate(switch_templates, start=1):
            response = (
                f"Mình đã tạo chuyến mới tại {new_destination.name}: 4 ngày, 3 người, ngân sách "
                "12 triệu. Ngân sách đã gồm chi phí di chuyển đến điểm đến chưa?"
                if includes_slots
                else (
                    f"Mình đã đổi sang điểm đến {new_destination.name} và bỏ thông tin phụ thuộc "
                    "chuyến cũ. Bạn dự định đi bao nhiêu ngày?"
                )
            )
            records.append(
                make_record(
                    f"transition-v8-destination-{old_destination.id}-{index}",
                    "destination_switch_v8",
                    [*context, {"role": "user", "content": prompt}, {"role": "assistant", "content": response}],
                    approved_at,
                    split,
                    ["new_trip_reset", "latest_destination_wins", "discard_stale_slots"],
                )
            )

        region_templates = (
            (f"Tôi muốn đi du lịch {region}.", "train"),
            (f"Đổi sang khám phá {region} nhé.", "train"),
            (f"Chuyến tiếp theo chuyển qua {region}.", heldout),
        )
        for index, (prompt, split) in enumerate(region_templates, start=1):
            response = (
                f"Mình đã tạo chuyến mới ở {region} và bỏ dữ liệu của {old_destination.name}. "
                "Bạn muốn ưu tiên biển, văn hóa, thiên nhiên hay loại trải nghiệm nào?"
            )
            records.append(
                make_record(
                    f"transition-v8-region-{old_destination.id}-{index}",
                    "region_switch_v8",
                    [*context, {"role": "user", "content": prompt}, {"role": "assistant", "content": response}],
                    approved_at,
                    split,
                    ["new_trip_reset", "region_scope_change", "discard_stale_destination"],
                )
            )

        corrections = (
            (
                "Đổi ngân sách thành 12 triệu.",
                "train",
                f"Mình vẫn giữ {old_destination.name}, 3 ngày, 2 người và cập nhật ngân sách thành 12 triệu.",
            ),
            (
                "Sửa thời lượng thành 4 ngày.",
                "train",
                f"Mình vẫn giữ chuyến {old_destination.name} cho 2 người, ngân sách 10 triệu và cập nhật thành 4 ngày.",
            ),
            (
                "Nhóm đổi thành 3 người nhé.",
                heldout,
                f"Mình vẫn giữ {old_destination.name}, 3 ngày, ngân sách 10 triệu và cập nhật nhóm thành 3 người.",
            ),
        )
        for index, (prompt, split, response) in enumerate(corrections, start=1):
            records.append(
                make_record(
                    f"transition-v8-correction-{old_destination.id}-{index}",
                    "slot_correction_v8",
                    [*context, {"role": "user", "content": prompt}, {"role": "assistant", "content": response}],
                    approved_at,
                    split,
                    ["retain_current_trip", "update_only_supplied_slot"],
                )
            )

        reset_templates = (
            ("Xóa thông tin chuyến cũ.", "train"),
            ("Mình muốn làm lại từ đầu.", "train"),
            ("Cho mình bắt đầu một chuyến khác.", "train"),
            ("Đổi kế hoạch mới hoàn toàn nhé.", heldout),
        )
        reset_response = "Mình đã xóa ngữ cảnh chuyến cũ. Bạn muốn bắt đầu chuyến mới ở đâu?"
        for index, (prompt, split) in enumerate(reset_templates, start=1):
            records.append(
                make_record(
                    f"transition-v8-reset-{old_destination.id}-{index}",
                    "explicit_reset_v8",
                    [*context, {"role": "user", "content": prompt}, {"role": "assistant", "content": reset_response}],
                    approved_at,
                    split,
                    ["explicit_context_reset", "discard_all_trip_slots"],
                )
            )

        retention_templates = (
            (
                f"Vẫn đi {old_destination.name}, mình thích ẩm thực.",
                "train",
                f"Mình giữ chuyến {old_destination.name} 3 ngày cho 2 người, ngân sách 10 triệu và thêm ưu tiên ẩm thực.",
            ),
            (
                "Cho lịch thư thả hơn nhé.",
                heldout,
                f"Mình giữ nguyên {old_destination.name}, 3 ngày, 2 người, ngân sách 10 triệu và đổi nhịp sang thư thả.",
            ),
        )
        for index, (prompt, split, response) in enumerate(retention_templates, start=1):
            records.append(
                make_record(
                    f"transition-v8-retain-{old_destination.id}-{index}",
                    "same_trip_retention_v8",
                    [*context, {"role": "user", "content": prompt}, {"role": "assistant", "content": response}],
                    approved_at,
                    split,
                    ["retain_current_trip", "preserve_unsupplied_slots"],
                )
            )
    return records


def audit_records(records: list[dict[str, Any]], challenge_records: list[dict[str, Any]]) -> None:
    expected_categories = {
        "destination_switch_v8": 140,
        "region_switch_v8": 105,
        "slot_correction_v8": 105,
        "explicit_reset_v8": 140,
        "same_trip_retention_v8": 70,
    }
    if Counter(record["category"] for record in records) != expected_categories:
        raise SystemExit("Phân bố category v8 không đúng")
    if Counter(record["split"] for record in records) != {
        "train": 385,
        "validation": 90,
        "test": 85,
    }:
        raise SystemExit("Phân bố split v8 không đúng")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise SystemExit("Dataset v8 có id trùng")
    challenge_prompts = {
        message["content"].strip().casefold()
        for record in challenge_records
        for message in record["messages"]
        if message["role"] == "user"
    }
    prompts = {
        message["content"].strip().casefold()
        for record in records
        for message in record["messages"]
        if message["role"] == "user"
    }
    if challenge_prompts & prompts:
        raise SystemExit("Dataset v8 bị rò rỉ prompt challenge")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset chuyển trạng thái TravelMate v8")
    parser.add_argument("--processed-v7-dir", type=Path, required=True)
    parser.add_argument("--challenge", type=Path, required=True)
    parser.add_argument("--reinforcement-output", type=Path, required=True)
    parser.add_argument("--processed-output-dir", type=Path, required=True)
    parser.add_argument("--approved-at", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    challenge_records, errors = load_and_validate(args.challenge, require_metadata=True)
    if errors:
        raise SystemExit("\n".join(errors))
    records = build_records(args.approved_at)
    audit_records(records, challenge_records)
    args.reinforcement_output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.reinforcement_output, records)

    old_splits: dict[str, list[dict[str, Any]]] = {}
    for split in ("train", "validation", "test"):
        old_splits[split], errors = load_and_validate(
            args.processed_v7_dir / f"{split}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))
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

    transition_test: list[dict[str, Any]] = []
    for category in expected_category_order():
        category_records = [
            record for record in new_splits["test"] if record["category"] == category
        ]
        transition_test.extend(category_records[:4])
    write_jsonl(args.processed_output_dir / "transition_test.jsonl", transition_test)

    for inherited_name in (
        "structured_validation",
        "structured_test",
        "expanded_structured_validation",
        "expanded_structured_test",
        "intent_test",
    ):
        inherited_records, errors = load_and_validate(
            args.processed_v7_dir / f"{inherited_name}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))
        write_jsonl(args.processed_output_dir / f"{inherited_name}.jsonl", inherited_records)

    manifest = {
        "version": "state_transition_v8",
        "approvedAt": args.approved_at,
        "reviewMethod": "state_transition_rule_audit_v8",
        "records": {split: len(split_records) for split, split_records in combined.items()},
        "newRecords": len(records),
        "newSplitRecords": {split: len(split_records) for split, split_records in new_splits.items()},
        "newCategories": dict(sorted(Counter(record["category"] for record in records).items())),
        "transitionTestRecords": len(transition_test),
        "destinations": len(DESTINATIONS),
        "challengePromptOverlap": 0,
        "reinforcementSha256": sha256(args.reinforcement_output),
        "limitations": [
            "Backend vẫn là nguồn sự thật cho state; model raw không tự quản lý dữ liệu lâu dài.",
            "Reset không hoàn tác giao dịch hoặc dữ liệu đã lưu ở dịch vụ khác.",
            "Tập challenge không được đưa vào train.",
        ],
    }
    (args.processed_output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def expected_category_order() -> tuple[str, ...]:
    return (
        "destination_switch_v8",
        "region_switch_v8",
        "slot_correction_v8",
        "explicit_reset_v8",
        "same_trip_retention_v8",
    )


if __name__ == "__main__":
    main()
