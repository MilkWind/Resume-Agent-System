from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置（从 .env 读取）"""
    # PaddleOCR API 配置（用于 PDF OCR）
    PADDLEOCR_TOKEN: str = ""
    PADDLEOCR_JOB_URL: str = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
    PADDLEOCR_MODEL: str = "PaddleOCR-CL-1.5"

    # SiliconFlow 配置（LLM：简历抽取、JD 解析、智能对话，OpenAI 兼容 API）
    SILICONFLOW_API_KEY: str = ""
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_CHAT_MODEL: str = "Pro/deepseek-ai/DeepSeek-V3.2"
    SILICONFLOW_TEMPERATURE: float = 0.1
    SILICONFLOW_MAX_TOKENS: int = 2000

    # pydantic-settings v2 配置
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()

# 配置项
EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"
EMBEDDING_CACHE_DIR = "./cache"          # 模型缓存目录
VECTOR_DB_PATH = "./data/chroma_db"      # ChromaDB存储路径
SQLITE_DB_URL = "sqlite:///./data/resume.db"  # SQLite数据库路径


