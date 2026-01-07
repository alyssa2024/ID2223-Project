# functions/llm_wrapper.py

import os
import getpass
import torch
import transformers
from transformers import AutoTokenizer, AutoModelForCausalLM


class LLMWrapper:
    """
    Agent-ready LLM wrapper (BASE MODEL version).

    - Uses a pure base causal language model
    - No PEFT / LoRA / adapters
    - Fully controlled by agentic loop + prompt
    """

    def __init__(
        self,
        model_name_or_path: str,
        temperature: float = 0.2,
        repetition_penalty: float = 1.5,
        max_new_tokens: int = 750,
    ):
        self.model_name_or_path = model_name_or_path
        self.temperature = temperature
        self.repetition_penalty = repetition_penalty
        self.max_new_tokens = max_new_tokens

        self.tokenizer, self.model = self._load_model()
        self.pipeline = self._build_pipeline()

    # ------------------------------------------------------------------
    # Model loading (BASE MODEL)
    # ------------------------------------------------------------------

    def _load_model(self):
        """
        Load base causal LM and tokenizer from HuggingFace.
        """
        os.environ["HF_API_KEY"] = (
            os.getenv("HF_API_KEY")
            or getpass.getpass("🔑 Enter your HuggingFace API key: ")
        )

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_name_or_path,
            token=os.environ["HF_API_KEY"],
        )

        model = AutoModelForCausalLM.from_pretrained(
            self.model_name_or_path,
            device_map="auto",
            torch_dtype=torch.float16,
            token=os.environ["HF_API_KEY"],
        )

        # Ensure padding works correctly
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = "right"

        print(f"⛳️ Base LLM loaded on device: {model.device}")
        return tokenizer, model

    # ------------------------------------------------------------------
    # Raw text-generation pipeline
    # ------------------------------------------------------------------

    def _build_pipeline(self):
        """
        Build a raw HuggingFace text-generation pipeline.
        """
        return transformers.pipeline(
            model=self.model,
            tokenizer=self.tokenizer,
            task="text-generation",
            temperature=self.temperature,
            repetition_penalty=self.repetition_penalty,
            max_new_tokens=self.max_new_tokens,
            do_sample=True,
            return_full_text=True,
            pad_token_id=self.tokenizer.eos_token_id,
        )

    # ------------------------------------------------------------------
    # Callable interface for Agent
    # ------------------------------------------------------------------

    def __call__(self, prompt: str) -> str:
        """
        Execute one reasoning step.

        Parameters
        ----------
        prompt : str
            Fully synthesized prompt from PromptSynthesizer

        Returns
        -------
        str
            Raw generated text
        """
        if not isinstance(prompt, str):
            raise ValueError("Prompt must be a string.")

        outputs = self.pipeline(prompt)

        if not outputs or "generated_text" not in outputs[0]:
            raise RuntimeError("Invalid LLM output format.")

        return outputs[0]["generated_text"].strip()
