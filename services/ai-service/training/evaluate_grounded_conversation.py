import argparse
import json
import re
from pathlib import Path
from typing import Any

from app.knowledge.destinations import NATIONWIDE_DESTINATIONS, normalize_lookup_key
from training.evaluate_predictions import load_predictions
from training.validate_dataset import load_and_validate

PROVINCE_BY_CODE = {
    destination.id.split("-", 2)[1]: destination
    for destination in NATIONWIDE_DESTINATIONS
}


def evaluate_records(
    records: list[dict[str, Any]],
    predictions: dict[str, str],
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    metrics = {
        "currentProvince": 0,
        "allCatalogPlaces": 0,
        "realtimeBoundary": 0,
        "strictTemplate": 0,
    }
    passed = 0
    for record in records:
        response = predictions.get(record["id"], "")
        expected = record["messages"][-1]["content"]
        destination = PROVINCE_BY_CODE[record["provinceCode"]]
        normalized = normalize_lookup_key(response)
        current_province = normalize_lookup_key(destination.name) in normalized
        all_places = all(
            normalize_lookup_key(place.name) in normalized
            for place in destination.places
        )
        unsupported_realtime = bool(
            re.search(
                r"\b(?:\d{1,2}(?::\d{2}|h\d{0,2})|\d+[.]?\d*\s*(?:vnd|dong|nghin|trieu))\b",
                normalized,
            )
        ) or any(term in normalized for term in ("mien phi", "mo cua tu", "gia ve la"))
        realtime_boundary = not unsupported_realtime and any(
            term in normalized
            for term in ("nguon realtime", "nguon hien tai", "sau khi truy xuat nguon")
        )
        strict_template = normalize_lookup_key(expected) == normalized
        checks = {
            "currentProvince": current_province,
            "allCatalogPlaces": all_places,
            "realtimeBoundary": realtime_boundary,
            "strictTemplate": strict_template,
        }
        for key, result in checks.items():
            metrics[key] += int(result)
        case_passed = all(checks.values())
        passed += int(case_passed)
        cases.append(
            {
                "id": record["id"],
                "provinceCode": record["provinceCode"],
                "passed": case_passed,
                "checks": checks,
            }
        )
    total = len(records)
    return {
        "records": total,
        "passed": passed,
        "passRate": round(passed / total, 4) if total else None,
        "metrics": {
            key: {"passed": value, "total": total, "rate": round(value / total, 4)}
            for key, value in metrics.items()
        },
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Đánh giá grounded conversation v12")
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
    report = evaluate_records(records, predictions)
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(report_text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
