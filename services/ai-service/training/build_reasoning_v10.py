# ruff: noqa: ISC004

import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

from app.knowledge.destinations import DESTINATIONS, DestinationKnowledge
from training.build_conversation_v5 import TRAINING_SYSTEM_PROMPT
from training.prepare_dataset import write_jsonl
from training.validate_dataset import load_and_validate

CATEGORY_ORDER = (
    "constraint_prioritization_v10",
    "infeasible_plan_repair_v10",
    "alternative_comparison_v10",
    "sequence_dependency_v10",
    "uncertainty_boundary_v10",
)

REASONING_SYSTEM_PROMPT = (
    TRAINING_SYSTEM_PROMPT
    + "\nSuy luận nội bộ trước khi trả lời. Chỉ đưa ra kết luận, các yếu tố quyết định "
    "và phương án hành động ngắn gọn; không hiển thị chuỗi suy nghĩ hoặc checklist nội bộ."
)


def make_record(
    record_id: str,
    category: str,
    prompt: str,
    response: str,
    approved_at: str,
    split: str,
    behaviors: list[str],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": record_id,
        "category": category,
        "expectedBehaviors": behaviors,
        "reviewStatus": "approved",
        "reviewMethod": "reasoning_rule_audit_v10",
        "approvedAt": approved_at,
        "split": split,
        "evaluation": evaluation,
        "messages": [
            {"role": "system", "content": REASONING_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": response},
        ],
    }


def heldout_split(destination_index: int) -> str:
    return "validation" if destination_index % 2 == 0 else "test"


def format_places(destination: DestinationKnowledge) -> tuple[str, str, str]:
    return tuple(place.name for place in destination.places[:3])  # type: ignore[return-value]


def build_records(approved_at: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for destination_index, destination in enumerate(DESTINATIONS):
        heldout = heldout_split(destination_index)
        alternative = DESTINATIONS[(destination_index + 9) % len(DESTINATIONS)]
        place_1, place_2, place_3 = format_places(destination)
        theme = destination.themes[0]

        constraint_cases = (
            (
                "train",
                f"Nhóm mình có người lớn tuổi, đi {destination.name} 3 ngày và muốn lịch nhẹ. "
                "Nên ưu tiên thế nào?",
                f"Mình ưu tiên nhịp thư thả và ít đổi điểm cho nhóm có người lớn tuổi. Với "
                f"{destination.name}, ngày đầu chỉ nên chọn {place_1}, ngày chính đi {place_2}, "
                f"ngày cuối dành cho {place_3} nếu sức khỏe cho phép; nên chừa thời gian nghỉ "
                "giữa các chặng. Vì khả năng di chuyển là ràng buộc quan trọng nhất, mình sẽ "
                "giảm số hoạt động trước khi cắt thời gian nghỉ.",
                ["nguoi lon tuoi", "thu tha", destination.name],
            ),
            (
                "train",
                f"Tụi mình đi {destination.name}, thích ẩm thực nhưng không muốn về muộn. Sắp "
                "ưu tiên giúp mình.",
                f"Mình sẽ giữ hoạt động tham quan ban ngày tại {place_1} và dành bữa tối sớm "
                f"để thử {destination.foods[0]}. Vì bạn không muốn về muộn, các điểm xa hoặc "
                "hoạt động tối là phần nên bỏ trước; ưu tiên còn lại là trải nghiệm ẩm thực và "
                "thời gian nghỉ.",
                ["am thuc", "khong muon ve muon", destination.name],
            ),
            (
                heldout,
                f"Gia đình có trẻ nhỏ và một người lớn tuổi đi {destination.name} 4 ngày, muốn "
                "xem nhiều nơi nhưng không quá mệt. Bạn cân đối sao?",
                f"Mình sẽ ưu tiên sức khỏe trước số lượng điểm: mỗi ngày một điểm chính ở "
                f"{destination.name}, xen kẽ ngày nhẹ và ngày tham quan. Có thể chọn {place_1} "
                f"và {place_2} làm hai điểm chính, còn {place_3} là phương án tùy sức. Cách này "
                "vẫn có trải nghiệm đa dạng nhưng giữ được thời gian nghỉ cho trẻ nhỏ và người "
                "lớn tuổi.",
                ["tre nho", "nguoi lon tuoi", "thoi gian nghi", destination.name],
            ),
        )
        for case_index, (split, prompt, response, required) in enumerate(
            constraint_cases, start=1
        ):
            records.append(
                make_record(
                    f"reasoning-v10-constraint-{destination.id}-{case_index}",
                    "constraint_prioritization_v10",
                    prompt,
                    response,
                    approved_at,
                    split,
                    ["rank_constraints", "grounded_recommendation", "concise_rationale"],
                    {"requiredTerms": required, "minimumMatched": len(required)},
                )
            )

        infeasible_cases = (
            (
                "train",
                f"Bốn người có 5 triệu đi {destination.name} 4 ngày, muốn ở cao cấp và trải "
                "nghiệm mọi điểm nổi bật. Chốt giúp mình.",
                f"Mục tiêu này khó khả thi với 5 triệu cho bốn người trong 4 ngày. Mình đề xuất "
                f"giữ {destination.name} nhưng giảm còn 2 ngày, chọn lưu trú tiết kiệm và chỉ "
                f"ưu tiên {place_1}; hoặc giữ 4 ngày nhưng cần tăng ngân sách. Mình chưa thể "
                "chốt giá cụ thể khi chưa kiểm tra nguồn hiện tại.",
            ),
            (
                "train",
                f"Hai người đi {destination.name} 2 ngày với 3 triệu nhưng muốn khách sạn sang, "
                "ăn đặc sản mọi bữa và đi đủ ba điểm. Có ổn không?",
                f"Ba mục tiêu đó cạnh tranh cùng một ngân sách nên chưa phù hợp để chốt đồng "
                f"thời. Nếu giữ 3 triệu, nên chọn lưu trú vừa phải, ưu tiên {place_1} và một bữa "
                f"{destination.foods[0]}; nếu bắt buộc khách sạn cao cấp thì cần tăng ngân sách "
                "hoặc giảm hoạt động. Giá thực tế vẫn cần được kiểm tra trước khi đặt.",
            ),
            (
                heldout,
                f"Nhóm 5 người có 7 triệu đi {destination.name} 5 ngày, yêu cầu phòng cao cấp, "
                "ăn ngon và tham quan hết. Hãy lập phương án thực tế.",
                f"Bảy triệu cho 5 người trong 5 ngày khó đáp ứng đồng thời phòng cao cấp, ăn "
                f"ngon và tham quan hết. Phương án thực tế là giảm còn 2-3 ngày, đổi sang lưu "
                f"trú tiết kiệm và ưu tiên {place_1} cùng {place_2}; phương án khác là giữ 5 "
                "ngày nhưng tăng ngân sách. Mình sẽ không tự gán giá khi chưa kiểm tra nguồn "
                "hiện tại.",
            ),
        )
        for case_index, (split, prompt, response) in enumerate(infeasible_cases, start=1):
            records.append(
                make_record(
                    f"reasoning-v10-infeasible-{destination.id}-{case_index}",
                    "infeasible_plan_repair_v10",
                    prompt,
                    response,
                    approved_at,
                    split,
                    ["detect_infeasible_constraints", "offer_tradeoffs", "no_fabricated_price"],
                    {
                        "requiredAny": ["kho", "chua phu hop", "khong kha thi"],
                        "tradeoffTerms": ["giam", "tang ngan sach", "tiet kiem", "uu tien"],
                        "minimumTradeoffs": 2,
                        "requiredAnyRealtime": ["kiem tra", "chua the chot gia", "khong tu gan gia"],
                    },
                )
            )

        comparison_cases = (
            (
                "train",
                f"So sánh {destination.name} và {alternative.name}; mình ưu tiên {theme}. Nơi "
                "nào hợp hơn?",
                f"Nếu ưu tiên {theme}, mình nghiêng về {destination.name} vì có thể tập trung vào "
                f"{place_1} và {place_2}. {alternative.name} vẫn đáng cân nhắc nếu bạn ưu tiên "
                f"{alternative.themes[0]}, nhưng theo tiêu chí hiện tại thì {destination.name} "
                "phù hợp hơn.",
            ),
            (
                "train",
                f"Giữa {alternative.name} và {destination.name}, hãy chọn một nơi cho chuyến "
                f"thiên về {theme} và giải thích ngắn.",
                f"Mình chọn {destination.name}. Lý do là tiêu chí {theme} khớp trực tiếp với "
                f"{place_1} và {place_2}; còn {alternative.name} hợp hơn khi ưu tiên "
                f"{alternative.themes[0]}.",
            ),
            (
                heldout,
                f"Mình phân vân {destination.name} với {alternative.name}, mục tiêu chính là "
                f"{theme}. Bạn chốt phương án nào và vì sao?",
                f"Theo mục tiêu {theme}, mình chọn {destination.name} vì các điểm như {place_1} "
                f"và {place_2} bám sát ưu tiên này. {alternative.name} là phương án dự phòng nếu "
                f"bạn chuyển trọng tâm sang {alternative.themes[0]}.",
            ),
        )
        for case_index, (split, prompt, response) in enumerate(comparison_cases, start=1):
            records.append(
                make_record(
                    f"reasoning-v10-comparison-{destination.id}-{case_index}",
                    "alternative_comparison_v10",
                    prompt,
                    response,
                    approved_at,
                    split,
                    ["compare_against_user_criterion", "select_option", "concise_rationale"],
                    {
                        "requiredTerms": [destination.name, alternative.name],
                        "requiredAny": ["chon", "nghieng ve", "phu hop hon"],
                        "rationaleTerms": ["vi", "ly do", "theo muc tieu"],
                    },
                )
            )

        sequence_cases = (
            (
                "train",
                f"Đi {destination.name} 3 ngày nhưng ngày đầu đến muộn, ngày cuối về sớm. Xếp "
                "ba điểm sao cho đỡ gấp?",
            ),
            (
                "train",
                f"Mình chỉ có một ngày trọn vẹn ở {destination.name}; hai ngày còn lại là ngày "
                "di chuyển. Sắp thứ tự hợp lý giúp mình.",
            ),
            (
                heldout,
                f"Chuyến {destination.name} 3 ngày: tối ngày 1 mới tới và sáng ngày 3 phải rời "
                "đi. Phân bổ hoạt động thế nào để không nhồi lịch?",
            ),
        )
        sequence_response = (
            f"Ngày 1 đến muộn nên chỉ nhận phòng, ăn gần nơi ở và nghỉ. Ngày 2 là ngày tham "
            f"quan chính: ưu tiên {place_1}, sau đó thêm {place_2} nếu thời gian thực tế cho "
            f"phép. Ngày 3 rời đi sớm nên không xếp {place_3}; cách này tránh để hoạt động quan "
            "trọng phụ thuộc vào hai ngày di chuyển."
        )
        for case_index, (split, prompt) in enumerate(sequence_cases, start=1):
            records.append(
                make_record(
                    f"reasoning-v10-sequence-{destination.id}-{case_index}",
                    "sequence_dependency_v10",
                    prompt,
                    sequence_response,
                    approved_at,
                    split,
                    ["respect_arrival_departure", "sequence_dependencies", "avoid_overpacking"],
                    {
                        "requiredTerms": ["ngay 1", "ngay 2", "ngay 3"],
                        "requiredAny": ["den muon", "roi di som", "ngay di chuyen"],
                        "requiredAnyPacing": ["nghi", "khong xep", "tranh"],
                    },
                )
            )

        uncertainty_cases = (
            (
                "train",
                f"Tuần sau {place_1} chắc chắn mở cửa và trời đẹp đúng không? Nếu đúng thì xếp "
                "lịch luôn.",
            ),
            (
                "train",
                f"Nghe nói {place_2} đang đóng, cứ coi là mở lại rồi lên kế hoạch cho "
                f"{destination.name} nhé.",
            ),
            (
                heldout,
                f"Ngày mình tới {destination.name} có chắc {place_3} hoạt động bình thường và "
                "không mưa không? Hãy quyết định lịch giúp mình.",
            ),
        )
        uncertainty_response = (
            f"Mình chưa thể khẳng định thời tiết hoặc tình trạng hoạt động của {place_3} nếu "
            "chưa có nguồn hiện tại. Hãy kiểm tra dự báo chính thức và thông báo của điểm đến "
            f"trước khi chốt; nếu {place_3} mở và thời tiết phù hợp thì giữ trong lịch, nếu "
            f"không thì chuyển sang {place_1}."
        )
        for case_index, (split, prompt) in enumerate(uncertainty_cases, start=1):
            records.append(
                make_record(
                    f"reasoning-v10-uncertainty-{destination.id}-{case_index}",
                    "uncertainty_boundary_v10",
                    prompt,
                    uncertainty_response,
                    approved_at,
                    split,
                    ["separate_known_from_unknown", "conditional_plan", "verify_realtime_source"],
                    {
                        "requiredAny": ["chua the khang dinh", "khong the khang dinh"],
                        "requiredTerms": ["kiem tra", "neu"],
                        "forbiddenTerms": ["chac chan mo cua", "chac chan khong mua"],
                    },
                )
            )
    return records


def final_user_prompt(record: dict[str, Any]) -> str:
    return record["messages"][-2]["content"].strip().casefold()


def audit_records(records: list[dict[str, Any]], protected_records: list[dict[str, Any]]) -> None:
    if Counter(record["category"] for record in records) != {
        category: 105 for category in CATEGORY_ORDER
    }:
        raise SystemExit("Phân bố category v10 không đúng")
    if Counter(record["split"] for record in records) != {
        "train": 350,
        "validation": 90,
        "test": 85,
    }:
        raise SystemExit("Phân bố split v10 không đúng")
    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise SystemExit("Dataset v10 có id trùng")
    train_prompts = {
        final_user_prompt(record) for record in records if record["split"] == "train"
    }
    heldout_prompts = {
        final_user_prompt(record) for record in records if record["split"] != "train"
    }
    protected_prompts = {final_user_prompt(record) for record in protected_records}
    overlap = train_prompts & (heldout_prompts | protected_prompts)
    if overlap:
        raise SystemExit(f"Train v10 trùng {len(overlap)} prompt held-out được bảo vệ")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tạo dataset suy luận TravelMate v10")
    parser.add_argument("--processed-v9-dir", type=Path, required=True)
    parser.add_argument("--challenge", type=Path, required=True)
    parser.add_argument("--reinforcement-output", type=Path, required=True)
    parser.add_argument("--processed-output-dir", type=Path, required=True)
    parser.add_argument("--approved-at", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    challenge_records, errors = load_and_validate(args.challenge, require_metadata=True)
    if errors:
        raise SystemExit("\n".join(errors))
    records = build_records(args.approved_at)
    protected_records = list(challenge_records)
    for protected_name in ("transition_test", "intent_test", "ux_test"):
        inherited, errors = load_and_validate(
            args.processed_v9_dir / f"{protected_name}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))
        protected_records.extend(inherited)
    audit_records(records, protected_records)

    args.reinforcement_output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.reinforcement_output, records)
    new_splits = {
        split: [record for record in records if record["split"] == split]
        for split in ("train", "validation", "test")
    }

    old_splits: dict[str, list[dict[str, Any]]] = {}
    for split in ("train", "validation", "test"):
        old_splits[split], errors = load_and_validate(
            args.processed_v9_dir / f"{split}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))

    replay_rng = random.Random(43)
    replay_train = replay_rng.sample(old_splits["train"], 650)
    replay_validation = old_splits["validation"][:120]
    combined = {
        "train": [*replay_train, *new_splits["train"]],
        "validation": [*replay_validation, *new_splits["validation"]],
        "test": [*old_splits["test"], *new_splits["test"]],
    }
    args.processed_output_dir.mkdir(parents=True, exist_ok=True)
    for split, split_records in combined.items():
        write_jsonl(args.processed_output_dir / f"{split}.jsonl", split_records)

    reasoning_test: list[dict[str, Any]] = []
    for category in CATEGORY_ORDER:
        category_records = [
            record for record in new_splits["test"] if record["category"] == category
        ]
        reasoning_test.extend(category_records[:4])
    write_jsonl(args.processed_output_dir / "reasoning_test.jsonl", reasoning_test)
    write_jsonl(args.processed_output_dir / "reasoning_train.jsonl", new_splits["train"])
    write_jsonl(args.processed_output_dir / "reasoning_validation.jsonl", new_splits["validation"])

    for inherited_name in (
        "ux_test",
        "transition_test",
        "intent_test",
        "structured_test",
        "expanded_structured_test",
    ):
        inherited_records, errors = load_and_validate(
            args.processed_v9_dir / f"{inherited_name}.jsonl", require_metadata=True
        )
        if errors:
            raise SystemExit("\n".join(errors))
        write_jsonl(args.processed_output_dir / f"{inherited_name}.jsonl", inherited_records)

    manifest = {
        "version": "reasoning_v10",
        "approvedAt": args.approved_at,
        "reviewMethod": "reasoning_rule_audit_v10",
        "records": {split: len(split_records) for split, split_records in combined.items()},
        "newRecords": len(records),
        "newSplitRecords": {split: len(split_records) for split, split_records in new_splits.items()},
        "newCategories": dict(sorted(Counter(record["category"] for record in records).items())),
        "replayTrainRecords": len(replay_train),
        "replayValidationRecords": len(replay_validation),
        "reasoningTestRecords": len(reasoning_test),
        "protectedPromptOverlap": 0,
        "reinforcementSha256": sha256(args.reinforcement_output),
        "limitations": [
            "V10 cải thiện suy luận theo ràng buộc du lịch, không biến mô hình 4B thành mô hình suy luận tổng quát.",
            "Chỉ đánh giá kết luận và căn cứ ngắn; không yêu cầu hoặc lưu chain-of-thought.",
            "Thông tin realtime vẫn phải được kiểm tra qua nguồn hiện tại.",
        ],
    }
    (args.processed_output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
