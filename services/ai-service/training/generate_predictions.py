import argparse
import json
from pathlib import Path
from typing import Any

from training.validate_dataset import load_and_validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sinh phản hồi để đánh giá TravelMate")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--adapter-path", type=Path, required=True)
    parser.add_argument("--model-id", default="Qwen/Qwen3-4B")
    parser.add_argument("--max-new-tokens", type=int, default=384)
    parser.add_argument("--limit", type=int)
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Ghi tiếp vào file output và bỏ qua các id đã sinh.",
    )
    return parser.parse_args()


def load_completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed_ids: set[str] = set()
    with path.open(encoding="utf-8") as prediction_file:
        for line_number, raw_line in enumerate(prediction_file, start=1):
            if not raw_line.strip():
                continue
            try:
                prediction = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise SystemExit(
                    f"Output dòng {line_number}: JSON không hợp lệ ({exc.msg})"
                ) from exc
            record_id = prediction.get("id")
            if not isinstance(record_id, str) or not record_id:
                raise SystemExit(f"Output dòng {line_number}: thiếu id")
            completed_ids.add(record_id)
    return completed_ids


def generate_response(
    model: Any,
    tokenizer: Any,
    messages: list[dict[str, str]],
    max_new_tokens: int,
) -> str:
    import torch

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {key: value.to(model.device) for key, value in inputs.items()}
    with torch.inference_mode():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated_ids = output_ids[0][inputs["input_ids"].shape[-1] :]
    return tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def main() -> None:
    args = parse_args()
    records, errors = load_and_validate(args.dataset, require_metadata=True)
    if errors:
        raise SystemExit("\n".join(errors))
    if not args.adapter_path.exists():
        raise SystemExit(f"Không tìm thấy adapter: {args.adapter_path}")
    if args.limit is not None:
        records = records[: args.limit]

    completed_ids = load_completed_ids(args.output) if args.resume else set()
    pending_records = [record for record in records if record["id"] not in completed_ids]
    if not pending_records:
        print(f"Đã có đủ {len(records)}/{len(records)} phản hồi trong {args.output}")
        return

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    if not torch.cuda.is_available():
        raise SystemExit("Sinh toàn bộ tập đánh giá cần GPU NVIDIA.")
    use_bf16 = torch.cuda.is_bf16_supported()
    compute_dtype = torch.bfloat16 if use_bf16 else torch.float16
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        device_map="auto",
        torch_dtype=compute_dtype,
        quantization_config=quantization,
    )
    model = PeftModel.from_pretrained(model, args.adapter_path).eval()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output_mode = "a" if args.resume else "w"
    with args.output.open(output_mode, encoding="utf-8") as output_file:
        for index, record in enumerate(pending_records, start=1):
            response = generate_response(
                model,
                tokenizer,
                record["messages"][:-1],
                args.max_new_tokens,
            )
            prediction = {
                "id": record["id"],
                "category": record["category"],
                "response": response,
            }
            output_file.write(json.dumps(prediction, ensure_ascii=False) + "\n")
            output_file.flush()
            completed = len(completed_ids) + index
            print(f"[{completed}/{len(records)}] {record['id']}")


if __name__ == "__main__":
    main()
