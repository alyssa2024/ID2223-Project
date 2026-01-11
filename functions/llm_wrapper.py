# functions/llm_wrapper.py

import os
from typing import Optional
from openai import OpenAI


class LLMWrapper:
    """
    Agent-ready LLM wrapper (OpenAI-compatible API).

    Works with:
    - SiliconFlow
    - OpenAI
    - Any OpenAI-compatible service

    Contract:
    - Input: prompt (str)
    - Output: raw generated text (str)
    """

    def __init__(
        self,
        model: str = "Qwen/Qwen3-8B",
        base_url: Optional[str] = None,
        api_key : Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.api_key = api_key 
        if not self.api_key:
            raise ValueError("API key is required.")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=base_url,
        )

    def __call__(self, prompt: str) -> str:
        if not isinstance(prompt, str):
            raise ValueError("Prompt must be a string.")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        try:
            return response.choices[0].message.content.strip()
        except Exception:
            raise RuntimeError(f"Invalid LLM response: {response}")
