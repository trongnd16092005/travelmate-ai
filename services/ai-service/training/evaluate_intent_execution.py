import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from training.evaluate_predictions import load_predictions
from training.validate_dataset import load_and_validate

INTENT_CATEGORIES = {
    "itinerary_execution_v7",
    "budget_execution_v7",
    "checklist_execution_v7",
    "compound_execution_v7",
}


def execution_errors(category: str, response: str) -> list[str]:
    normalized = response.casefold()
    errors: list[str] = []
    if not response.strip():
        return ["phản hồi rỗng"]

    has_itinerary = "ngày 1" in normalized and "ngày 2" in normalized
    budget_terms = sum(
        term in normalized for term in ("lưu trú", "ăn uống", "di chuyển", "tham quan", "dự phòng")
    )
    has_budget = budget_terms >= 3 and len(re.findall(r"\d+%", response)) >= 3
    checklist_terms = sum(
        term in normalized
        for term in (
            "giấy tờ",
            "cccd",
            "thuốc",
            "trang phục",
            "quần áo",
            "sạc",
            "tiền mặt",
            "thẻ",
            "trước khi đi",
        )
    )
    has_checklist = checklist_terms >= 4

    if category in {"itinerary_execution_v7", "compound_execution_v7"} and not has_itinerary:
        errors.append("thiếu lịch theo ngày")
    if category in {"budget_execution_v7", "compound_execution_v7"} and not has_budget:
        errors.append("thiếu phân bổ ngân sách cụ thể")
    if category in {"checklist_execution_v7", "compound_execution_v7"} and not has_checklist:
        errors.append("thiếu checklist cụ thể")
    if "?" in response:
        errors.append("vẫn đặt câu hỏi thay vì thực thi")
    if "bạn muốn mình" in normalized and any(
        term in normalized for term in ("lập lịch", "phân bổ ngân sách", "checklist")
    ):
        errors.append("lặp lại menu lựa chọn")
    return errors


def evaluate_intent_records(
    records: list[dict[str, Any]], predictions: dict[str, str]
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    category_totals: Counter[str] = Counter()
    category_passed: Counter[str] = Counter()
    for record in records:
        category = record.get("category", "")
        if category not in INTENT_CATEGORIES:
            continue
        category_totals[category] += 1
        response = predictions.get(record["id"], "")
        errors = execution_errors(category, response)
        if not errors:
            category_passed[category] += 1
        cases.append({"id": record["id"], "category": category, "passed": not errors, "errors": errors})

    total = sum(category_totals.values())
    passed = sum(category_passed.values())
    return {
        "records": total,
        "passed": passed,
        "passRate": round(passed / total, 4) if total else None,
        "categories": {
            category: {
                "passed": category_passed[category],
                "total": category_totals[category],
                "rate": round(category_passed[category] / category_totals[category], 4),
            }
            for category in INTENT_CATEGORIES
            if category_totals[category]
        },
        "cases": cases,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Đánh giá khả năng thực thi intent v7")
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
    report = evaluate_intent_records(records, predictions)
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(report_text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
