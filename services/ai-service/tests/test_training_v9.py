from collections import Counter

from training.build_natural_ux_v9 import audit_records, build_records


def test_v9_has_balanced_natural_ux_distribution() -> None:
    records = build_records("2026-08-07")

    assert len(records) == 455
    assert Counter(record["category"] for record in records) == {
        "multi_slot_followup_v9": 140,
        "correction_echo_v9": 105,
        "retention_echo_v9": 70,
        "clean_switch_v9": 105,
        "natural_clarification_v9": 35,
    }
    assert Counter(record["split"] for record in records) == {
        "train": 305,
        "validation": 77,
        "test": 73,
    }


def test_v9_responses_echo_state_and_never_copy_stale_slots() -> None:
    records = build_records("2026-08-07")
    by_category: dict[str, list[str]] = {}
    for record in records:
        by_category.setdefault(record["category"], []).append(
            record["messages"][-1]["content"]
        )

    assert all("Ngân sách này đã gồm" in reply for reply in by_category["multi_slot_followup_v9"])
    assert all("Mình vẫn giữ" in reply for reply in by_category["correction_echo_v9"])
    assert all("giữ nguyên" in reply for reply in by_category["retention_echo_v9"])
    assert all("thông tin phụ thuộc chuyến cũ" in reply for reply in by_category["clean_switch_v9"])
    assert all("điểm đến hoặc khu vực nào" in reply for reply in by_category["natural_clarification_v9"])


def test_v9_heldout_prompts_do_not_duplicate_train_prompts() -> None:
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


def test_v9_audit_accepts_generated_records() -> None:
    audit_records(build_records("2026-08-07"), [])
