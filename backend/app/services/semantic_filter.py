"""第一阶段：语义检索（基于向量相似度）"""

from typing import List, Dict, Any
from app.services.vector_store import vector_store


class SemanticFilter:
    def search(self, query_text: str, top_k: int = 50) -> List[Dict[str, Any]]:
        return vector_store.search(query_text, top_k)


semantic_filter = SemanticFilter()


