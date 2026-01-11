from typing import List, Dict, Any, Optional
import re


class ContextBuilder:
    """
    Context construction for In-Context Learning.

    Responsibilities:
    - Select relevant retrieved chunks
    - Deduplicate and order evidence
    - Enforce token / length budget
    - Return structured context (not prompt strings)
    """

    def __init__(
        self,
        max_tokens: int = 2000,
        max_chunks: int = 10,
    ):
        self.max_tokens = max_tokens
        self.max_chunks = max_chunks

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        Rough token estimation.
        (Avoid tokenizer dependency at this stage.)
        """
        return max(1, len(text.split()))

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def build(
        self,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        sorted_chunks = sorted(
                    retrieved_chunks,
                    key=lambda x: x.get("score") if x.get("score") is not None else float("inf"),
                )

        items = []
        seen = set()
        token_count = 0

        for chunk in sorted_chunks:
            key = (chunk["paper_id"], chunk.get("chunk_index"))
            if key in seen:
                continue

            content = self._normalize_text(chunk.get("content", ""))

            if not content:
                continue

            tokens = self._estimate_tokens(content)

            if token_count + tokens > self.max_tokens:
                break

            items.append(
                {
                    "source_id": f"{chunk['paper_id']}#chunk-{chunk.get('chunk_index')}",
                    "paper_id": chunk["paper_id"],
                    "title": chunk.get("title"), 
                    "content": content,
                    "score": chunk.get("score"),
                }
            )

            seen.add(key)
            token_count += tokens

            if len(items) >= self.max_chunks:
                break

        return {
            "items": items,
            "stats": {
                "num_items": len(items),
                "unique_papers": len({i["paper_id"] for i in items}),
            },
            "token_usage": {
                "estimated_tokens": token_count,
                "max_tokens": self.max_tokens,
            },
        }

