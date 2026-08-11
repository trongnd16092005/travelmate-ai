import json
from pathlib import Path

import pytest

from training.evaluate_state_transition import evaluate_transition_records
from training.validate_dataset import load_and_validate


def require_dataset(path: str) -> Path:
    dataset = Path(path)
    if not dataset.is_file():
        pytest.skip(f"Generated evaluation dataset is absent: {dataset}")
    return dataset


def test_reference_responses_pass_transition_evaluation(tmp_path: Path) -> None:
    dataset = require_dataset("training/data/processed/state_v8/transition_test.jsonl")
    records, errors = load_and_validate(dataset, require_metadata=True)
    assert errors == []
    predictions = {record["id"]: record["messages"][-1]["content"] for record in records}

    report = evaluate_transition_records(records, predictions)

    assert report["records"] == 20
    assert report["passed"] == 20
    assert report["passRate"] == 1.0


def test_empty_predictions_fail_all_transition_cases(tmp_path: Path) -> None:
    dataset = require_dataset("training/data/processed/state_v8/transition_test.jsonl")
    records = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines()]

    report = evaluate_transition_records(records, {})

    assert report["records"] == 20
    assert report["passed"] == 0
