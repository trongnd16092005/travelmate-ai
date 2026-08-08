import json

from training.build_training_v3 import build_chat_records, build_structured_records
from training.evaluate_structured_predictions import validate_structured_response


def test_training_v3_counts_and_unique_prompts() -> None:
    structured = build_structured_records("2026-08-05")
    chat = build_chat_records("2026-08-05")
    all_records = chat + [record for split in structured.values() for record in split]
    prompts = [record["messages"][-2]["content"] for record in all_records]

    assert len(chat) == 200
    assert len(structured["train"]) == 480
    assert len(structured["validation"]) == 40
    assert len(structured["test"]) == 40
    assert len(prompts) == len(set(prompts))


def test_structured_training_response_satisfies_grounding_contract() -> None:
    record = build_structured_records("2026-08-05")["test"][0]
    response = record["messages"][-1]["content"]

    assert validate_structured_response(record, response) == []


def test_structured_evaluator_rejects_unknown_place_id() -> None:
    record = build_structured_records("2026-08-05")["test"][0]
    response = json.loads(record["messages"][-1]["content"])
    response["days"][0]["activities"][0]["placeId"] = "unknown:place"

    errors = validate_structured_response(record, json.dumps(response))

    assert any("placeId ngoài danh mục" in error for error in errors)
