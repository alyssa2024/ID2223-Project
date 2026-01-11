# inference/agent_state.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set


@dataclass
class AgentState:
    # --- Query & Task ---
    original_query: str
    canonical_query: str
    task_type: Optional[str] = None
    current_goal: Optional[str] = None

    # --- Retrieval / Perception ---
    retrieval_results: List[Dict[str, Any]] = field(default_factory=list)
    candidate_papers: Set[str] = field(default_factory=set)

    # last_retrieval_type: Optional[str] = None

    # --- Context ---
    context_bundle: Optional[Dict[str, Any]] = None

    # --- Reasoning ---
    last_llm_output: Optional[Dict[str, Any]] = None

    # --- Loop control ---
    iteration: int = 0
    max_iterations: int = 5
    terminated: bool = False
    termination_reason: Optional[str] = None

    def should_terminate(self) -> bool:
        return self.terminated or self.iteration >= self.max_iterations
