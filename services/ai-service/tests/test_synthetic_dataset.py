from collections import Counter

from training.evaluate_predictions import evaluate_records
from training.generate_synthetic_dataset import generate_records
from training.validate_dataset import validate_record


def test_synthetic_dataset_has_expected_size_and_distribution() -> None:
    records = generate_records()

    assert len(records) == 1200
    assert Counter(record["category"] for record in records) == {
        "itinerary": 300,
        "budget": 240,
        "accommodation": 200,
        "food": 120,
        "safety_weather": 120,
        "realtime_limit": 80,
        "out_of_scope": 80,
        "action_boundary": 60,
    }


def test_synthetic_dataset_has_unique_ids_and_prompts() -> None:
    records = generate_records()
    record_ids = [record["id"] for record in records]
    user_prompts = [record["messages"][-2]["content"].casefold() for record in records]

    assert len(set(record_ids)) == len(records)
    assert len(set(user_prompts)) == len(records)
    assert {record["reviewStatus"] for record in records} == {"synthetic_draft_v1"}
    assert Counter(record["reviewBatch"] for record in records) == {
        batch: 100 for batch in range(1, 13)
    }


def test_every_synthetic_record_matches_conversation_schema() -> None:
    errors = [
        error
        for line_number, record in enumerate(generate_records(), start=1)
        for error in validate_record(record, line_number, require_metadata=True)
    ]

    assert errors == []


def test_reference_responses_pass_declared_behavior_checks() -> None:
    records = generate_records()
    reference_predictions = {record["id"]: record["messages"][-1]["content"] for record in records}

    report = evaluate_records(records, reference_predictions)

    assert report["coverage"] == 1.0
    assert report["nonEmptyRate"] == 1.0
    assert report["behaviorPassRate"] == 1.0
