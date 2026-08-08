import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from training.evaluate_predictions import load_predictions
from training.validate_dataset import load_and_validate

UX_CATEGORIES = {
    "multi_slot_followup_v9",
    "correction_echo_v9",
    "retention_echo_v9",
    "clean_switch_v9",
    "natural_clarification_v9",
}


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.casefold())
    unaccented = "".join(
        character for character in decomposed if unicodedata.category(character) != "Mn"
    )
    return unaccented.replace("đ", "d")


def has_money(response: str, millions: int) -> bool:
    normalized = normalize(response)
    return bool(
        re.search(rf"\b{millions}\s*(?:trieu|tr)\b", normalized)
        or re.search(rf"\b{millions}[.,]?000[.,]?000\b", normalized)
    )


def numeric_markers(text: str) -> dict[str, int]:
    normalized = normalize(text)
    markers: dict[str, int] = {}
    for key, suffix in (("days", "ngay"), ("people", "nguoi"), ("budget", "trieu")):
        match = re.search(rf"\b(\d+)\s*{suffix}\b", normalized)
        if match:
            markers[key] = int(match.group(1))
    return markers


def require_markers(response: str, markers: dict[str, int]) -> list[str]:
    normalized = normalize(response)
    errors: list[str] = []
    if "days" in markers and f"{markers['days']} ngay" not in normalized:
        errors.append("không nhắc đúng thời lượng")
    if "people" in markers and f"{markers['people']} nguoi" not in normalized:
        errors.append("không nhắc đúng số người")
    if "budget" in markers and not has_money(response, markers["budget"]):
        errors.append("không nhắc đúng ngân sách")
    return errors


def asks_for_destination(response: str) -> bool:
    normalized = normalize(response)
    destination_phrases = (
        "diem den",
        "khu vuc",
        "di dau",
        "noi dau",
        "noi nao",
        "cho nao",
    )
    return "?" in response and any(phrase in normalized for phrase in destination_phrases)


def mentions_stale_destination(response: str, old_destination: str) -> bool:
    normalized = normalize(response)
    if not old_destination or old_destination not in normalized:
        return False
    discard_pattern = rf"(?:bo|xoa|huy|khong con)(?:\s+\S+){{0,5}}\s+{re.escape(old_destination)}"
    return re.search(discard_pattern, normalized) is None


def ux_errors(record: dict[str, Any], response: str) -> list[str]:
    if not response.strip():
        return ["phản hồi rỗng"]
    category = record["category"]
    normalized = normalize(response)
    expected = record["messages"][-1]["content"]
    old_user = normalize(record["messages"][1]["content"])
    errors: list[str] = []

    if category == "multi_slot_followup_v9":
        destination_match = re.search(r"muon di (.+?)\.", old_user)
        destination = destination_match.group(1) if destination_match else ""
        if destination and destination not in normalized:
            errors.append("làm mất điểm đến")
        errors.extend(require_markers(response, numeric_markers(expected)))
        if "?" not in response:
            errors.append("không hỏi slot tiếp theo")
    elif category in {"correction_echo_v9", "retention_echo_v9"}:
        destination_match = re.search(r"minh di (.+?) 3 ngay", old_user)
        destination = destination_match.group(1) if destination_match else ""
        if destination and destination not in normalized:
            errors.append("làm mất điểm đến hiện tại")
        errors.extend(require_markers(response, numeric_markers(expected)))
    elif category == "clean_switch_v9":
        old_match = re.search(r"minh di (.+?) 3 ngay", old_user)
        target_match = re.search(r"tai (.+?) va bo", normalize(expected))
        old_destination = old_match.group(1) if old_match else ""
        target = target_match.group(1) if target_match else ""
        if target and target not in normalized:
            errors.append("không xác nhận điểm đến mới")
        if mentions_stale_destination(response, old_destination):
            errors.append("còn nhắc điểm đến cũ")
        if "3 ngay" in normalized or "2 nguoi" in normalized or has_money(response, 10):
            errors.append("còn giữ slot chuyến cũ")
    elif category == "natural_clarification_v9":
        prompt = record["messages"][-2]["content"]
        errors.extend(require_markers(response, numeric_markers(prompt)))
        if not asks_for_destination(response):
            errors.append("không hỏi điểm đến tự nhiên")
        if "kiem tra nguon hien tai" in normalized:
            errors.append("diễn đạt máy móc")
    return errors


def evaluate_ux_records(
    records: list[dict[str, Any]], predictions: dict[str, str]
) -> dict[str, Any]:
    totals: Counter[str] = Counter()
    passed: Counter[str] = Counter()
    cases: list[dict[str, Any]] = []
    for record in records:
        category = record.get("category", "")
        if category not in UX_CATEGORIES:
            continue
        totals[category] += 1
        errors = ux_errors(record, predictions.get(record["id"], ""))
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
    parser = argparse.ArgumentParser(description="Đánh giá độ tự nhiên và giữ state v9")
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
    report = evaluate_ux_records(records, predictions)
    report_text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(report_text, end="")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report_text, encoding="utf-8")


if __name__ == "__main__":
    main()
