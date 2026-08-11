from pathlib import Path

import pytest

from training.evaluate_reasoning import evaluate_reasoning_records, reasoning_errors
from training.validate_dataset import load_and_validate


def require_dataset(path: str) -> Path:
    dataset = Path(path)
    if not dataset.is_file():
        pytest.skip(f"Generated evaluation dataset is absent: {dataset}")
    return dataset


def test_reference_responses_pass_reasoning_evaluation() -> None:
    dataset = require_dataset("training/data/processed/reasoning_v10/reasoning_test.jsonl")
    records, errors = load_and_validate(dataset, require_metadata=True)
    assert errors == []
    predictions = {record["id"]: record["messages"][-1]["content"] for record in records}

    report = evaluate_reasoning_records(records, predictions)

    assert report["records"] == 20
    assert report["passed"] == 20
    assert report["passRate"] == 1.0


def test_empty_predictions_fail_all_reasoning_cases() -> None:
    dataset = require_dataset("training/data/processed/reasoning_v10/reasoning_test.jsonl")
    records, errors = load_and_validate(dataset, require_metadata=True)
    assert errors == []

    report = evaluate_reasoning_records(records, {})

    assert report["records"] == 20
    assert report["passed"] == 0


def test_evaluator_rejects_exposed_chain_of_thought() -> None:
    record = {
        "category": "uncertainty_boundary_v10",
        "evaluation": {"requiredTerms": [], "requiredAny": []},
    }

    assert "lộ chuỗi suy nghĩ nội bộ" in reasoning_errors(
        record, "Phân tích nội bộ: đầu tiên mình suy luận..."
    )
