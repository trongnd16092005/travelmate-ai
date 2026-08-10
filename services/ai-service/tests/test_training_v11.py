from collections import Counter

from app.knowledge.destinations import NATIONWIDE_DESTINATIONS, resolve_destination
from training.build_nationwide_v11 import (
    audit_records,
    build_alias_records,
    build_structured_records,
)
from training.evaluate_nationwide import evaluate_nationwide_records


def test_v11_covers_all_current_province_level_units() -> None:
    assert len(NATIONWIDE_DESTINATIONS) == 34
    assert len({destination.name for destination in NATIONWIDE_DESTINATIONS}) == 34
    assert {destination.id.split("-", 2)[1] for destination in NATIONWIDE_DESTINATIONS} == {
        "01", "04", "08", "11", "12", "14", "15", "19", "20", "22", "24", "25",
        "31", "33", "37", "38", "40", "42", "44", "46", "48", "51", "52", "56",
        "66", "68", "75", "79", "80", "82", "86", "91", "92", "96",
    }


def test_v11_balances_structured_and_alias_data() -> None:
    records = [*build_structured_records("2026-08-10"), *build_alias_records("2026-08-10")]

    assert len(records) == 952
    assert Counter(record["split"] for record in records) == {
        "train": 748,
        "validation": 102,
        "test": 102,
    }
    assert len({record["provinceCode"] for record in records}) == 34
    audit_records(records, [])


def test_v11_maps_legacy_province_names_to_current_catalog() -> None:
    assert resolve_destination("Hà Giang").name == "Tuyên Quang"
    assert resolve_destination("Quảng Bình").name == "Quảng Trị"
    assert resolve_destination("Bến Tre").name == "Vĩnh Long"
    assert resolve_destination("Bạc Liêu").name == "Cà Mau"
    assert resolve_destination("Bà Rịa - Vũng Tàu").name == "TP. Hồ Chí Minh"


def test_v11_never_places_heldout_prompts_in_training() -> None:
    records = [*build_structured_records("2026-08-10"), *build_alias_records("2026-08-10")]
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


def test_v11_evaluator_accepts_ground_truth_heldout_responses() -> None:
    records = [
        record
        for record in [
            *build_structured_records("2026-08-10"),
            *build_alias_records("2026-08-10"),
        ]
        if record["split"] == "test"
    ]
    predictions = {
        record["id"]: record["messages"][-1]["content"] for record in records
    }

    report = evaluate_nationwide_records(records, predictions)

    assert report["records"] == 102
    assert report["passed"] == 102
    assert report["provinceCoveragePassed"] == 34
