from typing import List, Dict, Any
import chromadb
from app.utils.config import VECTOR_DB_PATH
from .embedding_service import EmbeddingService


class VectorStore:
    def __init__(self):
        # 创建持久化客户端，向量索引会落到 ./data/chroma_db
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection = self.client.get_or_create_collection(
            name="resumes",
            metadata={"hnsw:space": "cosine"},  # 使用余弦相似度
        )
        self.embedding_service = EmbeddingService()

    def add_resume(self, resume_id: int, raw_content: str, metadata: Dict[str, Any]) -> str:
        """添加简历向量（以 resume_{id} 作为Chroma的文档ID）"""
        vector = self.embedding_service.encode_resume(raw_content, metadata)
        doc_id = f"resume_{resume_id}"
        self.collection.add(
            ids=[doc_id],
            embeddings=[vector],
            metadatas=[{
                "resume_id": resume_id,
                "name": metadata.get("name") or "",
                "skills": ",".join(metadata.get("skills") or []),
                "domain": metadata.get("domain") or "",
            }],
            documents=[raw_content[:500]],  # 预览字段，避免存太大
        )
        return doc_id

    def delete_resume(self, resume_id: int) -> None:
        """删除简历向量（通过规范化的ID）"""
        self.collection.delete(ids=[f"resume_{resume_id}"])

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """语义搜索，返回 resume_id 与相似度"""
        query_vector = self.embedding_service.encode_text(query)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["metadatas", "distances"],
        )
        if not results or not results.get("metadatas"):
            return []
        return [
            {
                "resume_id": meta.get("resume_id"),
                "name": meta.get("name"),
                "similarity": 1 - dist,
            }
            for meta, dist in zip(results["metadatas"][0], results["distances"][0])
        ]

# 创建全局单例，便于复用连接与缓存
vector_store = VectorStore()