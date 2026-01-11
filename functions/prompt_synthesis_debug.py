from typing import Dict, List

class DebugPromptSynthesizer:
    """
    Debug-oriented PromptSynthesizer (Relaxed Version).
    
    Adjustments:
    - Retains the structured reasoning steps (Steps 0-3).
    - Removes the "Trap of Perfectionism" (allows partial answers).
    - Works with your existing ContextBuilder (no metadata required).
    """

    def synthesize(
        self,
        question: str,
        context_bundle: Dict,
        current_goal: str,
    ) -> str:
        
        items: List[Dict] = context_bundle.get("items", [])

        # ---- Format retrieved evidence ----
        # (保持原样，适应现有的 ContextBuilder)
        evidence_blocks = []
        for i, item in enumerate(items):
            evidence_blocks.append(
                f"""
[EVIDENCE {i}]
source_id: {item.get("source_id")}
paper_id: {item.get("paper_id")}
score: {item.get("score")}

content:
{item.get("content")}
""".strip()
            )

        evidence_text = (
            "\n\n".join(evidence_blocks)
            if evidence_blocks
            else "NO EVIDENCE RETRIEVED"
        )

        # ---- Debug reasoning prompt (RELAXED & PRO-ACTIVE) ----
        prompt = f"""
You are a research agent operating in **DEBUG MODE**.

Your goal:
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

You MUST follow the steps below IN ORDER.

Step 0: Intent & Scope Analysis
- Identify the CORE intent of the question.
- Acknowledge that retrieved evidence is often fragmented (chunks).
- **Goal:** Your job is to *synthesize* a helpful answer from these fragments, NOT to reject them because they aren't perfect.

Step 1: Evidence Applicability Check
- Do NOT list "Required Information" (this leads to over-conservatism).
- Instead, list **"Available Connections"**:
  - Does the evidence mention the Core Concept?
  - If the User asks for specific domain (e.g., ECG) but evidence is general (e.g., GANs), mark this as a **Valid Theoretical Connection**.
  - **Rule:** General principles applied to specific domains are valid answers if labeled as "inference".

Step 2: Gap Handling (The "Best Effort" Rule)
- If specific details (e.g., a specific number or date) are missing, do NOT abstain.
- Instead, plan to state: "The text describes [General Concept], which suggests..." or "While specific ECG data is not shown, the method works by..."

Step 3: Decision
- **DEFAULT to "answer".**
- Choose "abstain" ONLY if the evidence is **completely irrelevant** (e.g., Question about Biology, Evidence about History).
- Uncertainty is NOT grounds for abstaining. State the uncertainty in the answer.

========================
OUTPUT FORMAT (STRICT)
========================

Return VALID JSON ONLY.

{{
  "decision": "answer" (or "abstain" only if impossible),
  "reasoning": {{
    "core_intent": "...",
    "available_connections": [ "Evidence X supports concept Y..." ],
    "inferences_made": [ "Applying general GAN theory to ECG domain..." ],
    "rationale": "Why I decided to answer despite gaps."
  }},
  "answer": "<The comprehensive answer. Use Markdown. If relying on inference, state 'Based on the general principles in the text...'>"
}}

DO NOT include any text outside the JSON.
""".strip()

        return prompt