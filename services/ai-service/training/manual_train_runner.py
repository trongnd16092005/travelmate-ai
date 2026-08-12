

from __future__ import annotations

import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class RunConfig:
    train_dataset: Path = Path(
        "training/data/processed/grounded_conversation_v12/"
        "grounded_conversation_train.jsonl"
    )
    validation_dataset: Path = Path(
        "training/data/processed/grounded_conversation_v12/"
        "grounded_conversation_validation.jsonl"
    )
    test_dataset: Path = Path(
        "training/data/processed/grounded_conversation_v12/"
        "grounded_conversation_test.jsonl"
    )
    init_adapter: Path = Path(
        "artifacts/travelmate-qwen3-4b-lora-v12-grounded-conversation-r3"
    )
    output_adapter: Path = Path("artifacts/travelmate-qwen3-4b-manual-candidate")
    predictions: Path = Path("training/outputs/manual_candidate_predictions.jsonl")
    report: Path = Path("training/outputs/manual_candidate_report.json")
    epochs: float = 1.0
    learning_rate: str = "5e-6"
    max_length: int = 512
    max_new_tokens: int = 192


def box(title: str, lines: list[str]) -> None:
    width = max([len(title), *(len(line) for line in lines)], default=0) + 4
    print("\n" + "=" * width)
    print(f"  {title}")
    print("-" * width)
    for line in lines:
        print(f"  {line}")
    print("=" * width)


def ask(label: str, default: str) -> str:
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def yes_no(question: str, *, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    answer = input(f"{question} [{hint}]: ").strip().casefold()
    if not answer:
        return default
    return answer in {"y", "yes", "c", "co", "có"}


def run_module(module: str, arguments: list[str]) -> bool:
    command = [sys.executable, "-m", module, *arguments]
    box("LỆNH SẮP CHẠY", [shlex.join(command)])
    result = subprocess.run(command, cwd=SERVICE_ROOT, check=False)
    if result.returncode == 0:
        print("\n✓ Hoàn tất thành công.")
        return True
    print(f"\n✗ Lệnh thất bại với exit code {result.returncode}.")
    return False


def configure(config: RunConfig) -> RunConfig:
    box(
        "HỘP THOẠI CẤU HÌNH",
        [
            "Nhấn Enter để giữ giá trị mặc định của pipeline v12.",
            "Output mặc định là candidate mới, không phải adapter production.",
        ],
    )
    config.train_dataset = Path(ask("File train", str(config.train_dataset)))
    config.validation_dataset = Path(
        ask("File validation", str(config.validation_dataset))
    )
    config.test_dataset = Path(ask("File held-out test", str(config.test_dataset)))
    config.init_adapter = Path(ask("Adapter khởi tạo", str(config.init_adapter)))
    config.output_adapter = Path(ask("Adapter candidate đầu ra", str(config.output_adapter)))
    config.predictions = Path(ask("File prediction", str(config.predictions)))
    config.report = Path(ask("File báo cáo", str(config.report)))
    config.epochs = float(ask("Số epoch", str(config.epochs)))
    config.learning_rate = ask("Learning rate", config.learning_rate)
    return config


def validate_paths(config: RunConfig) -> bool:
    box("HỘP THOẠI 1 — KIỂM TRA DỮ LIỆU", ["Kiểm tra train và validation JSONL."])
    for path in (config.train_dataset, config.validation_dataset):
        if not run_module(
            "training.validate_dataset",
            [
                str(path),
                "--minimum-records",
                "1",
                "--require-metadata",
                "--require-review-status",
                "approved",
            ],
        ):
            return False
    return True


def dry_run(config: RunConfig) -> bool:
    box(
        "HỘP THOẠI 2 — DRY-RUN",
        ["Kiểm tra cấu hình, token và số bước dự kiến; chưa dùng GPU."],
    )
    return run_module("training.train_qlora", train_arguments(config, dry_run=True))


def train_arguments(config: RunConfig, *, dry_run: bool = False) -> list[str]:
    arguments = [
        "--train-dataset",
        str(config.train_dataset),
        "--eval-dataset",
        str(config.validation_dataset),
        "--init-adapter-path",
        str(config.init_adapter),
        "--output-dir",
        str(config.output_adapter),
        "--epochs",
        str(config.epochs),
        "--max-length",
        str(config.max_length),
        "--learning-rate",
        config.learning_rate,
        "--gradient-accumulation-steps",
        "16",
        "--lora-r",
        "8",
        "--lora-alpha",
        "16",
        "--save-steps",
        "20",
    ]
    if dry_run:
        arguments.append("--dry-run")
    return arguments


def train(config: RunConfig) -> bool:
    box(
        "HỘP THOẠI 3 — TRAIN GPU",
        [
            "Bước này tải Qwen3-4B 4-bit và cập nhật LoRA adapter.",
            f"Output: {config.output_adapter}",
            "Không đóng cửa sổ terminal trong lúc train.",
        ],
    )
    output = SERVICE_ROOT / config.output_adapter
    if output.exists():
        print("CẢNH BÁO: thư mục output đã tồn tại. Script không tự xóa thư mục này.")
        if not yes_no("Bạn vẫn muốn để train_qlora xử lý thư mục hiện tại?"):
            return False
    if input("Gõ TRAIN để bắt đầu dùng GPU: ").strip() != "TRAIN":
        print("Đã hủy bước train.")
        return False
    return run_module("training.train_qlora", train_arguments(config))


def generate_predictions(config: RunConfig) -> bool:
    box(
        "HỘP THOẠI 4 — SINH PREDICTION",
        ["Chạy adapter candidate trên held-out test; chưa chấm điểm."],
    )
    return run_module(
        "training.generate_predictions",
        [
            "--dataset",
            str(config.test_dataset),
            "--adapter-path",
            str(config.output_adapter),
            "--output",
            str(config.predictions),
            "--max-new-tokens",
            str(config.max_new_tokens),
            "--resume",
        ],
    )


def evaluate(config: RunConfig) -> bool:
    box(
        "HỘP THOẠI 5 — CHẤM GROUNDED CONVERSATION",
        ["Kiểm tra tỉnh, địa điểm catalog, realtime và claim không có nguồn."],
    )
    return run_module(
        "training.evaluate_grounded_conversation",
        [
            "--dataset",
            str(config.test_dataset),
            "--predictions",
            str(config.predictions),
            "--output",
            str(config.report),
        ],
    )


def regression() -> bool:
    box(
        "HỘP THOẠI 6 — REGRESSION",
        ["Chạy unit test và Ruff; không tự promote adapter."],
    )
    tests = subprocess.run(
        [sys.executable, "-m", "pytest"], cwd=SERVICE_ROOT, check=False
    )
    lint = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."], cwd=SERVICE_ROOT, check=False
    )
    success = tests.returncode == 0 and lint.returncode == 0
    print("\n✓ Regression đạt." if success else "\n✗ Regression chưa đạt.")
    return success


def demo_matrix() -> bool:
    box(
        "HỘP THOẠI 7 — DEMO API",
        ["AI service phải đang chạy tại cổng 8001 trước khi thực hiện."],
    )
    base_url = ask("Base URL", "http://127.0.0.1:8001/internal/v1")
    version = ask("Model version mong đợi", "v12")
    return run_module(
        "training.run_demo_matrix",
        ["--base-url", base_url, "--expected-version", version],
    )


def full_wizard(config: RunConfig) -> None:
    config = configure(config)
    if not validate_paths(config) or not dry_run(config):
        print("Dừng wizard vì dữ liệu hoặc dry-run chưa đạt.")
        return
    if not train(config):
        return
    if not generate_predictions(config) or not evaluate(config):
        print("Candidate chưa hoàn tất đánh giá; không nên promote.")
        return
    regression()
    box(
        "HOÀN TẤT WIZARD",
        [
            f"Adapter candidate: {config.output_adapter}",
            f"Báo cáo: {config.report}",
            "Hãy review prediction thủ công và chạy demo trước khi promote.",
        ],
    )


def main() -> None:
    config = RunConfig()
    actions = {
        "1": lambda: full_wizard(config),
        "2": lambda: validate_paths(configure(config)),
        "3": lambda: dry_run(configure(config)),
        "4": lambda: train(configure(config)),
        "5": lambda: generate_predictions(configure(config)),
        "6": lambda: evaluate(configure(config)),
        "7": regression,
        "8": demo_matrix,
    }
    while True:
        box(
            "TRAVELMATE — MANUAL TRAIN RUNNER",
            [
                "1. Chạy wizard đầy đủ",
                "2. Validate dữ liệu",
                "3. Dry-run cấu hình",
                "4. Train QLoRA bằng GPU",
                "5. Sinh prediction",
                "6. Chấm grounded conversation",
                "7. Chạy test + Ruff",
                "8. Chạy demo matrix API",
                "0. Thoát",
            ],
        )
        choice = input("Chọn bước: ").strip()
        if choice == "0":
            print("Đã thoát manual train runner.")
            return
        action = actions.get(choice)
        if action is None:
            print("Lựa chọn không hợp lệ.")
            continue
        try:
            action()
        except (KeyboardInterrupt, EOFError):
            print("\nĐã hủy thao tác hiện tại.")
        except ValueError as error:
            print(f"Giá trị nhập không hợp lệ: {error}")


if __name__ == "__main__":
    main()
