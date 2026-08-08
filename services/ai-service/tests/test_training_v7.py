from collections import Counter

from training.build_intent_execution_v7 import audit_records, build_records


def test_v7_has_expected_intent_execution_distribution() -> None:
    records = build_records("2026-08-05")

    assert len(records) == 420
    assert Counter(record["category"] for record in records) == {
        "itinerary_execution_v7": 140,
        "budget_execution_v7": 105,
        "checklist_execution_v7": 105,
        "compound_execution_v7": 70,
    }
    assert Counter(record["split"] for record in records) == {
        "train": 280,
        "validation": 72,
        "test": 68,
    }


def test_v7_final_responses_execute_instead_of_asking() -> None:
    records = build_records("2026-08-05")

    assert all("?" not in record["messages"][-1]["content"] for record in records)
    assert all(
        "Ngày 1:" in record["messages"][-1]["content"]
        for record in records
        if record["category"] == "itinerary_execution_v7"
    )
    assert all(
        "Lưu trú 35%" in record["messages"][-1]["content"]
        for record in records
        if record["category"] == "budget_execution_v7"
    )
    assert all(
        "Giấy tờ" in record["messages"][-1]["content"]
        for record in records
        if record["category"] == "checklist_execution_v7"
    )


def test_v7_contains_current_demo_prompt_and_compound_execution() -> None:
    records = build_records("2026-08-05")
    user_messages = [
        message["content"]
        for record in records
        for message in record["messages"]
        if message["role"] == "user"
    ]
    compound = [record for record in records if record["category"] == "compound_execution_v7"]

    assert "Hỗ trợ lập lịch đi." in user_messages
    assert "Theo điểm đến nhé." in user_messages
    assert all("Ngày 1:" in record["messages"][-1]["content"] for record in compound)
    assert all("Lưu trú 35%" in record["messages"][-1]["content"] for record in compound)
    assert all("Giấy tờ" in record["messages"][-1]["content"] for record in compound)


def test_v7_audit_accepts_generated_records() -> None:
    audit_records(build_records("2026-08-05"), [])
