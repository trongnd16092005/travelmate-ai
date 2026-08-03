import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ALLOWED_ROLES = {"system", "user", "assistant"}


def validate_record(
    record: dict[str, Any], line_number: int, require_metadata: bool = False
) -> list[str]:
    errors: list[str] = []
    if require_metadata:
        if not isinstance(record.get("id"), str) or not record["id"].strip():
            errors.append(f"Dòng {line_number}: id phải là chuỗi không rỗng")
        if not isinstance(record.get("category"), str) or not record["category"].strip():
            errors.append(f"Dòng {line_number}: category phải là chuỗi không rỗng")
    messages = record.get("messages")
    if not isinstance(messages, list) or not messages:
        return [f"Dòng {line_number}: messages phải là danh sách không rỗng"]

    roles: list[str] = []
    for index, message in enumerate(messages, start=1):
        if not isinstance(message, dict):
            errors.append(f"Dòng {line_number}, message {index}: phải là object")
            continue
        role = message.get("role")
        content = message.get("content")
        if role not in ALLOWED_ROLES:
            errors.append(f"Dòng {line_number}, message {index}: role không hợp lệ")
        else:
            roles.append(role)
        if not isinstance(content, str) or not content.strip():
            errors.append(f"Dòng {line_number}, message {index}: content bị trống")

    if "user" not in roles or "assistant" not in roles:
        errors.append(f"Dòng {line_number}: phải có cả user và assistant")
    if roles and roles[-1] != "assistant":
        errors.append(f"Dòng {line_number}: message cuối phải là assistant")
    return errors


def load_and_validate(
    path: Path, require_metadata: bool = False
) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    with path.open(encoding="utf-8") as dataset_file:
        for line_number, raw_line in enumerate(dataset_file, start=1):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                errors.append(f"Dòng {line_number}: JSON không hợp lệ ({exc.msg})")
                continue
            if not isinstance(record, dict):
                errors.append(f"Dòng {line_number}: bản ghi phải là object")
                continue
            records.append(record)
            errors.extend(validate_record(record, line_number, require_metadata))
    return records, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Kiểm tra dataset hội thoại TravelMate")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--minimum-records", type=int, default=20)
    parser.add_argument("--require-metadata", action="store_true")
    args = parser.parse_args()

    records, errors = load_and_validate(args.dataset, args.require_metadata)
    if len(records) < args.minimum_records:
        errors.append(
            f"Dataset có {len(records)} bản ghi, cần ít nhất {args.minimum_records} bản ghi"
        )

    user_prompts = [
        message["content"].strip().casefold()
        for record in records
        for message in record["messages"]
        if message.get("role") == "user" and isinstance(message.get("content"), str)
    ]
    duplicates = [text for text, count in Counter(user_prompts).items() if count > 1]
    if duplicates:
        errors.append(f"Có {len(duplicates)} câu user bị trùng hoàn toàn")

    ids = [record.get("id") for record in records if isinstance(record.get("id"), str)]
    duplicate_ids = [record_id for record_id, count in Counter(ids).items() if count > 1]
    if duplicate_ids:
        errors.append(f"Có {len(duplicate_ids)} id bị trùng")

    if errors:
        for error in errors:
            print(f"[LOI] {error}")
        raise SystemExit(1)

    categories = Counter(
        record.get("category", "chưa_gán")
        for record in records
        if isinstance(record.get("category", "chưa_gán"), str)
    )
    print(f"Dataset hợp lệ: {len(records)} hội thoại, {len(user_prompts)} câu user")
    print("Phân bố chủ đề:")
    for category, count in sorted(categories.items()):
        print(f"- {category}: {count}")


if __name__ == "__main__":
    main()
