import argparse
import json
from pathlib import Path
from typing import Any

from app.knowledge.destinations import NATIONWIDE_DESTINATIONS, normalize_lookup_key
from training.evaluate_predictions import load_predictions
from training.evaluate_structured_predictions import validate_structured_response
from training.validate_dataset import load_and_validate

PROVINCE_BY_CODE = {
    destination.id.split("-", 2)[1]: destination
    for destination in NATIONWIDE_DESTINATIONS
}


def evaluate_nationwide_records(
    records: list[dict[str, Any]], predictions: dict[str, str]
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    passed = 0
    province_passes: set[str] = set()
    for record in records:
        errors: list[str] = []
        response = predictions.get(record["id"])
        code = record.get("provinceCode")
        destination = PROVINCE_BY_CODE.get(code)
        if response is None:
            errors.append("thiếu prediction")
        elif destination is None:
            errors.append("provinceCode không hợp lệ")
        elif record["category"] == "nationwide_structured_itinerary_v11":
            errors.extend(validate_structured_response(record, response))
        else:
            normalized_response = normalize_lookup_key(response)
            if normalize_lookup_key(destination.name) not in normalized_response:
                errors.append("không nhắc đúng tỉnh, thành hiện hành")
            if not any(
                marker in normalized_response
                for marker in ("kiem tra", "chua can chot gia", "realtime")
            ):
                errors.append("thiếu ranh giới dữ liệu realtime")
        if not errors:
            passed += 1
            province_passes.add(code)
        cases.append({"id": record["id"], "provinceCode": code, "passed": not errors, "errors": errors})
    total = len(records)
    return {
        "records": total,
        "passed": passed,
        "passRate": round(passed / total, 4) if total else None,
        "provinceCoveragePassed": len(province_passes),
        "provinceCoverageTotal": 34,
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Đánh giá độ phủ 34 tỉnh, thành v11")
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
    report = evaluate_nationwide_records(records, predictions)
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(report_text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
