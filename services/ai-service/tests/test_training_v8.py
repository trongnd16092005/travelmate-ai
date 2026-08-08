from collections import Counter

from training.build_state_transition_v8 import audit_records, build_records


def test_v8_has_generalized_state_transition_distribution() -> None:
    records = build_records("2026-08-05")

    assert len(records) == 560
    assert Counter(record["category"] for record in records) == {
        "destination_switch_v8": 140,
        "region_switch_v8": 105,
        "slot_correction_v8": 105,
        "explicit_reset_v8": 140,
        "same_trip_retention_v8": 70,
    }
    assert Counter(record["split"] for record in records) == {
        "train": 385,
        "validation": 90,
        "test": 85,
    }


def test_v8_covers_switch_correction_reset_and_retention() -> None:
    records = build_records("2026-08-05")
    categories = {record["category"]: [] for record in records}
    for record in records:
        categories[record["category"]].append(record["messages"][-1]["content"])

    assert all("bỏ thông tin phụ thuộc chuyến cũ" in response or "4 ngày" in response for response in categories["destination_switch_v8"])
    assert all("bỏ dữ liệu" in response for response in categories["region_switch_v8"])
    assert all("Mình vẫn giữ" in response for response in categories["slot_correction_v8"])
    assert all("đã xóa ngữ cảnh chuyến cũ" in response for response in categories["explicit_reset_v8"])
    assert all("giữ" in response for response in categories["same_trip_retention_v8"])


def test_v8_heldout_prompts_are_paraphrases_not_train_duplicates() -> None:
    records = build_records("2026-08-05")
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
    assert len(heldout_prompts) >= 25


def test_v8_audit_accepts_generated_records() -> None:
    audit_records(build_records("2026-08-05"), [])
