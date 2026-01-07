from typing import List, Optional, Dict, Any
import numpy as np


class SimilaritySearchEngine:
    """
    Perception layer for RAG / Agent systems.

    Responsibilities:
    - Embed query
    - Perform similarity search on Feature Views
    - Return structured retrieval results

    No LLM, no prompt, no agent logic.
    """

    def __init__(
        self,
        embedding_model,
        metadata_feature_view,
        chunk_feature_view,
    ):
        """
        Parameters
        ----------
        embedding_model:
            Any model with .encode(List[str]) -> np.ndarray
            (e.g., SentenceTransformer)

        metadata_feature_view:
            Hopsworks Feature View for paper-level metadata

        chunk_feature_view:
            Hopsworks Feature View for chunk-level full text
        """
        self.embedding_model = embedding_model
        self.metadata_fv = metadata_feature_view
        self.chunk_fv = chunk_feature_view

    def _embed_query(self, query: str) -> np.ndarray:
        return self.embedding_model.encode([query])

    def search_metadata(
        self,
        query: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Paper-level similarity search.
        """
        query_embedding = self._embed_query(query)

        neighbors = self.metadata_fv.find_neighbors(
            query_vector=query_embedding,
            k=k,
        )

        results: List[Dict[str, Any]] = []

        for _, row in neighbors.iterrows():
            results.append(
                {
                    "paper_id": row["paper_id"],
                    "title": row.get("title"),
                    "abstract": row.get("abstract"),
                    "score": row.get("distance", row.get("score")),
                }
            )

        return results

    def search_chunks(
        self,
        query: str,
        k: int = 20,
        paper_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Chunk-level similarity search.
        Optionally filtered by paper_ids.
        """
        query_embedding = self._embed_query(query)

        filter_condition = None
        if paper_ids:
            quoted_ids = ",".join(f"'{pid}'" for pid in paper_ids)
            filter_condition = f"paper_id in ({quoted_ids})"

        neighbors = self.chunk_fv.find_neighbors(
            query_vector=query_embedding,
            k=k,
            filter=filter_condition,
        )

        results: List[Dict[str, Any]] = []

        for _, row in neighbors.iterrows():
            results.append(
                {
                    "paper_id": row["paper_id"],
                    "chunk_index": row["chunk_index"],
                    "content": row["content"],
                    "score": row.get("distance", row.get("score")),
                }
            )

        return results
