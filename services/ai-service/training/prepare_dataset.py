import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from training.validate_dataset import load_and_validate


def split_records(
    records: list[dict[str, Any]],
    validation_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[dict[str, Any]]]:
    """Chia theo category và giữ nguyên splitGroup nếu dataset cung cấp."""
    if records and all(record.get("splitGroup") for record in records):
        return split_records_by_group(records, validation_ratio, test_ratio, seed)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["category"]].append(record)

    splits: dict[str, list[dict[str, Any]]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    randomizer = random.Random(seed)

    for category in sorted(grouped):
        category_records = list(grouped[category])
        randomizer.shuffle(category_records)
        size = len(category_records)

        validation_size = round(size * validation_ratio)
        test_size = round(size * test_ratio)
        if size >= 3:
            validation_size = max(1, validation_size)
            test_size = max(1, test_size)
        while validation_size + test_size >= size:
            if validation_size >= test_size and validation_size > 0:
                validation_size -= 1
            elif test_size > 0:
                test_size -= 1

        splits["validation"].extend(category_records[:validation_size])
        splits["test"].extend(category_records[validation_size : validation_size + test_size])
        splits["train"].extend(category_records[validation_size + test_size :])

    for split_records_list in splits.values():
        randomizer.shuffle(split_records_list)
    return splits


def split_records_by_group(
    records: list[dict[str, Any]],
    validation_ratio: float,
    test_ratio: float,
    seed: int,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[str(record["splitGroup"])].append(record)

    group_names = sorted(grouped)
    randomizer = random.Random(seed)
    randomizer.shuffle(group_names)
    validation_size = round(len(group_names) * validation_ratio)
    test_size = round(len(group_names) * test_ratio)
    if len(group_names) >= 3:
        if validation_ratio > 0:
            validation_size = max(1, validation_size)
        if test_ratio > 0:
            test_size = max(1, test_size)
    while validation_size + test_size >= len(group_names):
        if validation_size >= test_size and validation_size > 0:
            validation_size -= 1
        elif test_size > 0:
            test_size -= 1

    validation_groups = set(group_names[:validation_size])
    test_groups = set(group_names[validation_size : validation_size + test_size])
    splits: dict[str, list[dict[str, Any]]] = {
        "train": [],
        "validation": [],
        "test": [],
    }
    for group_name, group_records in grouped.items():
        if group_name in validation_groups:
            splits["validation"].extend(group_records)
        elif group_name in test_groups:
            splits["test"].extend(group_records)
        else:
            splits["train"].extend(group_records)
    for split_records_list in splits.values():
        randomizer.shuffle(split_records_list)
    return splits


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as output_file:
        for record in records:
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def build_manifest(
    source: Path,
    splits: dict[str, list[dict[str, Any]]],
    seed: int,
) -> dict[str, Any]:
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    return {
        "source": source.name,
        "sourceSha256": source_digest,
        "seed": seed,
        "totalRecords": sum(len(records) for records in splits.values()),
        "splits": {
            name: {
                "records": len(records),
                "categories": dict(sorted(Counter(r["category"] for r in records).items())),
                "splitGroups": sorted(
                    {str(record["splitGroup"]) for record in records if record.get("splitGroup")}
                ),
            }
            for name, records in splits.items()
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Chia dataset TravelMate cố định")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--validation-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not 0 <= args.validation_ratio < 1 or not 0 <= args.test_ratio < 1:
        raise SystemExit("Tỷ lệ validation và test phải nằm trong [0, 1).")
    if args.validation_ratio + args.test_ratio >= 1:
        raise SystemExit("Tổng tỷ lệ validation và test phải nhỏ hơn 1.")

    records, errors = load_and_validate(args.dataset, require_metadata=True)
    if errors:
        for error in errors:
            print(f"[LOI] {error}")
        raise SystemExit(1)

    splits = split_records(records, args.validation_ratio, args.test_ratio, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, split in splits.items():
        write_jsonl(args.output_dir / f"{name}.jsonl", split)

    manifest = build_manifest(args.dataset, splits, args.seed)
    manifest_path = args.output_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
