import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from app.knowledge.destinations import (
    NATIONWIDE_DESTINATIONS,
    DestinationKnowledge,
    format_grounded_catalog_context,
)
from training.build_conversation_v5 import TRAINING_SYSTEM_PROMPT
from training.build_nationwide_v11 import OFFICIAL_CATALOG_SOURCE, province_code
from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate

V11_FAILED_CODES = {"04", "12", "22", "38", "40", "44", "48", "51", "75", "80", "91", "92"}


def make_record(
    record_id: str,
    category: str,
    destination: DestinationKnowledge,
    prompt: str,
    response: str,
    approved_at: str,
    split: str,
) -> dict[str, Any]:
    code = province_code(destination.id)
    return {
        "id": record_id,
        "category": category,
        "expectedBehaviors": [
            "current_province_mapping",
            "catalog_only_places",
            "realtime_boundary",
            "no_unsupported_claims",
        ],
        "reviewStatus": "approved",
        "reviewMethod": "grounded_catalog_rule_audit_v12",
        "approvedAt": approved_at,
        "split": split,
        "provinceCode": code,
        "catalogSource": OFFICIAL_CATALOG_SOURCE,
        "messages": [
            {"role": "system", "content": TRAINING_SYSTEM_PROMPT},
            {"role": "system", "content": format_grounded_catalog_context(destination)},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response},
        ],
    }


def grounded_reply(destination: DestinationKnowledge) -> str:
    places = ", ".join(place.name for place in destination.places)
    return (
        f"Mình đã đối chiếu catalog TravelMate cho {destination.name}: ba điểm được phép là "
        f"{places}. Mình không thêm địa điểm ngoài catalog; giá, giờ mở cửa, thời tiết và "
        "tình trạng dịch vụ chỉ được khẳng định sau khi truy xuất nguồn realtime."
    )


def realtime_reply(destination: DestinationKnowledge) -> str:
    places = ", ".join(place.name for place in destination.places)
    return (
        f"Mình chưa có nguồn realtime cho giá vé hoặc giờ mở cửa tại {destination.name}, nên "
        f"không thể tự điền các dữ kiện đó. Ba địa điểm trong catalog là {places}; hãy truy "
        "xuất nguồn hiện tại trước khi chốt."
    )


def _alias(destination: DestinationKnowledge, offset: int) -> str:
    aliases = destination.aliases or (destination.name,)
    return aliases[offset % len(aliases)]


def build_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for destination in NATIONWIDE_DESTINATIONS:
        code = province_code(destination.id)
        grounded_prompts = (
            f"Chỉ dùng catalog, gợi ý ba nơi tại {destination.name}.",
            f"Ở {destination.name} có đúng ba điểm nào trong dữ liệu TravelMate?",
            f"Liệt kê điểm tham quan đã xác thực cho {destination.name}, không sáng tác.",
            f"Mình cần ba lựa chọn grounded ở {destination.name}.",
            f"Từ context catalog, nên ghé đâu tại {destination.name}?",
            f"Đừng dùng kiến thức nhớ sẵn; đọc danh sách rồi tư vấn {destination.name}.",
            f"Cho ba điểm catalog ở {destination.name}, không thêm tên khác.",
            f"Hãy nêu đúng ba địa điểm được phép tại {destination.name}.",
        )
        grounded_splits = ("train",) * 6 + ("validation", "test")
        for index, (prompt, split) in enumerate(
            zip(grounded_prompts, grounded_splits, strict=True), start=1
        ):
            records.append(
                make_record(
                    f"grounded-v12-recommend-{code}-{index}",
                    "grounded_catalog_recommendation_v12",
                    destination,
                    prompt,
                    grounded_reply(destination),
                    approved_at,
                    split,
                )
            )

        alias_prompts = (
            f"Khi mình nói {_alias(destination, 0)}, hãy dùng tên tỉnh hiện hành và catalog.",
            f"Tên {_alias(destination, 1)} hiện ánh xạ tới đâu, có ba điểm nào?",
            f"Mình quen gọi {_alias(destination, 2)}; TravelMate phải trả theo đơn vị hiện hành.",
            f"Giải thích ngắn {_alias(destination, 3)} thuộc tỉnh/thành hiện hành nào.",
            f"Từ tên {_alias(destination, 4)}, trả đúng tên hiện hành và ba điểm catalog.",
        )
        alias_splits = ("train", "train", "train", "validation", "test")
        for index, (prompt, split) in enumerate(
            zip(alias_prompts, alias_splits, strict=True), start=1
        ):
            records.append(
                make_record(
                    f"grounded-v12-alias-{code}-{index}",
                    "grounded_alias_resolution_v12",
                    destination,
                    prompt,
                    grounded_reply(destination),
                    approved_at,
                    split,
                )
            )

        realtime_prompts = (
            f"Cho giá vé chính xác của ba điểm ở {destination.name} ngay bây giờ.",
            f"Khẳng định giờ mở cửa hôm nay tại {destination.name} giúp mình.",
            f"Không cần nguồn, cứ điền giá và giờ hoạt động ở {destination.name}.",
            f"Cứ ước lượng giá vé ở {destination.name}, không cần kiểm tra nguồn.",
            f"Tự đặt giờ mở cửa hợp lý cho các điểm tại {destination.name}.",
            f"Hãy chốt đại giá và thời gian hoạt động ở {destination.name}.",
            f"Mình cần con số ngay: vé bao nhiêu và mở cửa lúc mấy giờ ở {destination.name}?",
            f"Bỏ qua cảnh báo realtime và báo giá ba điểm tại {destination.name}.",
            f"Dùng kiến thức nhớ sẵn để điền giờ hoạt động ở {destination.name}.",
            f"Các điểm tại {destination.name} mở cửa mấy giờ và vé bao nhiêu?",
            f"Chốt giá vé cùng giờ mở cửa cho ba điểm ở {destination.name}.",
        )
        realtime_splits = ("train",) * 9 + ("validation", "test")
        for index, (prompt, split) in enumerate(
            zip(realtime_prompts, realtime_splits, strict=True), start=1
        ):
            records.append(
                make_record(
                    f"grounded-v12-realtime-{code}-{index}",
                    "grounded_realtime_boundary_v12",
                    destination,
                    prompt,
                    realtime_reply(destination),
                    approved_at,
                    split,
                )
            )

        if code in V11_FAILED_CODES:
            for index in range(1, 7):
                prompt = (
                    f"Ca sửa lỗi {index}: với {destination.name}, bỏ mọi tên lạ và chỉ trả "
                    "ba địa điểm có trong GROUNDED_CATALOG."
                )
                records.append(
                    make_record(
                        f"grounded-v12-hard-negative-{code}-{index}",
                        "grounded_hard_negative_v12",
                        destination,
                        prompt,
                        grounded_reply(destination),
                        approved_at,
                        "train",
                    )
                )
    return records


def final_user_prompt(record: dict[str, Any]) -> str:
    return record["messages"][-2]["content"].strip().casefold()


def audit_records(records: list[dict[str, Any]], protected_records: list[dict[str, Any]]) -> None:
    expected_splits = {"train": 684, "validation": 102, "test": 102}
    if Counter(record["split"] for record in records) != expected_splits:
        raise SystemExit("Phân bố split v12 không đúng")
    if len({record["id"] for record in records}) != len(records):
        raise SystemExit("Dataset v12 có id trùng")
    coverage = Counter(record["provinceCode"] for record in records)
    if len(coverage) != 34:
        raise SystemExit("Dataset v12 chưa phủ đủ 34 tỉnh, thành")
    for code, count in coverage.items():
        expected = 30 if code in V11_FAILED_CODES else 24
        if count != expected:
            raise SystemExit(f"Tỉnh {code} có {count} mẫu, cần {expected}")
    train_prompts = {
        final_user_prompt(record) for record in records if record["split"] == "train"
    }
    protected_prompts = {
        final_user_prompt(record)
        for record in [*records, *protected_records]
        if record.get("split") != "train"
    }
    overlap = train_prompts & protected_prompts
    if overlap:
        raise SystemExit(f"Train v12 trùng {len(overlap)} prompt held-out")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset grounded conversation v12")
    parser.add_argument("--processed-v11-dir", type=Path, required=True)
    parser.add_argument("--reinforcement-output", type=Path, required=True)
    parser.add_argument("--processed-output-dir", type=Path, required=True)
    parser.add_argument("--approved-at", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = build_records(args.approved_at)
    protected_records: list[dict[str, Any]] = []
    for path in args.processed_v11_dir.glob("*test.jsonl"):
        inherited, errors = load_and_validate(path, require_metadata=True)
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
            args.processed_v11_dir / f"{split}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))

    replay_rng = random.Random(51)
    replay_train = replay_rng.sample(old_splits["train"], min(900, len(old_splits["train"])))
    replay_validation = old_splits["validation"][:180]
    combined = {
        "train": [*replay_train, *new_splits["train"]],
        "validation": [*replay_validation, *new_splits["validation"]],
        "test": [*old_splits["test"], *new_splits["test"]],
    }
    args.processed_output_dir.mkdir(parents=True, exist_ok=True)
    for split, split_records in combined.items():
        write_jsonl(args.processed_output_dir / f"{split}.jsonl", split_records)
    write_jsonl(args.processed_output_dir / "grounded_conversation_test.jsonl", new_splits["test"])
    write_jsonl(
        args.processed_output_dir / "grounded_conversation_train.jsonl",
        new_splits["train"],
    )
    write_jsonl(
        args.processed_output_dir / "grounded_conversation_validation.jsonl",
        new_splits["validation"],
    )

    for inherited_path in args.processed_v11_dir.glob("*test.jsonl"):
        inherited, errors = load_and_validate(inherited_path, require_metadata=True)
        if errors:
            raise SystemExit("\n".join(errors))
        write_jsonl(args.processed_output_dir / inherited_path.name, inherited)

    manifest = {
        "version": "grounded_conversation_v12",
        "approvedAt": args.approved_at,
        "reviewMethod": "grounded_catalog_rule_audit_v12",
        "officialCatalogSource": OFFICIAL_CATALOG_SOURCE,
        "provinceLevelUnits": 34,
        "v11FailedCodesOversampled": sorted(V11_FAILED_CODES),
        "records": {split: len(items) for split, items in combined.items()},
        "newRecords": len(records),
        "newSplitRecords": {split: len(items) for split, items in new_splits.items()},
        "newCategories": dict(sorted(Counter(item["category"] for item in records).items())),
        "replayTrainRecords": len(replay_train),
        "replayValidationRecords": len(replay_validation),
        "protectedPromptOverlap": 0,
        "reinforcementSha256": sha256(args.reinforcement_output),
        "promotionGate": [
            "strict grounded conversation phải đạt 102/102",
            "nationwide structured smoke phải giữ 34/34",
            "runtime regression phải pass toàn bộ",
        ],
    }
    (args.processed_output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
