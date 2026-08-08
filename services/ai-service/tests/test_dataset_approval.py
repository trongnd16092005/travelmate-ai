from training.approve_dataset import approve_records, audit_records
from training.generate_synthetic_dataset import generate_records


def test_generated_dataset_passes_approval_audit() -> None:
    report, errors = audit_records(generate_records())

    assert errors == []
    assert report["status"] == "passed"
    assert all(report["checks"].values())
    assert report["uniqueAssistantResponses"] == 1200
    assert report["behaviorEvaluation"]["behaviorPassRate"] == 1.0


def test_approve_records_preserves_content_and_marks_review() -> None:
    draft = generate_records()[:2]

    approved = approve_records(draft, "2026-08-03")

    assert approved[0]["messages"] == draft[0]["messages"]
    assert approved[0]["reviewStatus"] == "approved"
    assert approved[0]["reviewMethod"] == "template_schema_rule_audit_v1"
    assert approved[0]["approvedAt"] == "2026-08-03"
    assert draft[0]["reviewStatus"] == "synthetic_draft_v1"
