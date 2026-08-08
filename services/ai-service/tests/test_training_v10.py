from collections import Counter

from training.build_reasoning_v10 import audit_records, build_records


def test_v10_has_balanced_reasoning_distribution() -> None:
    records = build_records("2026-08-07")

    assert len(records) == 525
    assert Counter(record["category"] for record in records) == {
        "constraint_prioritization_v10": 105,
        "infeasible_plan_repair_v10": 105,
        "alternative_comparison_v10": 105,
        "sequence_dependency_v10": 105,
        "uncertainty_boundary_v10": 105,
    }
    assert Counter(record["split"] for record in records) == {
        "train": 350,
        "validation": 90,
        "test": 85,
    }


def test_v10_heldout_prompts_are_not_in_training() -> None:
    records = build_records("2026-08-07")
    train_prompts = {
        record["messages"][-2]["content"].casefold()
        for record in records
        if record["split"] == "train"
    }
    heldout_prompts = {
        record["messages"][-2]["content"].casefold()
        for record in records
        if record["split"] != "train"
    }

    assert not train_prompts & heldout_prompts


def test_v10_answers_do_not_request_or_expose_chain_of_thought() -> None:
    records = build_records("2026-08-07")
    forbidden = ("<think>", "chain of thought", "chuỗi suy nghĩ", "phân tích nội bộ")

    for record in records:
        answer = record["messages"][-1]["content"].casefold()
        assert not any(marker in answer for marker in forbidden)
        assert "reasoning" not in answer


def test_v10_audit_accepts_generated_records() -> None:
    audit_records(build_records("2026-08-07"), [])
