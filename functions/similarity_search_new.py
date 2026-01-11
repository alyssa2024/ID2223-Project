from typing import List, Optional, Dict, Any
import numpy as np
from sentence_transformers import CrossEncoder 


class SimilaritySearchEngine:
    """
    Perception layer for RAG / Agent systems with Reranking capabilities.

    Responsibilities:
    - Embed query
    - Perform initial vector similarity search (Recall)
    - Perform Cross-Encoder reranking (Precision)
    - Return structured retrieval results
    """

    def __init__(
        self,
        embedding_model,
        metadata_feature_view,
        chunk_feature_view,
        embedding_col_name: str = "embedding",
        reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        self.embedding_model = embedding_model
        self.metadata_fv = metadata_feature_view
        self.chunk_fv = chunk_feature_view
        self.embedding_col_name = embedding_col_name
        
        # --- 初始化 Reranker ---
        print(f"Loading Reranker model: {reranker_model_name}...")
        self.reranker = CrossEncoder(reranker_model_name)
        
        self.paper_id_to_title = {}
        try:
            print("Caching paper titles from Metadata Feature View...")
            
            # vvvvvvvvvvvvvvv [修改点] vvvvvvvvvvvvvvv
            # 使用 .query.read() 绕过 Training Dataset 检查，直接读源数据
            rows = self.metadata_fv.query.read()
            # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            
            # 兼容 DataFrame 遍历
            if hasattr(rows, "iterrows"):
                for _, row in rows.iterrows():
                    self._cache_title(row)
            else:
                for row in rows:
                    self._cache_title(row)
            print(f"Successfully cached {len(self.paper_id_to_title)} titles.")
            
        except Exception as e:
            print(f"Warning: Failed to cache paper titles: {e}")
            # 保持为空，防止程序崩溃
            self.paper_id_to_title = {}

    def _cache_title(self, row):
        # 辅助方法：从行数据中提取 title 并缓存
        if isinstance(row, dict):
            pid = row.get("paper_id")
            title = row.get("title")
        else: # pandas Series
            pid = row.get("paper_id")
            title = row.get("title")
        
        if pid and title:
            self.paper_id_to_title[pid] = title

    def _row_to_dict(self, row, feature_names):
        if isinstance(row, dict):
            return row
        if isinstance(row, (list, tuple)):
            return dict(zip(feature_names, row))
        raise TypeError(f"Unsupported row type: {type(row)}")

    def _normalize_neighbors(self, neighbors, feature_view):
        """
        Normalize hsfs find_neighbors output into list[dict].
        Contains fix for list[list] vs list[Row] confusion.
        """
        if neighbors is None:
            return []
        
        if isinstance(neighbors, list) and len(neighbors) == 0:
            return []

        feature_names = [f.name for f in feature_view.schema]
        rows = []

        # DataFrame format
        if hasattr(neighbors, "iterrows"):
            for _, row in neighbors.iterrows():
                rows.append(row.to_dict())
            return rows

        # List format handling
        if isinstance(neighbors, list):
            # Check for nested batch results
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
            
            # Single query results
            for row in neighbors:
                rows.append(self._row_to_dict(row, feature_names))
            return rows

        raise TypeError(f"Unsupported neighbors type: {type(neighbors)}")

    def _embed_query(self, query: str) -> np.ndarray:
        return self.embedding_model.encode(query)

    def _compute_distance_fallback(self, query_emb: np.ndarray, row: Dict[str, Any]) -> float:
        """
        Fallback: Calculate Cosine Distance manually if Hopsworks returns None.
        Used primarily for metadata search where reranking might be overkill.
        """
        target_emb_list = row.get(self.embedding_col_name)
        if target_emb_list is None:
            # Try to find list-like values in dict
            for val in row.values():
                if isinstance(val, (list, np.ndarray)) and len(val) > 10:
                    target_emb_list = val
                    break
        
        if target_emb_list is None:
            return float("inf")

        try:
            target_emb = np.array(target_emb_list)
            norm_q = np.linalg.norm(query_emb)
            norm_t = np.linalg.norm(target_emb)
            if norm_q == 0 or norm_t == 0:
                return float("inf")
            
            # Cosine Distance = 1 - Cosine Similarity
            return 1.0 - np.dot(query_emb, target_emb) / (norm_q * norm_t)
        except:
            return float("inf")

    def search_metadata(self, query: str, k: int = 5):
        """
        Searches paper metadata. 
        Uses standard vector search (lightweight).
        """
        query_embedding = self._embed_query(query)

        neighbors = self.metadata_fv.find_neighbors(
            query_embedding,
            k=k,
        )
        
        rows = self._normalize_neighbors(neighbors, self.metadata_fv)
        results = []

        for row in rows:
            # Use DB distance or compute manually
            score = row.get("distance", row.get("score"))
            if score is None:
                score = self._compute_distance_fallback(query_embedding, row)

            results.append({
                "paper_id": row.get("paper_id"),
                "title": row.get("title"),
                "abstract": row.get("abstract"),
                "score": score,
            })
            
        return results

    def search_chunks(self, query: str, k: int = 20, paper_ids=None):
        """
        Searches full text chunks with Reranking.
        1. Recall: Retrieve k*5 candidates via Vector Search.
        2. Rerank: Re-score using Cross-Encoder.
        """
        # 1. Expand retrieval window for Reranking (Recall Phase)
        initial_k = k * 5
        query_embedding = self._embed_query(query)

        # Note: 'filter' parameter usage depends on HSFS version/backend. 
        # If supported, use it. If not, we filter in python (less efficient but safe).
        neighbors = self.chunk_fv.find_neighbors(
            query_embedding,
            k=initial_k,
        )

        rows = self._normalize_neighbors(neighbors, self.chunk_fv)
        
        # 2. Filter & Prepare candidates
        candidates = []
        
        for row in rows:
            # Paper ID Filter
            if paper_ids and row.get("paper_id") not in paper_ids:
                continue

            content = row.get("content")
            if not content or not str(content).strip():
                continue
            
            # Prepare obj for results
            candidate = {
                "paper_id": row.get("paper_id"),
                "title": self.paper_id_to_title.get(row.get("paper_id"), "Unknown"),
                "chunk_index": row.get("chunk_index"),
                "content": content,
                # Temporary store original vector score if needed
                "_vector_score": row.get("distance", row.get("score")), 
            }
            candidates.append(candidate)

        if not candidates:
            return []

        # 3. Reranking Phase (Precision Phase)
        # Construct pairs: [[query, doc1], [query, doc2], ...]
        rerank_pairs = [[query, c["content"]] for c in candidates]
        
        # Predict scores (scores are "relevance", higher is better, can be negative or positive)
        # e.g., 7.5, -2.1, 0.5
        rerank_scores = self.reranker.predict(rerank_pairs)

        # 4. Assign new scores and Sort
        for i, candidate in enumerate(candidates):
            relevance_score = float(rerank_scores[i])
            
            # CRITICAL ADAPTATION FOR CONTEXT BUILDER:
            # Your ContextBuilder sorts by 'score' in ASCENDING order (low is better).
            # CrossEncoder outputs RELEVANCE (high is better).
            # Solution: We negate the relevance score. 
            # High relevance (8.0) becomes (-8.0), which sorts before low relevance (1.0 -> -1.0).
            candidate["score"] = -relevance_score
            
            # Optional: Keep the raw relevance for debugging
            # candidate["relevance"] = relevance_score

        # Sort by the new negated score (effectively descending relevance)
        candidates.sort(key=lambda x: x["score"])

        # 5. Slice top k
        return candidates[:k]