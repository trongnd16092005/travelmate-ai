from app.knowledge.destinations import DESTINATIONS, resolve_destination


def test_destination_catalog_has_unique_ids_and_place_ids() -> None:
    destination_ids = [destination.id for destination in DESTINATIONS]
    place_ids = [place.id for destination in DESTINATIONS for place in destination.places]

    assert len(DESTINATIONS) == 20
    assert len(set(destination_ids)) == len(destination_ids)
    assert len(set(place_ids)) == len(place_ids)
    assert all(place.id.startswith(f"{destination.id}:") for destination in DESTINATIONS for place in destination.places)


def test_destination_aliases_are_accent_and_punctuation_tolerant() -> None:
    assert resolve_destination("Da Nang").name == "Đà Nẵng"
    assert resolve_destination("TP.HCM").name == "TP. Hồ Chí Minh"
    assert resolve_destination("sai gon").name == "TP. Hồ Chí Minh"
    assert resolve_destination("điểm chưa hỗ trợ") is None
