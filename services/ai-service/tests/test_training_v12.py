from collections import Counter

from training.build_grounded_conversation_v12 import (
    V11_FAILED_CODES,
    build_records,
    final_user_prompt,
)
from training.evaluate_grounded_conversation import evaluate_records


def test_v12_split_and_targeted_oversampling() -> None:
    records = build_records("2026-08-10")

    assert Counter(record["split"] for record in records) == {
        "train": 684,
        "validation": 102,
        "test": 102,
    }
    coverage = Counter(record["provinceCode"] for record in records)
    assert len(coverage) == 34
    assert all(
        count == (30 if code in V11_FAILED_CODES else 24)
        for code, count in coverage.items()
    )


def test_v12_uses_grounded_catalog_context_and_no_realtime_facts() -> None:
    records = build_records("2026-08-10")

    assert all("[GROUNDED_CATALOG]" in record["messages"][1]["content"] for record in records)
    assert all(
        "nguồn realtime" in record["messages"][-1]["content"]
        or "nguồn hiện tại" in record["messages"][-1]["content"]
        for record in records
    )


def test_v12_train_prompts_do_not_overlap_heldout() -> None:
    records = build_records("2026-08-10")
    train = {final_user_prompt(record) for record in records if record["split"] == "train"}
    heldout = {
        final_user_prompt(record) for record in records if record["split"] != "train"
    }

    assert train.isdisjoint(heldout)


def test_v12_strict_evaluator_accepts_only_ground_truth() -> None:
    records = [record for record in build_records("2026-08-10") if record["split"] == "test"]
    predictions = {record["id"]: record["messages"][-1]["content"] for record in records}

    report = evaluate_records(records, predictions)

    assert report["records"] == 102
    assert report["passed"] == 102
    assert report["passRate"] == 1.0


def test_v12_strict_evaluator_rejects_hallucinated_place_and_hours() -> None:
    record = next(record for record in build_records("2026-08-10") if record["split"] == "test")
    predictions = {
        record["id"]: (
            "Mình gợi ý Công viên Mây Trắng, mở cửa từ 8:00 và vé 100000 VND."
        )
    }

    report = evaluate_records([record], predictions)

    assert report["passed"] == 0
    assert report["cases"][0]["checks"]["allCatalogPlaces"] is False
    assert report["cases"][0]["checks"]["realtimeBoundary"] is False
