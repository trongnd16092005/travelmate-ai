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


def format_vnd(value: int) -> str:
    return f"{value:,}".replace(",", ".") + " VND"


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
        "reviewMethod": "intent_execution_rule_audit_v7",
        "approvedAt": approved_at,
        "split": split,
        "messages": [{"role": "system", "content": TRAINING_SYSTEM_PROMPT}, *dialogue],
    }


def itinerary_reply(destination: DestinationKnowledge, duration: int, people: int) -> str:
    lines = [f"Lịch gợi ý {duration} ngày tại {destination.name} cho {people} người:"]
    for day in range(1, duration + 1):
        place = destination.places[(day - 1) % len(destination.places)]
        food = destination.foods[(day - 1) % len(destination.foods)]
        lines.append(
            f"Ngày {day}: sáng tham quan {place.name}; trưa thử {food}; "
            "chiều nghỉ hoặc khám phá khu vực lân cận; tối tự do."
        )
    lines.append(
        "Hãy kiểm tra thời tiết, giờ hoạt động và thời gian di chuyển thực tế trước khi chốt."
    )
    return "\n".join(lines)


def budget_reply(destination: DestinationKnowledge, total: int, people: int) -> str:
    amounts = {
        "Lưu trú 35%": total * 35 // 100,
        "Ăn uống 25%": total * 25 // 100,
        "Di chuyển toàn chuyến 20%": total * 20 // 100,
        "Tham quan 15%": total * 15 // 100,
    }
    reserve = total - sum(amounts.values())
    lines = [
        f"Phân bổ tham khảo {format_vnd(total)} cho chuyến {destination.name} của {people} người:"
    ]
    lines.extend(f"• {label}: {format_vnd(value)}." for label, value in amounts.items())
    lines.append(f"• Dự phòng 5%: {format_vnd(reserve)}.")
    lines.append("Đây là khung dự toán; hãy kiểm tra giá thực tế trước khi đặt dịch vụ.")
    return "\n".join(lines)


def checklist_reply(destination: DestinationKnowledge, duration: int) -> str:
    return (
        f"Checklist cho {destination.name} trong {duration} ngày:\n"
        "• Giấy tờ: CCCD/hộ chiếu, vé và xác nhận nơi ở.\n"
        "• Tài chính: tiền mặt dự phòng, thẻ và hạn mức chi tiêu.\n"
        "• Cá nhân: thuốc đang dùng, đồ vệ sinh, sạc và pin dự phòng.\n"
        "• Trang phục: quần áo theo thời tiết, giày dễ đi và đồ chống nắng/mưa.\n"
        "• Trước khi đi: kiểm tra thời tiết, giờ hoạt động, phương tiện và cảnh báo địa phương."
    )


def complete_context(
    destination: DestinationKnowledge,
    duration: int,
    people: int,
    budget: int,
) -> list[dict[str, str]]:
    return [
        {"role": "user", "content": f"Mình muốn đi {destination.name}."},
        {"role": "assistant", "content": "Bạn dự định đi bao nhiêu ngày?"},
        {
            "role": "user",
            "content": f"{duration} ngày, {people} người với mức {budget // 1_000_000} triệu.",
        },
        {
            "role": "assistant",
            "content": "Ngân sách này đã gồm chi phí di chuyển đến điểm đến chưa?",
        },
        {"role": "user", "content": "Rồi."},
        {
            "role": "assistant",
            "content": "Bạn muốn lập lịch trình, phân bổ ngân sách hay chuẩn bị checklist?",
        },
    ]


def heldout_split(destination_index: int) -> str:
    return "validation" if destination_index % 2 == 0 else "test"


def build_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for destination_index, destination in enumerate(DESTINATIONS):
        split = heldout_split(destination_index)
        contexts = {
            "small": complete_context(destination, 2, 2, 8_000_000),
            "demo": complete_context(destination, 3, 2, 10_000_000),
            "group": complete_context(destination, 4, 4, 20_000_000),
        }

        itinerary_prompts = (
            ("small", "Lập lịch luôn giúp mình.", "train"),
            ("demo", "Hỗ trợ lập lịch đi.", "train"),
            ("group", "Cho mình lịch trình cụ thể.", "train"),
            ("demo", "Theo điểm đến nhé.", split),
        )
        for index, (context_key, prompt, record_split) in enumerate(itinerary_prompts, start=1):
            duration, people = ((2, 2) if context_key == "small" else (4, 4) if context_key == "group" else (3, 2))
            records.append(
                make_record(
                    f"intent-v7-itinerary-{destination.id}-{index}",
                    "itinerary_execution_v7",
                    [
                        *contexts[context_key],
                        {"role": "user", "content": prompt},
                        {
                            "role": "assistant",
                            "content": itinerary_reply(destination, duration, people),
                        },
                    ],
                    approved_at,
                    record_split,
                    ["execute_current_intent", "grounded_itinerary", "no_repeated_question"],
                )
            )

        budget_prompts = (
            ("small", "Chia ngân sách cụ thể giúp mình.", 8_000_000, 2, "train"),
            ("demo", "Phân bổ ngân sách giúp tôi.", 10_000_000, 2, "train"),
            ("group", "Ngân sách nên chia thế nào?", 20_000_000, 4, split),
        )
        for index, (context_key, prompt, budget, people, record_split) in enumerate(
            budget_prompts, start=1
        ):
            records.append(
                make_record(
                    f"intent-v7-budget-{destination.id}-{index}",
                    "budget_execution_v7",
                    [
                        *contexts[context_key],
                        {"role": "user", "content": prompt},
                        {
                            "role": "assistant",
                            "content": budget_reply(destination, budget, people),
                        },
                    ],
                    approved_at,
                    record_split,
                    ["execute_current_intent", "budget_allocation", "no_repeated_question"],
                )
            )

        checklist_prompts = (
            ("small", "Làm checklist luôn nhé.", 2, "train"),
            ("demo", "Cần chuẩn bị những gì?", 3, "train"),
            ("group", "Cho mình danh sách đồ cần mang.", 4, split),
        )
        for index, (context_key, prompt, duration, record_split) in enumerate(
            checklist_prompts, start=1
        ):
            records.append(
                make_record(
                    f"intent-v7-checklist-{destination.id}-{index}",
                    "checklist_execution_v7",
                    [
                        *contexts[context_key],
                        {"role": "user", "content": prompt},
                        {
                            "role": "assistant",
                            "content": checklist_reply(destination, duration),
                        },
                    ],
                    approved_at,
                    record_split,
                    ["execute_current_intent", "contextual_checklist", "no_repeated_question"],
                )
            )

        compact_itinerary = itinerary_reply(destination, 2, 2)
        compound_response = "\n\n".join(
            (
                compact_itinerary,
                budget_reply(destination, 8_000_000, 2),
                checklist_reply(destination, 2),
            )
        )
        for index, (prompt, record_split) in enumerate(
            (
                ("Lập lịch, chia ngân sách và làm checklist luôn.", "train"),
                ("Cho mình đủ lịch trình, chi phí và đồ cần chuẩn bị.", split),
            ),
            start=1,
        ):
            records.append(
                make_record(
                    f"intent-v7-compound-{destination.id}-{index}",
                    "compound_execution_v7",
                    [
                        *contexts["small"],
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": compound_response},
                    ],
                    approved_at,
                    record_split,
                    ["execute_multiple_intents", "complete_response", "no_repeated_question"],
                )
            )
    return records


def audit_records(records: list[dict[str, Any]], challenge_records: list[dict[str, Any]]) -> None:
    expected = {
        "itinerary_execution_v7": 140,
        "budget_execution_v7": 105,
        "checklist_execution_v7": 105,
        "compound_execution_v7": 70,
    }
    if Counter(record["category"] for record in records) != expected:
        raise SystemExit("Phân bố category v7 không đúng")
    if Counter(record["split"] for record in records) != {
        "train": 280,
        "validation": 72,
        "test": 68,
    }:
        raise SystemExit("Phân bố split v7 không đúng")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise SystemExit("Dataset v7 có id trùng")
    challenge_prompts = {
        message["content"].strip().casefold()
        for record in challenge_records
        for message in record["messages"]
        if message["role"] == "user"
    }
    v7_prompts = {
        message["content"].strip().casefold()
        for record in records
        for message in record["messages"]
        if message["role"] == "user"
    }
    if challenge_prompts & v7_prompts:
        raise SystemExit("Dataset v7 bị rò rỉ prompt challenge")
    for record in records:
        final_response = record["messages"][-1]["content"]
        if final_response.count("?") > 0:
            raise SystemExit(f"{record['id']}: phản hồi thực thi vẫn đặt câu hỏi")
        if record["category"] == "itinerary_execution_v7" and "Ngày 1:" not in final_response:
            raise SystemExit(f"{record['id']}: thiếu lịch cụ thể")
        if record["category"] == "budget_execution_v7" and "Lưu trú 35%" not in final_response:
            raise SystemExit(f"{record['id']}: thiếu phân bổ cụ thể")
        if record["category"] == "checklist_execution_v7" and "Giấy tờ" not in final_response:
            raise SystemExit(f"{record['id']}: thiếu checklist cụ thể")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset thực thi intent TravelMate v7")
    parser.add_argument("--processed-v6-dir", type=Path, required=True)
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
            args.processed_v6_dir / f"{split}.jsonl", require_metadata=True
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
    intent_eval: list[dict[str, Any]] = []
    for category in (
        "itinerary_execution_v7",
        "budget_execution_v7",
        "checklist_execution_v7",
        "compound_execution_v7",
    ):
        category_records = [
            record for record in new_splits["test"] if record["category"] == category
        ]
        intent_eval.extend(category_records[:4])
    write_jsonl(args.processed_output_dir / "intent_test.jsonl", intent_eval)
    for structured_name in (
        "structured_validation",
        "structured_test",
        "expanded_structured_validation",
        "expanded_structured_test",
    ):
        structured_records, errors = load_and_validate(
            args.processed_v6_dir / f"{structured_name}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))
        write_jsonl(args.processed_output_dir / f"{structured_name}.jsonl", structured_records)

    manifest = {
        "version": "intent_execution_v7",
        "approvedAt": args.approved_at,
        "reviewMethod": "intent_execution_rule_audit_v7",
        "records": {split: len(split_records) for split, split_records in combined.items()},
        "newRecords": len(records),
        "newSplitRecords": {split: len(split_records) for split, split_records in new_splits.items()},
        "newCategories": dict(sorted(Counter(record["category"] for record in records).items())),
        "intentTestRecords": len(intent_eval),
        "destinations": len(DESTINATIONS),
        "challengePromptOverlap": 0,
        "reinforcementSha256": sha256(args.reinforcement_output),
        "limitations": [
            "Mẫu dự toán là tỷ lệ tham khảo, không phải giá thời gian thực.",
            "Lịch chat là bản tóm tắt; lịch lưu chính thức vẫn phải qua itinerary validator.",
            "Tập challenge không được đưa vào train.",
        ],
    }
    (args.processed_output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
