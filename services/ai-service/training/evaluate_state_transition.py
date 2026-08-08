import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from training.evaluate_predictions import load_predictions
from training.validate_dataset import load_and_validate

TRANSITION_CATEGORIES = {
    "destination_switch_v8",
    "region_switch_v8",
    "slot_correction_v8",
    "explicit_reset_v8",
    "same_trip_retention_v8",
}


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    return "".join(character for character in decomposed if unicodedata.category(character) != "Mn")


def contains_money(response: str, millions: int) -> bool:
    normalized = normalize(response)
    return bool(
        re.search(rf"\b{millions}\s*(?:trieu|tr)\b", normalized)
        or re.search(rf"\b{millions}[.,]?000[.,]?000\b", normalized)
    )


def transition_errors(record: dict[str, Any], response: str) -> list[str]:
    if not response.strip():
        return ["phản hồi rỗng"]
    category = record["category"]
    normalized = normalize(response)
    expected = normalize(record["messages"][-1]["content"])
    old_user = normalize(record["messages"][1]["content"])
    old_destination_match = re.search(r"dang di (.+?) 3 ngay", old_user)
    old_destination = old_destination_match.group(1) if old_destination_match else ""
    errors: list[str] = []

    if category == "destination_switch_v8":
        match = re.search(r"diem den (.+?) va bo", expected)
        new_destination = match.group(1) if match else ""
        if new_destination and new_destination not in normalized:
            errors.append("không xác nhận điểm đến mới")
        if old_destination and old_destination in normalized:
            errors.append("còn nhắc điểm đến cũ")
        if "3 ngay" in normalized or contains_money(response, 10):
            errors.append("còn giữ slot của chuyến cũ")
    elif category == "region_switch_v8":
        match = re.search(r"chuyen moi o (.+?) va bo", expected)
        new_region = match.group(1) if match else ""
        if new_region and new_region not in normalized:
            errors.append("không xác nhận vùng mới")
        if old_destination and old_destination in normalized:
            errors.append("còn giữ điểm đến cũ")
        if "3 ngay" in normalized or contains_money(response, 10):
            errors.append("còn giữ slot của chuyến cũ")
    elif category == "slot_correction_v8":
        if old_destination and old_destination not in normalized:
            errors.append("làm mất điểm đến hiện tại")
        for marker, label in (("3 ngay", "thời lượng"), ("3 nguoi", "số người")):
            if marker not in normalized:
                errors.append(f"không giữ/cập nhật {label}")
        if not contains_money(response, 10):
            errors.append("làm mất ngân sách hiện tại")
    elif category == "explicit_reset_v8":
        reset_terms = ("xoa", "lam lai", "bat dau", "chuyen moi", "ke hoach moi")
        if not any(term in normalized for term in reset_terms):
            errors.append("không xác nhận reset")
        if old_destination and old_destination in normalized:
            errors.append("còn giữ điểm đến cũ")
        if "3 ngay" in normalized or contains_money(response, 10):
            errors.append("còn giữ slot của chuyến cũ")
    elif category == "same_trip_retention_v8":
        if old_destination and old_destination not in normalized:
            errors.append("làm mất điểm đến hiện tại")
        if "3 ngay" not in normalized or "2 nguoi" not in normalized:
            errors.append("làm mất thời lượng hoặc số người")
        if not contains_money(response, 10):
            errors.append("làm mất ngân sách hiện tại")
    return errors


def evaluate_transition_records(
    records: list[dict[str, Any]], predictions: dict[str, str]
) -> dict[str, Any]:
    totals: Counter[str] = Counter()
    passed: Counter[str] = Counter()
    cases: list[dict[str, Any]] = []
    for record in records:
        category = record.get("category", "")
        if category not in TRANSITION_CATEGORIES:
            continue
        totals[category] += 1
        errors = transition_errors(record, predictions.get(record["id"], ""))
        if not errors:
            passed[category] += 1
        cases.append({"id": record["id"], "category": category, "passed": not errors, "errors": errors})
    total = sum(totals.values())
    passed_total = sum(passed.values())
    return {
        "records": total,
        "passed": passed_total,
        "passRate": round(passed_total / total, 4) if total else None,
        "categories": {
            category: {
                "passed": passed[category],
                "total": totals[category],
                "rate": round(passed[category] / totals[category], 4),
            }
            for category in sorted(totals)
        },
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Đánh giá chuyển trạng thái hội thoại v8")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, dataset_errors = load_and_validate(args.dataset, require_metadata=True)
    predictions, prediction_errors = load_predictions(args.predictions)
    errors = [*dataset_errors, *prediction_errors]
    if errors:
        raise SystemExit("\n".join(errors))
    report = evaluate_transition_records(records, predictions)
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(report_text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
