"""数据库模型定义"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from .base import Base


class Resume(Base):
    """简历主表

    大白话说明：存储每份简历的原始文本、结构化信息（JSON字符串）以及在向量库中的ID
    """

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    raw_content = Column(Text, nullable=False)
    metadata_json = Column(Text, nullable=False)
    vector_id = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
