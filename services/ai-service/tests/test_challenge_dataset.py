from training.build_challenge_dataset import build_records
from training.validate_dataset import validate_record


def test_challenge_dataset_is_manual_unique_and_valid() -> None:
    records = build_records()
    errors = [
        error
        for line_number, record in enumerate(records, start=1)
        for error in validate_record(record, line_number, require_metadata=True)
    ]

    assert len(records) == 20
    assert len({record["id"] for record in records}) == 20
    assert (
        len(
            {
                message["content"].casefold()
                for record in records
                for message in record["messages"]
                if message["role"] == "user"
            }
        )
        == 21
    )
    assert {record["reviewStatus"] for record in records} == {"challenge_v1"}
    assert errors == []
