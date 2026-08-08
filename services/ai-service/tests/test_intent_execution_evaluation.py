from training.build_intent_execution_v7 import build_records
from training.evaluate_intent_execution import evaluate_intent_records


def test_intent_evaluator_accepts_reference_responses() -> None:
    records = [record for record in build_records("2026-08-05") if record["split"] == "test"]
    predictions = {record["id"]: record["messages"][-1]["content"] for record in records}

    report = evaluate_intent_records(records, predictions)

    assert report["records"] == 68
    assert report["passed"] == 68
    assert report["passRate"] == 1.0


def test_intent_evaluator_rejects_menu_instead_of_execution() -> None:
    record = next(
        record
        for record in build_records("2026-08-05")
        if record["category"] == "itinerary_execution_v7"
    )
    predictions = {
        record["id"]: "Bạn muốn mình lập lịch trình, phân bổ ngân sách hay chuẩn bị checklist?"
    }

    report = evaluate_intent_records([record], predictions)

    assert report["passRate"] == 0.0
    assert "lặp lại menu lựa chọn" in report["cases"][0]["errors"]
