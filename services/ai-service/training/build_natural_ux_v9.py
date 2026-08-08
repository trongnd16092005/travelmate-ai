import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from app.knowledge.destinations import DESTINATIONS, DestinationKnowledge
from training.build_conversation_v5 import TRAINING_SYSTEM_PROMPT
from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate

CATEGORY_ORDER = (
    "multi_slot_followup_v9",
    "correction_echo_v9",
    "retention_echo_v9",
    "clean_switch_v9",
    "natural_clarification_v9",
)


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
        "reviewMethod": "natural_ux_rule_audit_v9",
        "approvedAt": approved_at,
        "split": split,
        "messages": [{"role": "system", "content": TRAINING_SYSTEM_PROMPT}, *dialogue],
    }


def heldout_split(destination_index: int) -> str:
    return "validation" if destination_index % 2 == 0 else "test"


def destination_context(destination: DestinationKnowledge) -> list[dict[str, str]]:
    return [
        {"role": "user", "content": f"Mình muốn đi {destination.name}."},
        {"role": "assistant", "content": f"Bạn dự định đi {destination.name} bao nhiêu ngày?"},
    ]


def completed_context(destination: DestinationKnowledge) -> list[dict[str, str]]:
    return [
        {
            "role": "user",
            "content": f"Mình đi {destination.name} 3 ngày, 2 người, ngân sách 10 triệu.",
        },
        {
            "role": "assistant",
            "content": (
                f"Mình đã ghi nhận chuyến {destination.name} 3 ngày cho 2 người, ngân sách "
                "10 triệu. Bạn cần hỗ trợ gì tiếp?"
            ),
        },
    ]


def build_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for destination_index, destination in enumerate(DESTINATIONS):
        heldout = heldout_split(destination_index)
        next_destination = DESTINATIONS[(destination_index + 11) % len(DESTINATIONS)]

        multi_slot_templates = (
            ("4 ngày, 3 người, ngân sách 12 triệu.", "train", 4, 3, 12),
            ("Đi 5 hôm cho 2 người, khoảng 15 triệu nhé.", "train", 5, 2, 15),
            ("Nhóm mình 4 khách, đi 3 ngày và có 18 triệu.", "train", 3, 4, 18),
            ("Chốt 6 ngày, 2 người, tổng 20 triệu.", heldout, 6, 2, 20),
        )
        for template_index, (prompt, split, days, people, budget) in enumerate(
            multi_slot_templates, start=1
        ):
            response = (
                f"Mình đã ghi nhận chuyến {destination.name} {days} ngày cho {people} người "
                f"với ngân sách {budget} triệu. Ngân sách này đã gồm chi phí di chuyển đến "
                "điểm đến chưa?"
            )
            records.append(
                make_record(
                    f"ux-v9-multi-{destination.id}-{template_index}",
                    "multi_slot_followup_v9",
                    [
                        *destination_context(destination),
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ],
                    approved_at,
                    split,
                    ["acknowledge_all_slots", "retain_destination", "ask_next_missing_slot"],
                )
            )

        correction_templates = (
            (
                "Tăng nhóm lên 3 khách giúp mình.",
                "train",
                (
                    f"Mình vẫn giữ {destination.name}, 3 ngày và ngân sách 10 triệu; số người "
                    "đã được cập nhật thành 3."
                ),
            ),
            (
                "Điều chỉnh tổng tiền lên 14 triệu nhé.",
                "train",
                (
                    f"Mình vẫn giữ chuyến {destination.name} 3 ngày cho 2 người và cập nhật ngân "
                    "sách thành 14 triệu."
                ),
            ),
            (
                "Cho mình đổi thời lượng thành 5 ngày.",
                heldout,
                (
                    f"Mình vẫn giữ {destination.name}, 2 người và ngân sách 10 triệu; thời lượng "
                    "đã được cập nhật thành 5 ngày."
                ),
            ),
        )
        for template_index, (prompt, split, response) in enumerate(
            correction_templates, start=1
        ):
            records.append(
                make_record(
                    f"ux-v9-correction-{destination.id}-{template_index}",
                    "correction_echo_v9",
                    [
                        *completed_context(destination),
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ],
                    approved_at,
                    split,
                    ["echo_retained_state", "update_only_supplied_slot", "natural_acknowledgement"],
                )
            )

        retention_templates = (
            (
                "Giữ nguyên chuyến này nhưng giảm nhịp hoạt động nhé.",
                "train",
                (
                    f"Mình giữ nguyên chuyến {destination.name} 3 ngày cho 2 người, ngân sách "
                    "10 triệu và chuyển lịch sang nhịp thư thả hơn."
                ),
            ),
            (
                "Chuyến hiện tại thêm ưu tiên ẩm thực giúp mình.",
                heldout,
                (
                    f"Mình giữ nguyên {destination.name}, 3 ngày, 2 người, ngân sách 10 triệu và "
                    "thêm ưu tiên trải nghiệm ẩm thực."
                ),
            ),
        )
        for template_index, (prompt, split, response) in enumerate(
            retention_templates, start=1
        ):
            records.append(
                make_record(
                    f"ux-v9-retention-{destination.id}-{template_index}",
                    "retention_echo_v9",
                    [
                        *completed_context(destination),
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ],
                    approved_at,
                    split,
                    ["echo_retained_state", "preserve_unsupplied_slots", "apply_preference"],
                )
            )

        switch_templates = (
            (
                f"Bỏ kế hoạch hiện tại, chuyển điểm đến sang {next_destination.name}.",
                "train",
            ),
            (
                f"Mình muốn tạo chuyến mới ở {next_destination.name}.",
                "train",
            ),
            (
                f"Không đi {destination.name} nữa; chuyến mới chọn {next_destination.name}.",
                heldout,
            ),
        )
        for template_index, (prompt, split) in enumerate(switch_templates, start=1):
            response = (
                f"Mình đã chuyển sang chuyến mới tại {next_destination.name} và bỏ các thông "
                "tin phụ thuộc chuyến cũ. Bạn dự định đi bao nhiêu ngày?"
            )
            records.append(
                make_record(
                    f"ux-v9-switch-{destination.id}-{template_index}",
                    "clean_switch_v9",
                    [
                        *completed_context(destination),
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ],
                    approved_at,
                    split,
                    ["new_trip_reset", "never_echo_stale_slots", "ask_duration"],
                )
            )

        days = 2 + destination_index % 6
        people = 1 + destination_index % 4
        budget = 6 + destination_index
        clarification_split = (
            "validation"
            if destination_index % 7 == 0
            else "test"
            if destination_index % 7 == 1
            else "train"
        )
        prompt = (
            f"Mình muốn đi chơi {days} ngày với {people} người, khoảng {budget} triệu, "
            "tư vấn giúp."
        )
        response = (
            f"Mình đã ghi nhận chuyến {days} ngày cho {people} người với ngân sách khoảng "
            f"{budget} triệu. Bạn muốn đi điểm đến hoặc khu vực nào?"
        )
        records.append(
            make_record(
                f"ux-v9-clarification-{destination_index + 1:02d}",
                "natural_clarification_v9",
                [{"role": "user", "content": prompt}, {"role": "assistant", "content": response}],
                approved_at,
                clarification_split,
                ["acknowledge_known_slots", "ask_only_destination", "natural_clarification"],
            )
        )
    return records


def final_user_prompt(record: dict[str, Any]) -> str:
    return record["messages"][-2]["content"].strip().casefold()


def audit_records(
    records: list[dict[str, Any]],
    protected_records: list[dict[str, Any]],
) -> None:
    if Counter(record["category"] for record in records) != {
        "multi_slot_followup_v9": 140,
        "correction_echo_v9": 105,
        "retention_echo_v9": 70,
        "clean_switch_v9": 105,
        "natural_clarification_v9": 35,
    }:
        raise SystemExit("Phân bố category v9 không đúng")
    if Counter(record["split"] for record in records) != {
        "train": 305,
        "validation": 77,
        "test": 73,
    }:
        raise SystemExit("Phân bố split v9 không đúng")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise SystemExit("Dataset v9 có id trùng")
    protected_prompts = {final_user_prompt(record) for record in protected_records}
    train_prompts = {
        final_user_prompt(record) for record in records if record["split"] == "train"
    }
    overlap = protected_prompts & train_prompts
    if overlap:
        raise SystemExit(f"Train v9 trùng {len(overlap)} prompt held-out được bảo vệ")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset UX tự nhiên TravelMate v9")
    parser.add_argument("--processed-v8-dir", type=Path, required=True)
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
    transition_records, errors = load_and_validate(
        args.processed_v8_dir / "transition_test.jsonl", require_metadata=True
    )
    if errors:
        raise SystemExit("\n".join(errors))
    records = build_records(args.approved_at)
    audit_records(records, [*challenge_records, *transition_records])

    args.reinforcement_output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.reinforcement_output, records)
    new_splits = {
        split: [record for record in records if record["split"] == split]
        for split in ("train", "validation", "test")
    }

    old_train, errors = load_and_validate(
        args.processed_v8_dir / "train.jsonl", require_metadata=True
    )
    if errors:
        raise SystemExit("\n".join(errors))
    old_validation, errors = load_and_validate(
        args.processed_v8_dir / "validation.jsonl", require_metadata=True
    )
    if errors:
        raise SystemExit("\n".join(errors))
    old_test, errors = load_and_validate(
        args.processed_v8_dir / "test.jsonl", require_metadata=True
    )
    if errors:
        raise SystemExit("\n".join(errors))

    replay_rng = random.Random(42)
    replay_train = replay_rng.sample(old_train, 600)
    replay_validation = old_validation[:100]
    combined = {
        "train": [*replay_train, *new_splits["train"]],
        "validation": [*replay_validation, *new_splits["validation"]],
        "test": [*old_test, *new_splits["test"]],
    }
    args.processed_output_dir.mkdir(parents=True, exist_ok=True)
    for split, split_records in combined.items():
        write_jsonl(args.processed_output_dir / f"{split}.jsonl", split_records)

    ux_test: list[dict[str, Any]] = []
    for category in CATEGORY_ORDER:
        category_records = [
            record
            for record in new_splits["test"]
            if record["category"] == category
        ]
        ux_test.extend(category_records[:4])
    write_jsonl(args.processed_output_dir / "ux_test.jsonl", ux_test)

    for inherited_name in (
        "transition_test",
        "intent_test",
        "structured_test",
        "expanded_structured_test",
    ):
        inherited_records, errors = load_and_validate(
            args.processed_v8_dir / f"{inherited_name}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))
        write_jsonl(args.processed_output_dir / f"{inherited_name}.jsonl", inherited_records)

    manifest = {
        "version": "natural_ux_v9",
        "approvedAt": args.approved_at,
        "reviewMethod": "natural_ux_rule_audit_v9",
        "records": {split: len(split_records) for split, split_records in combined.items()},
        "newRecords": len(records),
        "newSplitRecords": {split: len(split_records) for split, split_records in new_splits.items()},
        "newCategories": dict(sorted(Counter(record["category"] for record in records).items())),
        "replayTrainRecords": len(replay_train),
        "replayValidationRecords": len(replay_validation),
        "uxTestRecords": len(ux_test),
        "protectedPromptOverlap": 0,
        "reinforcementSha256": sha256(args.reinforcement_output),
        "limitations": [
            "Backend vẫn là nguồn sự thật của state.",
            "Tập v8 transition và challenge chỉ dùng đánh giá, không đưa prompt cuối vào train v9.",
            "Continued fine-tune cần giữ learning rate thấp để hạn chế quên adapter v8.",
        ],
    }
    (args.processed_output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
