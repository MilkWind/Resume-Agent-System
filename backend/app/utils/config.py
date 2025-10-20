from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """应用配置（从 .env 读取）"""
    # Gemini配置
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-flash"
    TEMPERATURE: float = 0.1
    MAX_TOKENS: int = 2000

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


