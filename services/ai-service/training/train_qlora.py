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
    parser.add_argument(
        "--save-steps",
        type=int,
        default=20,
        help="Lưu checkpoint sau mỗi số bước này để có thể tiếp tục khi runtime bị reset.",
    )
    parser.add_argument("--resume-from-checkpoint", action="store_true")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Chạy model Qwen3 cực nhỏ ngẫu nhiên trên CPU để kiểm tra toàn bộ pipeline.",
    )
    parser.add_argument(
        "--allow-unreviewed-data",
        action="store_true",
        help="Cho phép train dữ liệu còn reviewStatus khác approved; chỉ dùng để thử pipeline.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Chỉ kiểm tra dữ liệu và cấu hình, không tải model hoặc dùng GPU.",
    )
    return parser.parse_args()


def validate_training_files(
    train_path: Path,
    eval_path: Path,
    allow_unreviewed_data: bool = False,
) -> tuple[int, int]:
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
    if not allow_unreviewed_data:
        unreviewed = [
            record["id"]
            for record in train_records + eval_records
            if "reviewStatus" in record and record["reviewStatus"] != "approved"
        ]
        if unreviewed:
            errors.append(
                f"Có {len(unreviewed)} mẫu chưa được duyệt; "
                "chỉ dùng --allow-unreviewed-data để smoke test."
            )
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
    estimated_steps = max(
        1,
        round(train_size * args.epochs / args.gradient_accumulation_steps),
    )
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
        "saveSteps": args.save_steps,
        "warmupSteps": max(1, round(estimated_steps * 0.05)),
        "smokeTest": args.smoke_test,
        "outputDir": str(args.output_dir),
    }


def main() -> None:
    args = parse_args()
    if args.save_steps < 1:
        raise SystemExit("--save-steps phải lớn hơn hoặc bằng 1")
    train_size, eval_size = validate_training_files(
        args.train_dataset,
        args.eval_dataset,
        args.allow_unreviewed_data,
    )
    run_summary = build_run_summary(args, train_size, eval_size)
    print(json.dumps(run_summary, ensure_ascii=False, indent=2))
    if args.dry_run:
        print("Dry-run thành công: chưa tải model và chưa sử dụng GPU.")
        return

    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, TrainerCallback
    from trl import SFTConfig, SFTTrainer

    if not args.smoke_test and not torch.cuda.is_available():
        raise SystemExit("QLoRA cần GPU NVIDIA. Hãy chạy script trên Google Colab hoặc Kaggle.")

    use_bf16 = not args.smoke_test and torch.cuda.is_bf16_supported()
    compute_dtype = torch.bfloat16 if use_bf16 else torch.float16

    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    if args.smoke_test:
        from transformers import Qwen3Config, Qwen3ForCausalLM

        smoke_config = Qwen3Config(
            vocab_size=len(tokenizer),
            hidden_size=64,
            intermediate_size=128,
            num_hidden_layers=2,
            num_attention_heads=4,
            num_key_value_heads=2,
            head_dim=16,
            max_position_embeddings=max(args.max_length, 128),
            tie_word_embeddings=True,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
        model = Qwen3ForCausalLM(smoke_config)
    else:
        quantization = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )
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
        warmup_steps=run_summary["warmupSteps"],
        max_length=args.max_length,
        completion_only_loss=True,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="steps",
        save_steps=args.save_steps,
        save_total_limit=3,
        gradient_checkpointing=not args.smoke_test,
        gradient_checkpointing_kwargs=({"use_reentrant": False} if not args.smoke_test else None),
        bf16=use_bf16,
        fp16=not use_bf16 and not args.smoke_test,
        optim="adamw_torch" if args.smoke_test else "paged_adamw_8bit",
        report_to="none",
        seed=42,
    )

    class FrequentCheckpointCallback(TrainerCallback):
        def on_step_end(self, args, state, control, **kwargs):
            if state.global_step > 0 and state.global_step % int(args.save_steps) == 0:
                control.should_save = True
            return control

    trainer = SFTTrainer(
        model=model,
        args=training_config,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        processing_class=tokenizer,
        peft_config=lora_config,
        callbacks=[FrequentCheckpointCallback()],
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
