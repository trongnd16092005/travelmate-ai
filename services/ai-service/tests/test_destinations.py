from app.knowledge.destinations import DESTINATIONS, recommend_destinations, resolve_destination


def test_expanded_catalog_has_region_and_theme_metadata() -> None:
    assert len(DESTINATIONS) == 35
    assert all(destination.region and destination.themes for destination in DESTINATIONS)


def test_northern_beach_recommendations_are_grounded_and_ranked() -> None:
    recommendations = recommend_destinations("Miền Bắc", ("biển",), limit=5)

    assert [destination.name for destination in recommendations] == [
        "Hạ Long",
        "Cát Bà",
        "Cô Tô",
        "Quan Lạn",
        "Móng Cái",
    ]
    assert all(destination.region == "Miền Bắc" for destination in recommendations)
    assert all("biển" in destination.themes for destination in recommendations)


def test_new_destination_aliases_resolve() -> None:
    assert resolve_destination("đảo Cát Bà").name == "Cát Bà"
    assert resolve_destination("Tra Co").name == "Móng Cái"
    assert resolve_destination("Con Son").name == "Côn Đảo"


def test_runtime_catalog_expands_hot_destinations_only() -> None:
    assert len(resolve_destination("Hà Nội").places) == 6
    assert len(resolve_destination("Hạ Long").places) == 6
    assert len(resolve_destination("Đà Nẵng").places) == 6
    assert len(resolve_destination("Cao Bằng").places) == 3
