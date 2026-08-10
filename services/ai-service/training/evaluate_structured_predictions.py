import argparse
import json
import re
from pathlib import Path
from typing import Any

from training.evaluate_predictions import load_predictions
from training.validate_dataset import load_and_validate

ALLOWED_PERIODS = {"morning", "afternoon", "evening"}
ALLOWED_KINDS = {"visit", "meal", "rest", "travel", "free_time"}


def parse_contract(user_prompt: str) -> tuple[int, set[str]]:
    duration_match = re.search(r"Số ngày:\s*(\d+)", user_prompt)
    if not duration_match:
        raise ValueError("prompt thiếu số ngày")
    allowed_ids = {
        place_id.strip()
        for place_id in re.findall(r"^- ([^|\n]+)\s*\|", user_prompt, re.MULTILINE)
    }
    return int(duration_match.group(1)), allowed_ids


def validate_structured_response(record: dict[str, Any], response: str) -> list[str]:
    errors: list[str] = []
    try:
        value = json.loads(response)
    except json.JSONDecodeError as exc:
        return [f"JSON không hợp lệ: {exc.msg}"]
    if not isinstance(value, dict) or set(value) != {"days"}:
        return ["root phải chỉ có field days"]
    days = value.get("days")
    if not isinstance(days, list):
        return ["days phải là danh sách"]

    duration, allowed_ids = parse_contract(record["messages"][-2]["content"])
    actual_days = [day.get("day") for day in days if isinstance(day, dict)]
    if actual_days != list(range(1, duration + 1)):
        errors.append("số ngày hoặc thứ tự ngày không đúng")

    for day_index, day in enumerate(days, start=1):
        if not isinstance(day, dict) or set(day) != {"day", "activities"}:
            errors.append(f"ngày {day_index}: schema không đúng")
            continue
        activities = day.get("activities")
        if not isinstance(activities, list) or not 1 <= len(activities) <= 3:
            errors.append(f"ngày {day_index}: cần 1-3 hoạt động")
            continue
        periods: set[str] = set()
        for activity_index, activity in enumerate(activities, start=1):
            label = f"ngày {day_index}, hoạt động {activity_index}"
            if not isinstance(activity, dict) or set(activity) != {"period", "kind", "placeId"}:
                errors.append(f"{label}: schema không đúng")
                continue
            period = activity.get("period")
            kind = activity.get("kind")
            place_id = activity.get("placeId")
            if period not in ALLOWED_PERIODS:
                errors.append(f"{label}: period không hợp lệ")
            elif period in periods:
                errors.append(f"{label}: period bị lặp")
            else:
                periods.add(period)
            if kind not in ALLOWED_KINDS:
                errors.append(f"{label}: kind không hợp lệ")
            elif kind == "visit" and place_id not in allowed_ids:
                errors.append(f"{label}: placeId ngoài danh mục")
            elif kind != "visit" and place_id is not None:
                errors.append(f"{label}: kind không phải visit nhưng có placeId")
    return errors


def evaluate_structured_records(
    records: list[dict[str, Any]],
    predictions: dict[str, str],
) -> dict[str, Any]:
    structured_categories = {
        "structured_itinerary_v3",
        "expanded_structured_itinerary_v6",
        "nationwide_structured_itinerary_v11",
    }
    structured_records = [
        record for record in records if record.get("category") in structured_categories
    ]
    cases: list[dict[str, Any]] = []
    passed = 0
    for record in structured_records:
        response = predictions.get(record["id"])
        if response is None:
            errors = ["thiếu prediction"]
        else:
            errors = validate_structured_response(record, response)
        if not errors:
            passed += 1
        cases.append({"id": record["id"], "passed": not errors, "errors": errors})
    total = len(structured_records)
    return {
        "records": total,
        "passed": passed,
        "passRate": round(passed / total, 4) if total else None,
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Đánh giá JSON itinerary có grounding")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, dataset_errors = load_and_validate(args.dataset, require_metadata=True)
    predictions, prediction_errors = load_predictions(args.predictions)
    errors = dataset_errors + prediction_errors
    if errors:
        raise SystemExit("\n".join(errors))
    report = evaluate_structured_records(records, predictions)
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(report_text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
