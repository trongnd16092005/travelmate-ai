from pathlib import Path

from training.evaluate_natural_ux import (
    asks_for_destination,
    evaluate_ux_records,
    mentions_stale_destination,
)
from training.validate_dataset import load_and_validate


def test_reference_responses_pass_natural_ux_evaluation() -> None:
    dataset = Path("training/data/processed/ux_v9/ux_test.jsonl")
    records, errors = load_and_validate(dataset, require_metadata=True)
    assert errors == []
    predictions = {record["id"]: record["messages"][-1]["content"] for record in records}

    report = evaluate_ux_records(records, predictions)

    assert report["records"] == 20
    assert report["passed"] == 20
    assert report["passRate"] == 1.0


def test_empty_predictions_fail_all_natural_ux_cases() -> None:
    dataset = Path("training/data/processed/ux_v9/ux_test.jsonl")
    records, errors = load_and_validate(dataset, require_metadata=True)
    assert errors == []

    report = evaluate_ux_records(records, {})

    assert report["records"] == 20
    assert report["passed"] == 0


def test_destination_question_accepts_natural_vietnamese_variants() -> None:
    assert asks_for_destination("Bạn đi đâu trước?")
    assert asks_for_destination("Bạn dự định đi nơi đâu trước?")
    assert asks_for_destination("Bạn muốn chọn khu vực nào?")
    assert not asks_for_destination("Bạn dự định khởi hành khi nào?")


def test_old_destination_is_allowed_only_as_a_reset_confirmation() -> None:
    assert not mentions_stale_destination("Mình đã bỏ thông tin chuyến Huế.", "hue")
    assert mentions_stale_destination("Lịch Huế vẫn giữ nguyên.", "hue")
