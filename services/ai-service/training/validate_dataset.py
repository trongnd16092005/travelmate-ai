import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ALLOWED_ROLES = {"system", "user", "assistant"}


def validate_record(record: dict[str, Any], line_number: int) -> list[str]:
    errors: list[str] = []
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


def load_and_validate(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
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
            errors.extend(validate_record(record, line_number))
    return records, errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Kiểm tra dataset hội thoại TravelMate")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--minimum-records", type=int, default=20)
    args = parser.parse_args()

    records, errors = load_and_validate(args.dataset)
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

    if errors:
        for error in errors:
            print(f"[LOI] {error}")
        raise SystemExit(1)

    print(f"Dataset hợp lệ: {len(records)} hội thoại, {len(user_prompts)} câu user")


if __name__ == "__main__":
    main()
