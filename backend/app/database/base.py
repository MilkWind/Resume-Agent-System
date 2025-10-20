"""数据库基础配置：引擎、会话、基类

大白话说明：
- 这里创建SQLite连接和Session工厂，其他模块直接引用使用即可
- 会自动在项目的 data 目录下创建数据库文件
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.utils.config import SQLITE_DB_URL


# 确保数据库文件所在目录存在（例如 ./data）
def _ensure_db_dir(db_url: str) -> None:
    if db_url.startswith("sqlite:///./"):
        db_path = db_url.replace("sqlite:///./", "")
        db_file = Path(db_path)
        db_dir = db_file.parent
        db_dir.mkdir(parents=True, exist_ok=True)


_ensure_db_dir(SQLITE_DB_URL)

# SQLite 在多线程下需要特殊参数
engine = create_engine(
    SQLITE_DB_URL,
    connect_args={"check_same_thread": False} if SQLITE_DB_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base() # 数据库基类


