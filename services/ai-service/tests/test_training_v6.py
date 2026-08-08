from collections import Counter

from training.build_destination_v6 import (
    EXPANDED_DESTINATION_NAMES,
    audit_records,
    build_recommendation_records,
    build_structured_records,
)


def test_v6_expands_fifteen_destinations_with_structured_grounding() -> None:
    records = build_structured_records("2026-08-05")

    assert len(EXPANDED_DESTINATION_NAMES) == 15
    assert len(records) == 420
    assert Counter(record["split"] for record in records) == {
        "train": 360,
        "validation": 30,
        "test": 30,
    }


def test_v6_covers_region_theme_recommendations_and_demo_shape() -> None:
    records = build_recommendation_records("2026-08-05")
    northern_beach = [
        record
        for record in records
        if "Với ưu tiên biển ở Miền Bắc" in record["messages"][-1]["content"]
    ]

    assert len(records) >= 80
    assert len(northern_beach) == 4
    assert all("Hạ Long" in record["messages"][-1]["content"] for record in northern_beach)
    assert all("Cát Bà" in record["messages"][-1]["content"] for record in northern_beach)
    assert any(
        message["content"] == "Gợi ý giúp tôi."
        for record in northern_beach
        for message in record["messages"]
    )


def test_v6_audit_accepts_generated_records() -> None:
    records = [
        *build_structured_records("2026-08-05"),
        *build_recommendation_records("2026-08-05"),
    ]

    audit_records(records, [])
