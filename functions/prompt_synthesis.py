from typing import Dict, Any, List


class PromptSynthesizer:
    """
    Prompt synthesizer for agentic inference (base model friendly).
    """

    def __init__(
        self,
        max_context_chars: int = 8000,
    ):
        self.max_context_chars = max_context_chars

    # ------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------

    def synthesize(
        self,
        question: str,
        context_bundle: Dict[str, Any],
        current_goal: str,
    ) -> str:
        system_rules = self._system_rules()
        schema = self._output_schema()
        examples = self._icl_examples()
        context = self._format_context(context_bundle)

        prompt = f"""
{system_rules}

{schema}

{examples}

### CONTEXT
{context}

### QUESTION
{question}

### GOAL
{current_goal}

### RESPONSE
"""

        return prompt.strip()

    # ------------------------------------------------------------
    # Prompt components
    # ------------------------------------------------------------

    def _system_rules(self) -> str:
        return """
You are an autonomous reasoning agent.
You must decide the next action based ONLY on the given context.
You are NOT a conversational chatbot.

Rules:
- Do NOT use external knowledge.
- Do NOT hallucinate facts.
- If evidence is insufficient, choose abstain.
- Follow the output format EXACTLY.
""".strip()

    def _output_schema(self) -> str:
        return """
You MUST output a valid JSON object with the following schema:

{
  "decision": "<one of: answer | search_metadata | search_chunks | abstain>",
  "answer": "<string or null>",
  "rationale": "<brief explanation>"
}

Rules:
- decision is REQUIRED.
- If decision is "answer", answer MUST be a non-empty string.
- If decision is NOT "answer", answer MUST be null.
- Output JSON ONLY. No extra text.
""".strip()

    def _icl_examples(self) -> str:
        """
        In-context learning examples to stabilize base model behavior.
        """
        return """
### EXAMPLES

Context:
Paper A: "This paper introduces method X for risk analysis."

Question:
"What is method X used for?"

Response:
{
  "decision": "answer",
  "answer": "Method X is used for risk analysis.",
  "rationale": "The context explicitly describes the purpose of method X."
}

---

Context:
(No relevant information found.)

Question:
"How does method Y improve performance?"

Response:
{
  "decision": "abstain",
  "answer": null,
  "rationale": "The context does not mention method Y."
}

---

Context:
Paper A: "This paper discusses general security principles."

Question:
"Give implementation details of protocol Z."

Response:
{
  "decision": "search_chunks",
  "answer": null,
  "rationale": "More detailed evidence may be found in full text."
}
""".strip()

    def _format_context(self, context_bundle: Dict[str, Any]) -> str:
        """
        Convert retrieved context into a compact textual form.
        """
        if not context_bundle or not context_bundle.get("chunks"):
            return "(No relevant context found.)"

        texts: List[str] = []
        for item in context_bundle["chunks"]:
            source = item.get("source", "unknown")
            content = item.get("content", "")
            texts.append(f"[Source: {source}]\n{content}")

        context_text = "\n\n".join(texts)
        return context_text[: self.max_context_chars]
