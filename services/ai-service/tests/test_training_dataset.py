import json
from pathlib import Path

from training.prepare_dataset import build_manifest, split_records, write_jsonl
from training.validate_dataset import load_and_validate, validate_record


def make_record(record_id: str, category: str) -> dict:
    return {
        "id": record_id,
        "category": category,
        "messages": [
            {"role": "user", "content": f"Câu hỏi {record_id}?"},
            {"role": "assistant", "content": f"Trả lời {record_id}."},
        ],
    }


def test_validate_record_requires_training_metadata() -> None:
    record = {
        "messages": [
            {"role": "user", "content": "Tôi nên đi đâu?"},
            {"role": "assistant", "content": "Bạn thích biển hay núi?"},
        ]
    }

    errors = validate_record(record, line_number=1, require_metadata=True)

    assert "id phải là chuỗi không rỗng" in errors[0]
    assert "category phải là chuỗi không rỗng" in errors[1]


def test_split_records_is_deterministic_and_has_no_overlap() -> None:
    records = [
        make_record(f"{category}-{index}", category)
        for category in ("itinerary", "budget")
        for index in range(10)
    ]

    first = split_records(records, validation_ratio=0.1, test_ratio=0.1, seed=42)
    second = split_records(records, validation_ratio=0.1, test_ratio=0.1, seed=42)

    assert first == second
    split_ids = [{record["id"] for record in split} for split in first.values()]
    assert len(set.union(*split_ids)) == len(records)
    assert all(
        left.isdisjoint(right) for left in split_ids for right in split_ids if left is not right
    )


def test_written_split_can_be_loaded_and_manifested(tmp_path: Path) -> None:
    records = [make_record(f"itinerary-{index}", "itinerary") for index in range(4)]
    dataset_path = tmp_path / "seed.jsonl"
    write_jsonl(dataset_path, records)

    loaded, errors = load_and_validate(dataset_path, require_metadata=True)
    splits = split_records(loaded, validation_ratio=0.25, test_ratio=0.25, seed=7)
    manifest = build_manifest(dataset_path, splits, seed=7)

    assert errors == []
    assert manifest["totalRecords"] == 4
    assert len(manifest["sourceSha256"]) == 64
    json.dumps(manifest)


def test_split_group_never_leaks_between_sets() -> None:
    records = [
        {
            **make_record(f"{category}-{destination}-{index}", category),
            "splitGroup": destination,
        }
        for destination in ("Đà Nẵng", "Huế", "Hội An", "Đà Lạt", "Nha Trang")
        for category in ("itinerary", "budget")
        for index in range(3)
    ]

    splits = split_records(records, validation_ratio=0.2, test_ratio=0.2, seed=42)
    group_sets = [
        {record["splitGroup"] for record in split_records_list}
        for split_records_list in splits.values()
    ]

    assert all(
        left.isdisjoint(right) for left in group_sets for right in group_sets if left is not right
    )
