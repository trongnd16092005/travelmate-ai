import argparse
import json
from pathlib import Path
from typing import Any

from training.validate_dataset import load_and_validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune TravelMate bằng QLoRA")
    parser.add_argument("--train-dataset", type=Path, required=True)
    parser.add_argument("--eval-dataset", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-id", default="Qwen/Qwen3-4B")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=8)
    parser.add_argument("--resume-from-checkpoint", action="store_true")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ kiểm tra dữ liệu và cấu hình, không tải model hoặc dùng GPU.",
    )
    return parser.parse_args()


def validate_training_files(train_path: Path, eval_path: Path) -> tuple[int, int]:
    train_records, train_errors = load_and_validate(train_path, require_metadata=True)
    eval_records, eval_errors = load_and_validate(eval_path, require_metadata=True)
    errors = [
        *(f"Train: {error}" for error in train_errors),
        *(f"Validation: {error}" for error in eval_errors),
    ]
    if len(train_records) < 2:
        errors.append("Train: cần ít nhất 2 hội thoại")
    if not eval_records:
        errors.append("Validation: cần ít nhất 1 hội thoại")
    if errors:
        raise SystemExit("\n".join(errors))
    return len(train_records), len(eval_records)


def to_prompt_completion(example: dict[str, Any]) -> dict[str, Any]:
    messages = example["messages"]
    return {
        "prompt": messages[:-1],
        "completion": [messages[-1]],
    }


def build_run_summary(args: argparse.Namespace, train_size: int, eval_size: int) -> dict[str, Any]:
    return {
        "modelId": args.model_id,
        "trainDataset": str(args.train_dataset),
        "evalDataset": str(args.eval_dataset),
        "trainRecords": train_size,
        "evalRecords": eval_size,
        "epochs": args.epochs,
        "maxLength": args.max_length,
        "learningRate": args.learning_rate,
        "gradientAccumulationSteps": args.gradient_accumulation_steps,
        "outputDir": str(args.output_dir),
    }


def main() -> None:
    args = parse_args()
    train_size, eval_size = validate_training_files(args.train_dataset, args.eval_dataset)
    run_summary = build_run_summary(args, train_size, eval_size)
    print(json.dumps(run_summary, ensure_ascii=False, indent=2))
    if args.dry_run:
        print("Dry-run thành công: chưa tải model và chưa sử dụng GPU.")
        return

    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    if not torch.cuda.is_available():
        raise SystemExit("QLoRA cần GPU NVIDIA. Hãy chạy script trên Google Colab hoặc Kaggle.")

    use_bf16 = torch.cuda.is_bf16_supported()
    compute_dtype = torch.bfloat16 if use_bf16 else torch.float16
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        device_map="auto",
        torch_dtype=compute_dtype,
        quantization_config=quantization,
    )
    model.config.use_cache = False

    raw_dataset = load_dataset(
        "json",
        data_files={
            "train": str(args.train_dataset),
            "validation": str(args.eval_dataset),
        },
    )
    train_dataset = raw_dataset["train"].map(
        to_prompt_completion,
        remove_columns=raw_dataset["train"].column_names,
    )
    eval_dataset = raw_dataset["validation"].map(
        to_prompt_completion,
        remove_columns=raw_dataset["validation"].column_names,
    )

    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )
    training_config = SFTConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        max_length=args.max_length,
        completion_only_loss=True,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        bf16=use_bf16,
        fp16=not use_bf16,
        optim="paged_adamw_8bit",
        report_to="none",
        seed=42,
    )
    trainer = SFTTrainer(
        model=model,
        args=training_config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        peft_config=lora_config,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "run_config.json").write_text(
        json.dumps(run_summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    train_result = trainer.train(resume_from_checkpoint=args.resume_from_checkpoint)
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(args.output_dir)
    trainer.save_metrics("train", train_result.metrics)
    trainer.save_metrics("eval", trainer.evaluate())
    print(f"Đã lưu LoRA adapter tại {args.output_dir}")


if __name__ == "__main__":
    main()
