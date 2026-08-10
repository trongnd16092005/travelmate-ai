import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from app.knowledge.destinations import NATIONWIDE_DESTINATIONS, recommend_provinces
from app.prompts.itinerary import ITINERARY_SYSTEM_PROMPT
from training.build_conversation_v5 import TRAINING_SYSTEM_PROMPT
from training.build_training_v3 import structured_prompt, structured_response
from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate

OFFICIAL_CATALOG_SOURCE = (
    "https://xaydungchinhsach.chinhphu.vn/"
    "bang-danh-muc-va-ma-so-cua-34-tinh-thanh-moi-cac-don-vi-hanh-chinh-cap-xa-moi-"
    "11925070418263625.htm"
)


def make_record(
    record_id: str,
    category: str,
    messages: list[dict[str, str]],
    approved_at: str,
    split: str,
    behaviors: list[str],
    province_code: str,
) -> dict[str, Any]:
    return {
        "id": record_id,
        "category": category,
        "expectedBehaviors": behaviors,
        "reviewStatus": "approved",
        "reviewMethod": "nationwide_catalog_rule_audit_v11",
        "approvedAt": approved_at,
        "split": split,
        "provinceCode": province_code,
        "catalogSource": OFFICIAL_CATALOG_SOURCE,
        "messages": messages,
    }


def province_code(destination_id: str) -> str:
    return destination_id.split("-", 2)[1]


def build_structured_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    preferences = ("ẩm thực và văn hóa", "thiên nhiên và chụp ảnh")
    for destination in NATIONWIDE_DESTINATIONS:
        code = province_code(destination.id)
        index = 0
        for duration in (2, 3, 4):
            for people in (1, 2, 4):
                for preference in preferences:
                    index += 1
                    budget = duration * people * 1_150_000 + index * 10_000
                    records.append(
                        make_record(
                            f"nationwide-v11-structured-train-{code}-{index:02d}",
                            "nationwide_structured_itinerary_v11",
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
                            [
                                "grounded_place_ids",
                                "valid_itinerary_json",
                                "nationwide_coverage",
                            ],
                            code,
                        )
                    )
        for split, duration, people in (
            ("validation", 3, 3),
            ("validation", 5, 2),
            ("test", 2, 3),
            ("test", 5, 4),
        ):
            records.append(
                make_record(
                    f"nationwide-v11-structured-{split}-{code}-{duration}-{people}",
                    "nationwide_structured_itinerary_v11",
                    [
                        {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": structured_prompt(
                                destination,
                                duration,
                                people,
                                duration * people * 1_300_000,
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
                    ["grounded_place_ids", "valid_itinerary_json", "nationwide_coverage"],
                    code,
                )
            )
    return records


def recommendation_reply(destination: Any) -> str:
    places = ", ".join(place.name for place in destination.places)
    return (
        f"Mình đã nhận diện {destination.name} trong danh mục 34 tỉnh, thành hiện hành. "
        f"Bạn có thể cân nhắc {places}. Cho mình số ngày, số người và ngân sách để lên "
        "lịch grounded; giá, giờ mở cửa và thời tiết vẫn cần kiểm tra sát ngày đi."
    )


def build_alias_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for destination in NATIONWIDE_DESTINATIONS:
        code = province_code(destination.id)
        aliases = destination.aliases or (destination.name,)
        prompts = (
            f"Mình muốn đi {destination.name}, gợi ý điểm nổi bật.",
            f"Đi {aliases[0]} thì nên ưu tiên đâu?",
            f"Lập chuyến tới {aliases[-1]} giúp mình, chưa cần chốt giá.",
            f"Mình thích {destination.themes[0]} ở {destination.region}, tỉnh nào phù hợp?",
            f"Tên cũ {aliases[0]} hiện được TravelMate xếp vào tỉnh, thành nào?",
            f"Cho mình ba điểm grounded ở {destination.name}; đừng bịa giờ mở cửa.",
        )
        splits = ("train", "train", "train", "train", "validation", "test")
        for index, (prompt, split) in enumerate(zip(prompts, splits, strict=True), start=1):
            if index == 4:
                recommendations = recommend_provinces(
                    destination.region, (destination.themes[0],), limit=4
                )
                options = ", ".join(item.name for item in recommendations)
                response = (
                    f"Với ưu tiên {destination.themes[0]} ở {destination.region}, các lựa chọn "
                    f"grounded gồm {options}. Nếu chọn {destination.name}, mình sẽ dùng các "
                    "địa điểm trong catalog và hỏi thêm số ngày, số người, ngân sách."
                )
            else:
                response = recommendation_reply(destination)
            records.append(
                make_record(
                    f"nationwide-v11-alias-{code}-{index}",
                    "nationwide_alias_recommendation_v11",
                    [
                        {"role": "system", "content": TRAINING_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": response},
                    ],
                    approved_at,
                    split,
                    [
                        "current_province_mapping",
                        "legacy_alias_resolution",
                        "grounded_recommendation",
                        "realtime_boundary",
                    ],
                    code,
                )
            )
    return records


def final_user_prompt(record: dict[str, Any]) -> str:
    return record["messages"][-2]["content"].strip().casefold()


def audit_records(records: list[dict[str, Any]], protected_records: list[dict[str, Any]]) -> None:
    if len(NATIONWIDE_DESTINATIONS) != 34:
        raise SystemExit("Catalog v11 phải có đúng 34 tỉnh, thành")
    if Counter(record["category"] for record in records) != {
        "nationwide_structured_itinerary_v11": 748,
        "nationwide_alias_recommendation_v11": 204,
    }:
        raise SystemExit("Phân bố category v11 không đúng")
    if Counter(record["split"] for record in records) != {
        "train": 748,
        "validation": 102,
        "test": 102,
    }:
        raise SystemExit("Phân bố split v11 không đúng")
    if len({record["id"] for record in records}) != len(records):
        raise SystemExit("Dataset v11 có id trùng")
    coverage = Counter(record["provinceCode"] for record in records)
    if len(coverage) != 34 or set(coverage.values()) != {28}:
        raise SystemExit(f"Độ phủ tỉnh, thành v11 không cân bằng: {coverage}")
    train_prompts = {
        final_user_prompt(record) for record in records if record["split"] == "train"
    }
    heldout_prompts = {
        final_user_prompt(record) for record in records if record["split"] != "train"
    }
    protected_prompts = {final_user_prompt(record) for record in protected_records}
    overlap = train_prompts & (heldout_prompts | protected_prompts)
    if overlap:
        raise SystemExit(f"Train v11 trùng {len(overlap)} prompt held-out được bảo vệ")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset phủ 34 tỉnh, thành cho v11")
    parser.add_argument("--processed-v10-dir", type=Path, required=True)
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
    records = [*build_structured_records(args.approved_at), *build_alias_records(args.approved_at)]

    protected_records = list(challenge_records)
    for protected_name in (
        "reasoning_test",
        "ux_test",
        "transition_test",
        "intent_test",
        "structured_test",
        "expanded_structured_test",
    ):
        inherited, errors = load_and_validate(
            args.processed_v10_dir / f"{protected_name}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))
        protected_records.extend(inherited)
    audit_records(records, protected_records)

    args.reinforcement_output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.reinforcement_output, records)
    new_splits = {
        split: [record for record in records if record["split"] == split]
        for split in ("train", "validation", "test")
    }
    old_splits: dict[str, list[dict[str, Any]]] = {}
    for split in ("train", "validation", "test"):
        old_splits[split], errors = load_and_validate(
            args.processed_v10_dir / f"{split}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))

    replay_rng = random.Random(44)
    replay_train = replay_rng.sample(old_splits["train"], min(700, len(old_splits["train"])))
    replay_validation = old_splits["validation"][:120]
    combined = {
        "train": [*replay_train, *new_splits["train"]],
        "validation": [*replay_validation, *new_splits["validation"]],
        "test": [*old_splits["test"], *new_splits["test"]],
    }
    args.processed_output_dir.mkdir(parents=True, exist_ok=True)
    for split, split_records in combined.items():
        write_jsonl(args.processed_output_dir / f"{split}.jsonl", split_records)
    write_jsonl(args.processed_output_dir / "nationwide_test.jsonl", new_splits["test"])
    write_jsonl(args.processed_output_dir / "nationwide_validation.jsonl", new_splits["validation"])
    alias_test = [
        record
        for record in new_splits["test"]
        if record["category"] == "nationwide_alias_recommendation_v11"
    ]
    write_jsonl(args.processed_output_dir / "nationwide_alias_test.jsonl", alias_test)
    structured_smoke: list[dict[str, Any]] = []
    seen_provinces: set[str] = set()
    for record in new_splits["test"]:
        if record["category"] != "nationwide_structured_itinerary_v11":
            continue
        if record["provinceCode"] in seen_provinces:
            continue
        seen_provinces.add(record["provinceCode"])
        structured_smoke.append(record)
    write_jsonl(
        args.processed_output_dir / "nationwide_structured_smoke_test.jsonl",
        structured_smoke,
    )

    for inherited_name in (
        "reasoning_test",
        "ux_test",
        "transition_test",
        "intent_test",
        "structured_test",
        "expanded_structured_test",
    ):
        inherited_records, errors = load_and_validate(
            args.processed_v10_dir / f"{inherited_name}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))
        write_jsonl(
            args.processed_output_dir / f"{inherited_name}.jsonl", inherited_records
        )

    manifest = {
        "version": "nationwide_v11",
        "approvedAt": args.approved_at,
        "reviewMethod": "nationwide_catalog_rule_audit_v11",
        "officialCatalogSource": OFFICIAL_CATALOG_SOURCE,
        "provinceLevelUnits": len(NATIONWIDE_DESTINATIONS),
        "records": {split: len(items) for split, items in combined.items()},
        "newRecords": len(records),
        "newSplitRecords": {split: len(items) for split, items in new_splits.items()},
        "nationwideStructuredSmokeRecords": len(structured_smoke),
        "nationwideAliasTestRecords": len(alias_test),
        "newCategories": dict(sorted(Counter(item["category"] for item in records).items())),
        "replayTrainRecords": len(replay_train),
        "replayValidationRecords": len(replay_validation),
        "protectedPromptOverlap": 0,
        "reinforcementSha256": sha256(args.reinforcement_output),
        "limitations": [
            "Catalog theo 34 đơn vị hành chính cấp tỉnh có hiệu lực từ 01/07/2025.",
            "Alias tỉnh cũ dùng để hiểu câu hỏi, không khẳng định địa giới ngoài catalog.",
            "Giá, giờ mở cửa, thời tiết và tình trạng dịch vụ vẫn là dữ liệu realtime.",
            "Candidate chỉ được promote sau khi vượt toàn bộ regression v10 và nationwide held-out.",
        ],
    }
    (args.processed_output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
