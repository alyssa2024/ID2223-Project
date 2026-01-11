from typing import TypedDict, Optional, Literal


Decision = Literal[
    "answer",
    "search_metadata",
    "search_chunks",
    "abstain",
]


class ReasoningOutput(TypedDict):
    decision: Decision
    answer: Optional[str]
    rationale: str

