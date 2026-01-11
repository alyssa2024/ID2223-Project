# functions/prompt_synthesis_debug.py

from typing import Dict, List


class DebugPromptSynthesizer:
    """
    Drop-in replacement for PromptSynthesizer.
    Agent-loop does NOT need to change.
    """

    def synthesize(
        self,
        question: str,
        context_bundle: Dict,
        current_goal: str,
    ) -> str:
        """
        Build an extremely verbose debug prompt that exposes:
        - reasoning
        - evidence usage
        - decision justification
        """

        chunks: List[Dict] = context_bundle.get("chunks", [])
        metadata: List[Dict] = context_bundle.get("metadata", [])

        # ---- Format retrieved evidence clearly ----
        evidence_blocks = []

        for i, c in enumerate(chunks):
            evidence_blocks.append(
                f"""
[EVIDENCE CHUNK {i}]
paper_id: {c.get("paper_id")}
score: {c.get("score")}
content:
{c.get("text")}
""".strip()
            )

        for i, m in enumerate(metadata):
            evidence_blocks.append(
                f"""
[METADATA {i}]
paper_id: {m.get("paper_id")}
title: {m.get("title")}
abstract:
{m.get("abstract")}
""".strip()
            )

        evidence_text = "\n\n".join(evidence_blocks) if evidence_blocks else "NO EVIDENCE RETRIEVED"

        # ---- Debug reasoning prompt ----
        prompt = f"""
You are a research agent operating in DEBUG MODE.

Your task:
{current_goal}

User question:
{question}

========================
RETRIEVED EVIDENCE
========================
{evidence_text}

========================
REASONING INSTRUCTIONS
========================

You MUST follow these steps explicitly:

1. List what information is REQUIRED to answer the question.
2. For each required item, check whether it is present in the retrieved evidence.
3. Cite the specific paper_id(s) used for each fact.
4. Decide ONE of the following actions:
   - "answer"
   - "search_metadata"
   - "search_chunks"
   - "abstain"

IMPORTANT CONSTRAINTS:
- You may ONLY choose "abstain" if you clearly explain what information is missing.
- If ANY partial answer is possible from the evidence, prefer "answer".
- Do NOT hallucinate facts not present in evidence.

========================
OUTPUT FORMAT (STRICT)
========================

Return VALID JSON ONLY.

{{
  "decision": "<one of: answer | search_metadata | search_chunks | abstain>",
  "reasoning": {{
    "required_information": [ ... ],
    "evidence_analysis": [ ... ],
    "missing_information": [ ... ],
    "decision_rationale": "..."
  }},
  "answer": "<only if decision == answer, otherwise null>"
}}

DO NOT include any text outside the JSON.
""".strip()

        return prompt
