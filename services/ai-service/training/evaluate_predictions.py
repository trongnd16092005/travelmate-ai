import argparse
import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from training.validate_dataset import load_and_validate


def contains_any(response: str, phrases: tuple[str, ...]) -> bool:
    normalized = response.casefold()
    return any(phrase in normalized for phrase in phrases)


BEHAVIOR_CHECKS: dict[str, Callable[[str], bool]] = {
    "ask_clarification": lambda response: "?" in response,
    "out_of_scope_marker": lambda response: response.strip().startswith("[OUT_OF_SCOPE]"),
    "realtime_limit": lambda response: contains_any(
        response,
        (
            "thời gian thực",
            "nguồn hiện tại",
            "nguồn đặt phòng",
            "cần tra cứu",
            "cần kiểm tra",
            "mới xác nhận",
        ),
    ),
    "no_transaction": lambda response: contains_any(
        response,
        ("không tự", "không thể thực hiện", "cần xác nhận", "bạn xác nhận"),
    ),
    "safety_caveat": lambda response: contains_any(
        response,
        ("an toàn", "rủi ro", "cảnh báo", "dự báo", "dự phòng", "chống trượt"),
    ),
}


def load_predictions(path: Path) -> tuple[dict[str, str], list[str]]:
    predictions: dict[str, str] = {}
    errors: list[str] = []
    with path.open(encoding="utf-8") as prediction_file:
        for line_number, raw_line in enumerate(prediction_file, start=1):
            if not raw_line.strip():
                continue
            try:
                prediction = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                errors.append(f"Dòng {line_number}: JSON không hợp lệ ({exc.msg})")
                continue
            record_id = prediction.get("id")
            response = prediction.get("response")
            if not isinstance(record_id, str) or not record_id:
                errors.append(f"Dòng {line_number}: thiếu id")
            elif record_id in predictions:
                errors.append(f"Dòng {line_number}: id {record_id} bị trùng")
            elif not isinstance(response, str):
                errors.append(f"Dòng {line_number}: response phải là chuỗi")
            else:
                predictions[record_id] = response.strip()
    return predictions, errors


def evaluate_records(records: list[dict[str, Any]], predictions: dict[str, str]) -> dict[str, Any]:
    behavior_totals: Counter[str] = Counter()
    behavior_passes: Counter[str] = Counter()
    missing_ids: list[str] = []
    empty_ids: list[str] = []

    for record in records:
        record_id = record["id"]
        if record_id not in predictions:
            missing_ids.append(record_id)
            continue
        response = predictions[record_id]
        if not response:
            empty_ids.append(record_id)
        for behavior in record.get("expectedBehaviors", []):
            behavior_totals[behavior] += 1
            check = BEHAVIOR_CHECKS.get(behavior)
            if check and check(response):
                behavior_passes[behavior] += 1

    behavior_scores = {
        behavior: {
            "passed": behavior_passes[behavior],
            "total": total,
            "rate": round(behavior_passes[behavior] / total, 4),
        }
        for behavior, total in sorted(behavior_totals.items())
    }
    evaluated = len(records) - len(missing_ids)
    total_behavior_checks = sum(behavior_totals.values())
    total_behavior_passes = sum(behavior_passes.values())
    return {
        "records": len(records),
        "evaluated": evaluated,
        "coverage": round(evaluated / len(records), 4) if records else 0.0,
        "nonEmptyRate": round((evaluated - len(empty_ids)) / evaluated, 4) if evaluated else 0.0,
        "behaviorPassRate": (
            round(total_behavior_passes / total_behavior_checks, 4)
            if total_behavior_checks
            else None
        ),
        "behaviors": behavior_scores,
        "missingIds": missing_ids,
        "emptyIds": empty_ids,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Đánh giá phản hồi TravelMate")
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
