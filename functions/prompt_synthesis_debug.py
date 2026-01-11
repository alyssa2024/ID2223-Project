from typing import Dict, List

class DebugPromptSynthesizer:
    """
    Debug-oriented PromptSynthesizer (Strict Evidence Mode).
    
    Adjustments:
    - Maps internal Paper IDs to user-friendly citation numbers (e.g.,).
    - Enforces strict citation formatting in LLM output.
    """

    def synthesize(
        self,
        question: str,
        context_bundle: Dict,
        current_goal: str,
    ) -> str:
        
        items: List[Dict] = context_bundle.get("items", [])

        unique_paper_ids = []
        paper_id_to_index = {}
        
        for item in items:
            pid = item.get("paper_id")
            if pid not in paper_id_to_index:
                unique_paper_ids.append(pid)
                paper_id_to_index[pid] = len(unique_paper_ids)

        evidence_blocks = []
        for i, item in enumerate(items):
            pid = item.get("paper_id")
            cite_index = paper_id_to_index.get(pid)
            
            evidence_blocks.append(
                f"""
[EVIDENCE {i}]
Reference: [{cite_index}]
Title: {item.get("title", "Unknown Title")}
Content:
{item.get("content")}
""".strip()
            )

        evidence_text = (
            "\n\n".join(evidence_blocks)
            if evidence_blocks
            else "NO EVIDENCE RETRIEVED"
        )

        legend_blocks = []
        for pid in unique_paper_ids:
            idx = paper_id_to_index[pid]
            title = "Unknown Title"
            for it in items:
                if it["paper_id"] == pid:
                    title = it.get("title", "Unknown Title")
                    break
            legend_blocks.append(f" -> {title} (ID: {pid})")
            
        sources_legend = "\n".join(legend_blocks)

        prompt = f"""
You are a research agent operating in **STRICT EVIDENCE MODE**.

Your goal:
{current_goal}

User question:
{question}

========================
RETRIEVED EVIDENCE
========================
{evidence_text}

========================
SOURCE LEGEND (Context only)
========================
{sources_legend}

========================
REASONING INSTRUCTIONS
========================

You MUST follow the steps below IN ORDER.

Step 0: Intent Verification
- Does the evidence address the core question?
- If user asks for "Challenges", but evidence only shows "Results", NOTE this discrepancy.

Step 1: Evidence Synthesis
- Extract facts *solely* from the provided [EVIDENCE] blocks.
- **CITATION RULE (CRITICAL):** - Every time you state a fact from an evidence block, you MUST copy the `Reference` tag from that block exactly (e.g., ``).
  - Put the citation at the END of the sentence.
  - Example: "WaveNet is used for PCG synthesis."
  - Use ONLY the provided numeric citation format like [1], [2].
  - Do NOT invent new citation numbers.
  - Do NOT use Source ID, Paper ID, or author-year formats.


Step 2: Decision
- Decision: "answer"
    - If you have relevant information.
    - If the user input is Chitchat/Greeting (e.g., "hi"), answer politely without citations.
- Decision: "abstain"
    - ONLY if the evidence is completely unrelated.

========================
OUTPUT FORMAT (STRICT)
========================

Return VALID JSON ONLY.

{{
  "decision": "answer",
  "reasoning": {{
    "core_intent_check": "Yes/Partial/No",
    "key_findings": [ "Finding 1" ],
    "discrepancies": "Any missing info.",
    "rationale": "Why I am answering."
  }},
  "answer": "<The comprehensive answer in Markdown. **Every sentence must have a citation** if based on evidence.>"
}}

DO NOT include any text outside the JSON.
""".strip()

        return prompt