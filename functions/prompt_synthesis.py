from typing import Dict, Any, List


class PromptSynthesizer:
    """
    Prompt synthesizer for agentic inference (base model friendly).

    Design goals:
    - Enforce paper-level numeric citations ([1], [2], ...)
    - Prevent Source ID / Paper ID leakage into model output
    - Stable behavior for base LLMs (non-chat, non-tool models)
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
""".strip()

        return prompt

    # ------------------------------------------------------------
    # Prompt components
    # ------------------------------------------------------------

    def _system_rules(self) -> str:
        return """
You are an autonomous research reasoning agent.
You must decide the next action based ONLY on the given context.
You are NOT a conversational chatbot.

General Rules:
- Do NOT use external knowledge.
- Do NOT hallucinate facts.
- You MAY synthesize, summarize, and generalize across multiple sources.
- If ANY relevant information is present in the context, you MUST attempt to answer.
- Do NOT abstain due to uncertainty alone.
- Use abstain ONLY if the context is empty or completely irrelevant.
- Metadata (title/abstract) alone is NOT sufficient evidence.
- If only metadata-level information is present, you MUST request search_chunks before answering.
- Follow the output format EXACTLY.
- Output JSON ONLY. No extra text.

Citation Rules (CRITICAL):
- Every factual statement derived from the context MUST include a citation.
- Citations MUST use the numeric format exactly as provided in the context (e.g., [1], [2]).
- Do NOT invent new citation numbers.
- Do NOT use Source ID, Paper ID, author names, or year-based citations.
- Do NOT cite information not present in the context.
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
- If decision is "answer", the answer MUST use numeric citations like [1], [2] for all factual claims.
- Output JSON ONLY. No extra text.
""".strip()

    def _icl_examples(self) -> str:
        """
        In-context learning examples to stabilize base model behavior.
        Domain: PCG (phonocardiogram) signal synthesis and analysis.
        """
        return """
### EXAMPLES

Context:
[EVIDENCE]
Reference: [1]
Title: Neural Modeling of Phonocardiogram Signals
Content:
This paper proposes a neural network-based method to synthesize realistic PCG signals by modeling heart sound components such as S1 and S2 using a waveform-level generator.

Question:
"What is the purpose of the proposed PCG synthesis method?"

Response:
{
  "decision": "answer",
  "answer": "The proposed method is designed to synthesize realistic phonocardiogram signals by modeling key heart sound components such as S1 and S2 using a neural waveform generator [1].",
  "rationale": "The context explicitly describes the goal and methodology of the PCG synthesis approach."
}

---

Context:
(No relevant context found.)

Question:
"How does diffusion modeling improve PCG signal generation?"

Response:
{
  "decision": "abstain",
  "answer": null,
  "rationale": "The context does not contain any information related to diffusion-based PCG signal generation."
}

---

Context:
Paper A (metadata only):
Title: A Review of Heart Sound Analysis Techniques
Abstract:
This paper surveys general methods for heart sound analysis.

Question:
"What neural architectures are used for PCG waveform synthesis?"

Response:
{
  "decision": "search_chunks",
  "answer": null,
  "rationale": "The available context only contains high-level metadata and lacks chunk-level evidence on specific synthesis architectures."
}

---

Context:
[EVIDENCE]
Reference: [1]
Title: Data-Driven PCG Signal Modeling
Content:
The study highlights that high-quality PCG datasets with accurate segmentation of cardiac cycles are essential for training reliable synthesis models.

[EVIDENCE]
Reference: [2]
Title: Neural Synthesis of Biomedical Signals
Content:
The paper emphasizes that incorporating temporal structure improves the perceptual quality of synthesized biomedical waveforms.

Question:
"What factors are important for training effective PCG signal synthesis models?"

Response:
{
  "decision": "answer",
  "answer": "Effective PCG signal synthesis models rely on high-quality datasets with accurate cardiac cycle segmentation [1], as well as modeling strategies that incorporate temporal structure to improve perceptual quality [2].",
  "rationale": "Both sources provide complementary evidence about data requirements and modeling considerations for PCG synthesis."
}
""".strip()

    def _format_context(self, context_bundle: Dict[str, Any]) -> str:
        if not context_bundle or not context_bundle.get("items"):
            return "(No relevant context found.)"

        texts: List[str] = []

        # Map paper_id to a stable numeric citation order
        paper_id_to_order: Dict[str, int] = {}
        current_order = 1

        for item in context_bundle["items"]:
            pid = item.get("paper_id")
            if pid not in paper_id_to_order:
                paper_id_to_order[pid] = current_order
                current_order += 1

            order = paper_id_to_order[pid]
            title = item.get("title", "Unknown Title")
            content = item.get("content", "")

            texts.append(
                f"""[EVIDENCE]
Reference: [{order}]
Title: {title}
Content:
{content}
""".strip()
            )

        context_text = "\n\n".join(texts)
        return context_text[: self.max_context_chars]
