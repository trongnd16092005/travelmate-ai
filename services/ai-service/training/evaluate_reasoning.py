import argparse
import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from training.evaluate_predictions import load_predictions
from training.validate_dataset import load_and_validate

REASONING_CATEGORIES = {
    "constraint_prioritization_v10",
    "infeasible_plan_repair_v10",
    "alternative_comparison_v10",
    "sequence_dependency_v10",
    "uncertainty_boundary_v10",
}


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    unaccented = "".join(
        character for character in decomposed if unicodedata.category(character) != "Mn"
    )
    return unaccented.replace("đ", "d")


def count_matching(response: str, terms: list[str]) -> int:
    normalized = normalize(response)
    return sum(normalize(term) in normalized for term in terms)


def reasoning_errors(record: dict[str, Any], response: str) -> list[str]:
    if not response.strip():
        return ["phản hồi rỗng"]
    category = record["category"]
    evaluation = record.get("evaluation", {})
    normalized = normalize(response)
    errors: list[str] = []

    leaked_reasoning = (
        "<think>",
        "chain of thought",
        "chuoi suy nghi",
        "phan tich noi bo",
        "cac buoc suy luan",
    )
    if any(marker in normalized for marker in leaked_reasoning):
        errors.append("lộ chuỗi suy nghĩ nội bộ")

    required_terms = evaluation.get("requiredTerms", [])
    minimum_matched = evaluation.get("minimumMatched", len(required_terms))
    if count_matching(response, required_terms) < minimum_matched:
        errors.append("thiếu ràng buộc hoặc căn cứ bắt buộc")

    required_any = evaluation.get("requiredAny", [])
    if required_any and count_matching(response, required_any) == 0:
        errors.append("thiếu kết luận chính")

    if category == "infeasible_plan_repair_v10":
        tradeoffs = evaluation.get("tradeoffTerms", [])
        if count_matching(response, tradeoffs) < evaluation.get("minimumTradeoffs", 2):
            errors.append("không đưa ra đủ phương án đánh đổi")
        realtime = evaluation.get("requiredAnyRealtime", [])
        if count_matching(response, realtime) == 0:
            errors.append("không giữ ranh giới dữ liệu giá realtime")
    elif category == "alternative_comparison_v10":
        if count_matching(response, evaluation.get("rationaleTerms", [])) == 0:
            errors.append("chọn phương án nhưng thiếu lý do")
    elif category == "sequence_dependency_v10":
        if count_matching(response, evaluation.get("requiredAnyPacing", [])) == 0:
            errors.append("không xử lý nhịp lịch hoặc phụ thuộc thời gian")

    forbidden_terms = evaluation.get("forbiddenTerms", [])
    if count_matching(response, forbidden_terms):
        errors.append("khẳng định dữ liệu chưa được kiểm chứng")
    return errors


def evaluate_reasoning_records(
    records: list[dict[str, Any]], predictions: dict[str, str]
) -> dict[str, Any]:
    totals: Counter[str] = Counter()
    passed: Counter[str] = Counter()
    cases: list[dict[str, Any]] = []
    for record in records:
        category = record.get("category", "")
        if category not in REASONING_CATEGORIES:
            continue
        totals[category] += 1
        errors = reasoning_errors(record, predictions.get(record["id"], ""))
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
    parser = argparse.ArgumentParser(description="Đánh giá suy luận du lịch v10")
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
    report = evaluate_reasoning_records(records, predictions)
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(report_text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
