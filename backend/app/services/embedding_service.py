from typing import List
import os
from sentence_transformers import SentenceTransformer
from app.utils.config import EMBEDDING_MODEL, EMBEDDING_CACHE_DIR


class EmbeddingService:
    def __init__(self):
        # 设置缓存目录到项目 cache（便于管理与离线缓存）
        os.environ.setdefault('TRANSFORMERS_CACHE', EMBEDDING_CACHE_DIR)
        os.environ.setdefault('HF_HOME', EMBEDDING_CACHE_DIR)
        os.environ.setdefault('SENTENCE_TRANSFORMERS_HOME', EMBEDDING_CACHE_DIR)

        # 加载中文Embedding模型
        self.model = SentenceTransformer(
            EMBEDDING_MODEL,
            cache_folder=EMBEDDING_CACHE_DIR,
        )

    def encode_text(self, text: str) -> List[float]:
        """将文本转换为向量（返回Python原生list）"""
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def encode_resume(self, raw_content: str, metadata: dict) -> List[float]:
        """
        组合 raw_content 和 metadata 生成综合向量

        策略：将结构化信息拼接到文本前，增加权重
        """
        # 保护性取值，避免KeyError
        name = metadata.get('name') or ''
        skills = metadata.get('skills') or []
        domain = metadata.get('domain') or ''
        education = metadata.get('education') or ''
        work_years = metadata.get('work_years') or 0

        combined_text = (
            f"姓名：{name}\n"
            f"技能：{', '.join(skills)}\n"
            f"领域：{domain}\n"
            f"学历：{education}\n"
            f"工作年限：{work_years}年\n\n"
            f"{raw_content}"
        )
        return self.encode_text(combined_text)