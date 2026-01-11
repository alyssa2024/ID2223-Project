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
    You are an autonomous research reasoning agent.
    You must decide the next action based ONLY on the given context.
    You are NOT a conversational chatbot.

    Rules:
    - Do NOT use external knowledge.
    - Do NOT hallucinate facts.
    - You MAY synthesize, summarize, and generalize across multiple sources.
    - If ANY relevant information is present in the context, you MUST attempt to answer.
    - Do NOT abstain due to uncertainty alone.
    - Use abstain ONLY if the context is empty or completely irrelevant.
    - Follow the output format EXACTLY.
    - Metadata (title/abstract) is NOT sufficient evidence.
    - If only metadata-level information is present, you MUST request search_chunks before answering.
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
- Preferred decision priority (highest to lowest):
  1. answer
  2. search_chunks
  3. search_metadata
  4. abstain
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

---

Context:
Paper A: "This paper discusses general risk reporting principles such as transparency and consistency."

Question:
"What are best practices for risk reporting?"

Response:
{
  "decision": "answer",
  "answer": "Based on the literature, best practices for risk reporting include transparency, consistency, and clear communication of uncertainties.",
  "rationale": "The context provides general principles that can be synthesized into best practices."
}
""".strip()

    def _format_context(self, context_bundle: Dict[str, Any]) -> str:
        if not context_bundle or not context_bundle.get("items"):
            return "(No relevant context found.)"

        texts = []
        for item in context_bundle["items"]:
            texts.append(
                f"[Source: {item['source_id']}]\n{item['content']}"
            )

        context_text = "\n\n".join(texts)
        return context_text[: self.max_context_chars]

