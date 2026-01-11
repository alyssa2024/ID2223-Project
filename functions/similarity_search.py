from typing import List, Optional, Dict, Any
from networkx import neighbors
import numpy as np
from sklearn import neighbors


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

    def _row_to_dict(self, row, feature_names):
        """
        Convert a hsfs neighbor row into a dict using feature names.
        """
        # Case 1: already dict
        if isinstance(row, dict):
            return row

        # Case 2: tuple or list → map by schema order
        if isinstance(row, (list, tuple)):
            return dict(zip(feature_names, row))

        raise TypeError(f"Unsupported row type: {type(row)}")

    def _normalize_neighbors(self, neighbors, feature_view):
            """
            Normalize hsfs find_neighbors output into list[dict]
            using feature view schema.
            """
            if neighbors is None:
                return []

            feature_names = [f.name for f in feature_view.schema]
            rows = []

            # DataFrame
            if hasattr(neighbors, "iterrows"):
                for _, row in neighbors.iterrows():
                    rows.append(row.to_dict())
                return rows

            # list-based outputs
            if isinstance(neighbors, list):
                if len(neighbors) == 0:
                    return []

                should_flatten = False
                first_neighbor = neighbors[0]
                
                if isinstance(first_neighbor, list) and len(first_neighbor) > 0:
                    if isinstance(first_neighbor[0], (list, dict, tuple)):
                        should_flatten = True

                if should_flatten:
                    for sub in neighbors:
                        for row in sub:
                            rows.append(self._row_to_dict(row, feature_names))
                    return rows

                for row in neighbors:
                    rows.append(self._row_to_dict(row, feature_names))
                return rows

            raise TypeError(f"Unsupported neighbors type: {type(neighbors)}")

    def _embed_query(self, query: str) -> np.ndarray:
        embedding = self.embedding_model.encode(query)
        return embedding

    def search_metadata(self, query: str, k: int = 5):
        query_embedding = self._embed_query(query)

        neighbors = self.metadata_fv.find_neighbors(
            query_embedding,
            k=k,
        )

        rows = self._normalize_neighbors(neighbors, self.metadata_fv)

        results = []
        for rank, row in enumerate(rows):
            results.append(
                {
                    "paper_id": row.get("paper_id"),
                    "title": row.get("title"),
                    "abstract": row.get("abstract"),
                    # "score": row.get("distance", row.get("score")),
                    "score": 1.0 / (rank + 1),
                }
            )

        return results


    def search_chunks(self, query: str, k: int = 20, paper_ids=None):
        query_embedding = self._embed_query(query)

        filter_query = None
        if paper_ids:
            filter_query = {
                "bool": {
                    "must": [
                        {"terms": {"paper_id": paper_ids}}
                    ]
                }
            }

        if filter_query is not None:
            neighbors = self.chunk_fv.find_neighbors(
                query_embedding,
                k=k,
                filter=filter_query,
            )
        else:
            neighbors = self.chunk_fv.find_neighbors(
                query_embedding,
                k=k,
            )

        rows = self._normalize_neighbors(neighbors, self.chunk_fv)

        results = []
        for rank, row in enumerate(rows):
            results.append(
                {
                    "paper_id": row.get("paper_id"),
                    "chunk_index": row.get("chunk_index"),
                    "content": row.get("content"),
                    # "score": row.get("distance", row.get("score")),
                    "score": 1.0 / (rank + 1),
                }
            )

        return results
