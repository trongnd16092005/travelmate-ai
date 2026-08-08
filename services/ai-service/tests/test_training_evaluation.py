from argparse import Namespace
from pathlib import Path

import pytest

from training.build_reinforcement_v2 import EXPECTED_COUNTS, build_records
from training.evaluate_predictions import evaluate_records
from training.prepare_dataset import write_jsonl
from training.train_qlora import (
    build_run_summary,
    find_truncated_completion_ids,
    to_prompt_completion,
    validate_training_files,
)


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


def test_token_budget_guard_detects_completion_cutoff() -> None:
    class CharacterTokenizer:
        @staticmethod
        def apply_chat_template(messages, **kwargs):
            return "|".join(message["content"] for message in messages)

        @staticmethod
        def __call__(value, **kwargs):
            return {"input_ids": list(value)}

    records = [
        {
            "id": "fits",
            "messages": [
                {"role": "user", "content": "ngắn"},
                {"role": "assistant", "content": "được"},
            ],
        },
        {
            "id": "truncated",
            "messages": [
                {"role": "system", "content": "x" * 20},
                {"role": "user", "content": "dài"},
                {"role": "assistant", "content": "không được cắt"},
            ],
        },
    ]

    assert find_truncated_completion_ids(records, CharacterTokenizer(), 10) == ["truncated"]


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


def test_training_rejects_synthetic_draft_without_explicit_override(tmp_path: Path) -> None:
    records = [make_record(f"draft-{index}", "ask_clarification") for index in range(3)]
    for record in records:
        record["reviewStatus"] = "synthetic_draft_v1"
    train_path = tmp_path / "train.jsonl"
    eval_path = tmp_path / "validation.jsonl"
    write_jsonl(train_path, records[:2])
    write_jsonl(eval_path, records[2:])

    with pytest.raises(SystemExit, match="mẫu chưa được duyệt"):
        validate_training_files(train_path, eval_path)

    assert validate_training_files(train_path, eval_path, allow_unreviewed_data=True) == (2, 1)


def test_build_run_summary_honors_benchmark_step_limit() -> None:
    args = Namespace(
        model_id="Qwen/Qwen3-4B",
        train_dataset=Path("train.jsonl"),
        eval_dataset=Path("validation.jsonl"),
        output_dir=Path("adapter-v2"),
        epochs=3.0,
        max_length=512,
        learning_rate=2e-4,
        gradient_accumulation_steps=16,
        lora_r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        max_steps=20,
        save_steps=20,
        smoke_test=False,
    )

    summary = build_run_summary(args, train_size=960, eval_size=120)

    assert summary["estimatedSteps"] == 20
    assert summary["maxSteps"] == 20
    assert summary["loraR"] == 8
    assert summary["gradientAccumulationSteps"] == 16


def test_build_run_summary_rounds_partial_optimizer_step_up() -> None:
    args = Namespace(
        model_id="Qwen/Qwen3-4B",
        train_dataset=Path("train.jsonl"),
        eval_dataset=Path("validation.jsonl"),
        output_dir=Path("adapter-v2"),
        epochs=1.0,
        max_length=512,
        learning_rate=1e-4,
        gradient_accumulation_steps=16,
        lora_r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        max_steps=-1,
        save_steps=20,
        smoke_test=False,
    )

    summary = build_run_summary(args, train_size=1140, eval_size=120)

    assert summary["estimatedSteps"] == 72


def test_reinforcement_v2_has_expected_distribution_and_unique_prompts() -> None:
    records = build_records("2026-08-05")
    prompts = [record["messages"][-2]["content"].casefold() for record in records]
    counts: dict[str, int] = {}
    for record in records:
        category = record["category"]
        counts[category] = counts.get(category, 0) + 1

    assert len(records) == 180
    assert len(set(prompts)) == len(prompts)
    assert dict(sorted(counts.items())) == EXPECTED_COUNTS
    assert all(record["reviewStatus"] == "approved" for record in records)
