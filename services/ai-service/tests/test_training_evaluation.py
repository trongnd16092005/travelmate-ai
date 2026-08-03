from training.evaluate_predictions import evaluate_records
from training.train_qlora import to_prompt_completion


def make_record(record_id: str, behavior: str) -> dict:
    return {
        "id": record_id,
        "category": "test",
        "expectedBehaviors": [behavior],
        "messages": [
            {"role": "user", "content": "Câu hỏi thử nghiệm"},
            {"role": "assistant", "content": "Câu trả lời tham chiếu"},
        ],
    }


def test_to_prompt_completion_only_trains_assistant_turn() -> None:
    record = make_record("test-001", "ask_clarification")

    formatted = to_prompt_completion(record)

    assert formatted["prompt"] == record["messages"][:-1]
    assert formatted["completion"] == [record["messages"][-1]]


def test_behavior_evaluation_reports_pass_rates() -> None:
    records = [
        make_record("scope-001", "out_of_scope_marker"),
        make_record("realtime-001", "realtime_limit"),
        make_record("clarify-001", "ask_clarification"),
    ]
    predictions = {
        "scope-001": "[OUT_OF_SCOPE] Mình chỉ hỗ trợ du lịch.",
        "realtime-001": "Thông tin này cần tra cứu theo thời gian thực.",
        "clarify-001": "Bạn đi bao nhiêu người?",
    }

    report = evaluate_records(records, predictions)

    assert report["coverage"] == 1.0
    assert report["nonEmptyRate"] == 1.0
    assert report["behaviorPassRate"] == 1.0


def test_behavior_evaluation_tracks_missing_predictions() -> None:
    records = [make_record("scope-001", "out_of_scope_marker")]

    report = evaluate_records(records, {})

    assert report["coverage"] == 0.0
    assert report["missingIds"] == ["scope-001"]
