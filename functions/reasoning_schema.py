# inference/reasoning_schema.py
from typing import TypedDict, Optional


class ReasoningOutput(TypedDict, total=False):
    decision: str
    """
    Allowed values:
    - "answer"
    - "search_metadata"
    - "search_chunks"
    - "refine_query"
    - "abstain"
    """

    answer: Optional[str]
    rationale: Optional[str]
