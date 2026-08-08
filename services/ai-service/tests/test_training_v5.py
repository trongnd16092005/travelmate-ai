from collections import Counter
from copy import deepcopy

import pytest

from training.build_conversation_v5 import TRAINING_SYSTEM_PROMPT, audit_records, build_records


def test_conversation_v5_has_expected_stateful_distribution() -> None:
    records = build_records("2026-08-05")

    assert len(records) == 400
    assert Counter(record["category"] for record in records) == {
        "long_context_v5": 120,
        "short_context_answer_v5": 100,
        "intent_switch_v5": 80,
        "state_conflict_v5": 60,
        "realtime_retention_v5": 20,
        "safety_retention_v5": 20,
    }
    assert Counter(record["split"] for record in records) == {
        "train": 300,
        "validation": 50,
        "test": 50,
    }


def test_conversation_v5_contains_long_and_elliptical_dialogues() -> None:
    records = build_records("2026-08-05")
    long_records = [record for record in records if record["category"] == "long_context_v5"]
    short_answers = [
        message["content"].strip().casefold()
        for record in records
        for message in record["messages"]
        if message["role"] == "user" and len(message["content"].split()) == 1
    ]

    assert all(len(record["messages"]) == 11 for record in long_records)
    assert len(short_answers) >= 100
    assert {"rồi.", "chưa.", "4.", "3.", "có."}.issubset(set(short_answers))


def test_conversation_v5_prompt_defines_state_and_intent_rules() -> None:
    assert len(TRAINING_SYSTEM_PROMPT) < 700
    assert '"rồi", "chưa", "có", "không"' in TRAINING_SYSTEM_PROMPT
    assert "Trả lời ý định hiện tại trước" in TRAINING_SYSTEM_PROMPT
    assert "không hỏi lại dữ liệu đã có" in TRAINING_SYSTEM_PROMPT


def test_conversation_v5_audit_rejects_repeated_question_shape() -> None:
    records = build_records("2026-08-05")
    invalid_records = deepcopy(records)
    invalid_records[0]["messages"][-1]["content"] = "Bạn đi mấy ngày? Ngân sách bao nhiêu?"

    with pytest.raises(SystemExit, match="hỏi nhiều câu"):
        audit_records(invalid_records, [])
