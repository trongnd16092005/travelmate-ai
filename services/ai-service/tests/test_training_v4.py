from collections import Counter
from copy import deepcopy

import pytest

from training.build_conversation_v4 import audit_records, build_records


def test_conversation_v4_has_expected_multi_turn_distribution() -> None:
    records = build_records("2026-08-05")

    assert len(records) == 240
    assert Counter(record["category"] for record in records) == {
        "multi_turn_slot_v4": 80,
        "multi_turn_correction_v4": 60,
        "multi_turn_budget_v4": 40,
        "multi_turn_followup_v4": 40,
        "multi_turn_casual_v4": 20,
    }
    assert all(len(record["messages"]) == 5 for record in records)
    assert Counter(record["split"] for record in records) == {
        "train": 200,
        "validation": 20,
        "test": 20,
    }


def test_conversation_v4_assistant_style_is_plain_and_concise() -> None:
    records = build_records("2026-08-05")
    responses = [
        message["content"]
        for record in records
        for message in record["messages"]
        if message["role"] == "assistant"
    ]

    assert len(responses) == 480
    assert all(len(response) <= 320 for response in responses)
    assert all(response.count("?") <= 1 for response in responses)
    assert all(not any(marker in response for marker in ("**", "###", "```")) for response in responses)


def test_conversation_v4_audit_rejects_markdown() -> None:
    records = build_records("2026-08-05")
    invalid_records = deepcopy(records)
    invalid_records[0]["messages"][-1]["content"] = "**Câu trả lời máy móc**"

    with pytest.raises(SystemExit, match="Markdown"):
        audit_records(invalid_records, [])
