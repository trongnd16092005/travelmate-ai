from pathlib import Path
from typing import Any

from app.clients.llm.base import ChatMessage, LocalModelUnavailableError
from app.core.config import Settings


class LocalTransformersChatModel:
    """Lazy-loading Transformers client for a Qwen-compatible local model."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model: Any = None
        self._tokenizer: Any = None

    def generate(self, messages: list[ChatMessage]) -> str:
        import torch

        self._ensure_loaded()
        prompt = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
        inputs = self._tokenizer(prompt, return_tensors="pt")
        inputs = {key: value.to(self._model.device) for key, value in inputs.items()}

        with torch.inference_mode():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=self.settings.local_model_max_new_tokens,
                do_sample=False,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        generated_ids = output_ids[0][inputs["input_ids"].shape[-1] :]
        return self._tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return

        try:
            import torch
            from peft import PeftModel
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError as exc:
            raise LocalModelUnavailableError(
                'Thiếu thư viện local LLM. Chạy: pip install -e ".[local-llm]"'
            ) from exc

        use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
        compute_dtype = torch.bfloat16 if use_bf16 else torch.float16
        model_options: dict[str, Any] = {
            "device_map": self.settings.local_model_device,
            "dtype": compute_dtype,
        }
        if self.settings.local_model_load_in_4bit:
            model_options["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_use_double_quant=True,
            )

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(self.settings.local_model_id)
            model = AutoModelForCausalLM.from_pretrained(
                self.settings.local_model_id,
                **model_options,
            )
            adapter_path = Path(self.settings.local_adapter_path)
            if adapter_path.exists():
                model = PeftModel.from_pretrained(model, adapter_path)
            self._model = model.eval()
        except Exception as exc:
            raise LocalModelUnavailableError(
                f"Không thể tải local model {self.settings.local_model_id}: {exc}"
            ) from exc
