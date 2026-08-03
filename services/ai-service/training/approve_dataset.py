import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from training.evaluate_predictions import evaluate_records
from training.generate_synthetic_dataset import generate_records
from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate

EXPECTED_CATEGORY_COUNTS = {
    "itinerary": 300,
    "budget": 240,
    "accommodation": 200,
    "food": 120,
    "safety_weather": 120,
    "realtime_limit": 80,
    "out_of_scope": 80,
    "action_boundary": 60,
}

REVIEW_SOURCES = [
    "https://vietnam.travel/site-map",
    "https://vietnam.travel/places-to-go/central-vietnam",
    "https://vietnam.travel/node/20",
    "https://vietnam.travel/things-to-do/must-visit-places-in-da-nang",
    "https://www.vietnam.travel/things-to-do/discovering-cao-bang-7-must-do-experiences",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_records(records: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    expected_records = generate_records()
    record_ids = [record["id"] for record in records]
    prompts = [record["messages"][-2]["content"].strip().casefold() for record in records]
    responses = [record["messages"][-1]["content"].strip().casefold() for record in records]
    systems = [record["messages"][0]["content"].strip() for record in records]
    response_word_counts = [len(response.split()) for response in responses]
    categories = Counter(record["category"] for record in records)
    review_batches = Counter(record.get("reviewBatch") for record in records)
    reference_predictions = {record["id"]: record["messages"][-1]["content"] for record in records}
    behavior_report = evaluate_records(records, reference_predictions)

    checks = {
        "recordCount": len(records) == 1200,
        "categoryDistribution": dict(categories) == EXPECTED_CATEGORY_COUNTS,
        "uniqueIds": len(set(record_ids)) == len(records),
        "uniqueUserPrompts": len(set(prompts)) == len(records),
        "uniqueAssistantResponses": len(set(responses)) == len(records),
        "singleSystemPrompt": len(set(systems)) == 1,
        "reviewBatches": review_batches == Counter({batch: 100 for batch in range(1, 13)}),
        "draftStatus": all(
            record.get("reviewStatus") == "synthetic_draft_v1" for record in records
        ),
        "responseLength": bool(response_word_counts)
        and min(response_word_counts) >= 20
        and max(response_word_counts) <= 100,
        "behaviorRules": behavior_report["behaviorPassRate"] == 1.0,
        "generatorMatch": records == expected_records,
    }
    errors.extend(name for name, passed in checks.items() if not passed)

    report = {
        "status": "passed" if not errors else "failed",
        "checks": checks,
        "recordCount": len(records),
        "categories": dict(sorted(categories.items())),
        "reviewBatches": {str(batch): review_batches[batch] for batch in range(1, 13)},
        "uniqueAssistantResponses": len(set(responses)),
        "responseWords": {
            "minimum": min(response_word_counts) if response_word_counts else 0,
            "maximum": max(response_word_counts) if response_word_counts else 0,
            "average": (
                round(sum(response_word_counts) / len(response_word_counts), 2)
                if response_word_counts
                else 0
            ),
        },
        "behaviorEvaluation": behavior_report,
        "tourismReferenceSources": REVIEW_SOURCES,
        "limitations": [
            "Dữ liệu được duyệt theo template, schema và rule; chưa có đánh giá độc lập từ người dùng.",
            "Giá, rating, giờ mở cửa và tình trạng phòng không được xem là dữ liệu tĩnh.",
            "Cần đánh giá thủ công phản hồi model trên tập Test sau khi fine-tune.",
        ],
        "errors": errors,
    }
    return report, errors


def approve_records(
    records: list[dict[str, Any]],
    approved_at: str,
) -> list[dict[str, Any]]:
    approved: list[dict[str, Any]] = []
    for record in records:
        approved_record = dict(record)
        approved_record["reviewStatus"] = "approved"
        approved_record["reviewMethod"] = "template_schema_rule_audit_v1"
        approved_record["approvedAt"] = approved_at
        approved.append(approved_record)
    return approved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit và phê duyệt dataset TravelMate v1")
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--approved-at", required=True, help="Ngày phê duyệt theo YYYY-MM-DD")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, validation_errors = load_and_validate(args.draft, require_metadata=True)
    report, audit_errors = audit_records(records)
    errors = validation_errors + audit_errors
    if errors:
        report["status"] = "failed"
        report["errors"] = errors
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise SystemExit("Audit dataset thất bại: " + ", ".join(errors))

    approved_records = approve_records(records, args.approved_at)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output, approved_records)
    report.update(
        {
            "approvedAt": args.approved_at,
            "reviewMethod": "template_schema_rule_audit_v1",
            "draftFile": args.draft.name,
            "draftSha256": sha256(args.draft),
            "approvedFile": args.output.name,
            "approvedSha256": sha256(args.output),
        }
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Đã phê duyệt {len(approved_records)} mẫu vào {args.output}")
    print(f"Báo cáo audit: {args.report}")


if __name__ == "__main__":
    main()
