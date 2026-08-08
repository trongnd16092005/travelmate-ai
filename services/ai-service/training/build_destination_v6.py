import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.knowledge.destinations import (
    DESTINATIONS,
    recommend_destinations,
)
from app.prompts.itinerary import ITINERARY_SYSTEM_PROMPT
from training.build_conversation_v5 import TRAINING_SYSTEM_PROMPT
from training.build_training_v3 import structured_prompt, structured_response
from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate

EXPANDED_DESTINATION_NAMES = {
    "Cát Bà",
    "Cô Tô",
    "Quan Lạn",
    "Móng Cái",
    "Đồ Sơn",
    "Mộc Châu",
    "Mai Châu",
    "Tam Đảo",
    "Sầm Sơn",
    "Cửa Lò",
    "Phú Yên",
    "Lý Sơn",
    "Côn Đảo",
    "Châu Đốc",
    "Bến Tre",
}


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
        "reviewMethod": "expanded_catalog_rule_audit_v6",
        "approvedAt": approved_at,
        "split": split,
        "messages": messages,
    }


def build_structured_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    destinations = [
        destination
        for destination in DESTINATIONS
        if destination.name in EXPANDED_DESTINATION_NAMES
    ]
    preferences = ("ẩm thực và tham quan", "thiên nhiên và chụp ảnh")
    for destination in destinations:
        index = 0
        for duration in (2, 3, 4, 5):
            for people in (1, 2, 4):
                for preference in preferences:
                    index += 1
                    budget = duration * people * 1_100_000 + index * 10_000
                    records.append(
                        make_record(
                            f"structured-v6-train-{destination.id}-{index:02d}",
                            "expanded_structured_itinerary_v6",
                            [
                                {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
                                {
                                    "role": "user",
                                    "content": structured_prompt(
                                        destination,
                                        duration,
                                        people,
                                        budget,
                                        preference,
                                    ),
                                },
                                {
                                    "role": "assistant",
                                    "content": structured_response(destination, duration),
                                },
                            ],
                            approved_at,
                            "train",
                            ["grounded_place_ids", "valid_itinerary_json", "expanded_catalog"],
                        )
                    )

        for split, duration, people in (
            ("validation", 3, 3),
            ("validation", 5, 2),
            ("test", 2, 3),
            ("test", 4, 2),
        ):
            records.append(
                make_record(
                    f"structured-v6-{split}-{destination.id}-{duration}-{people}",
                    "expanded_structured_itinerary_v6",
                    [
                        {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": structured_prompt(
                                destination,
                                duration,
                                people,
                                duration * people * 1_250_000,
                                "đi thư thả và ưu tiên trải nghiệm đặc trưng",
                            ),
                        },
                        {
                            "role": "assistant",
                            "content": structured_response(destination, duration),
                        },
                    ],
                    approved_at,
                    split,
                    ["grounded_place_ids", "valid_itinerary_json", "expanded_catalog"],
                )
            )
    return records


def _recommendation_reply(region: str, theme: str) -> str:
    recommendations = recommend_destinations(region, (theme,), limit=5)
    options = "; ".join(
        f"{destination.name} ({', '.join(place.name for place in destination.places[:2])})"
        for destination in recommendations
    )
    return (
        f"Với ưu tiên {theme} ở {region}, mình gợi ý: {options}. "
        "Bạn chọn một nơi, mình sẽ lên lịch và phân bổ ngân sách theo số ngày."
    )


def build_recommendation_records(approved_at: str) -> list[dict[str, Any]]:
    pairs = sorted(
        {(destination.region, theme) for destination in DESTINATIONS for theme in destination.themes}
    )
    records: list[dict[str, Any]] = []
    for pair_index, (region, theme) in enumerate(pairs):
        response = _recommendation_reply(region, theme)
        dialogues = (
            [
                {"role": "user", "content": f"Gợi ý điểm đến ở {region}, mình thích {theme}."},
                {"role": "assistant", "content": response},
            ],
            [
                {"role": "user", "content": f"Tôi cần đi du lịch ở {region}."},
                {
                    "role": "assistant",
                    "content": "Bạn muốn ưu tiên biển, văn hóa hay thiên nhiên?",
                },
                {"role": "user", "content": theme},
                {"role": "assistant", "content": response},
            ],
            [
                {"role": "user", "content": f"Muốn tìm nơi ở {region}."},
                {
                    "role": "assistant",
                    "content": "Bạn thích loại trải nghiệm nào để mình lọc đúng điểm đến?",
                },
                {"role": "user", "content": f"Ưu tiên {theme}."},
                {"role": "assistant", "content": response},
            ],
            [
                {"role": "user", "content": f"Tôi muốn đi {region}, thiên về {theme}."},
                {"role": "assistant", "content": response},
                {"role": "user", "content": "Gợi ý giúp tôi."},
                {"role": "assistant", "content": response},
            ],
        )
        for dialogue_index, dialogue in enumerate(dialogues, start=1):
            if dialogue_index <= 3:
                split = "train"
            else:
                split = "validation" if pair_index % 2 == 0 else "test"
            records.append(
                make_record(
                    f"recommendation-v6-{pair_index + 1:02d}-{dialogue_index}",
                    "regional_theme_recommendation_v6",
                    [{"role": "system", "content": TRAINING_SYSTEM_PROMPT}, *dialogue],
                    approved_at,
                    split,
                    ["region_theme_grounding", "catalog_recommendation", "context_retention"],
                )
            )
    return records


def audit_records(records: list[dict[str, Any]], challenge_records: list[dict[str, Any]]) -> None:
    counts = Counter(record["category"] for record in records)
    if counts["expanded_structured_itinerary_v6"] != 420:
        raise SystemExit(f"Số mẫu structured v6 không đúng: {counts}")
    if counts["regional_theme_recommendation_v6"] < 80:
        raise SystemExit(f"Độ phủ region-theme v6 chưa đủ: {counts}")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise SystemExit("Dataset v6 có id trùng")
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
        raise SystemExit("Dataset v6 bị rò rỉ prompt challenge")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset mở rộng điểm đến TravelMate v6")
    parser.add_argument("--processed-v5-dir", type=Path, required=True)
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
    records = [*build_structured_records(args.approved_at), *build_recommendation_records(args.approved_at)]
    audit_records(records, challenge_records)
    args.reinforcement_output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.reinforcement_output, records)

    old_splits: dict[str, list[dict[str, Any]]] = {}
    for split in ("train", "validation", "test"):
        old_splits[split], errors = load_and_validate(
            args.processed_v5_dir / f"{split}.jsonl", require_metadata=True
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

    for structured_name, split in (("structured_validation", "validation"), ("structured_test", "test")):
        old_structured, errors = load_and_validate(
            args.processed_v5_dir / f"{structured_name}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))
        new_structured = [
            record
            for record in new_splits[split]
            if record["category"] == "expanded_structured_itinerary_v6"
        ]
        write_jsonl(
            args.processed_output_dir / f"{structured_name}.jsonl",
            [*old_structured, *new_structured],
        )
        write_jsonl(
            args.processed_output_dir / f"expanded_{structured_name}.jsonl",
            new_structured,
        )

    manifest = {
        "version": "expanded_destinations_v6",
        "approvedAt": args.approved_at,
        "reviewMethod": "expanded_catalog_rule_audit_v6",
        "records": {split: len(split_records) for split, split_records in combined.items()},
        "newRecords": len(records),
        "newSplitRecords": {split: len(split_records) for split, split_records in new_splits.items()},
        "newCategories": dict(sorted(Counter(record["category"] for record in records).items())),
        "destinations": len(DESTINATIONS),
        "newDestinations": len(EXPANDED_DESTINATION_NAMES),
        "challengePromptOverlap": 0,
        "reinforcementSha256": sha256(args.reinforcement_output),
        "limitations": [
            "Danh mục là tập grounding đóng và không thay thế dữ liệu thời gian thực.",
            "Giá, giờ mở cửa, thời tiết và tình trạng dịch vụ phải được kiểm tra sát ngày đi.",
            "Dữ liệu sinh theo quy tắc cần tiếp tục được review bằng hội thoại thực tế.",
        ],
    }
    (args.processed_output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
