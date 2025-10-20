"""数据库CRUD封装"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from .models import Resume


def create_resume(
    db: Session,
    *,
    filename: str,
    raw_content: str,
    metadata_json: str,
    vector_id: Optional[str] = None,
) -> Resume:
    """创建简历记录并返回对象"""
    resume = Resume(
        filename=filename,
        raw_content=raw_content,
        metadata_json=metadata_json,
        vector_id=vector_id,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def get_resume_by_id(db: Session, resume_id: int) -> Optional[Resume]:
    return db.query(Resume).filter(Resume.id == resume_id).first()


def get_all_resumes(db: Session, skip: int = 0, limit: int = 100) -> List[Resume]:
    return db.query(Resume).order_by(Resume.id.desc()).offset(skip).limit(limit).all()


def count_resumes(db: Session) -> int:
    return db.query(Resume).count()


def update_resume(db: Session, resume_id: int, updates: Dict[str, Any]) -> Optional[Resume]:
    resume = get_resume_by_id(db, resume_id)
    if not resume:
        return None
    for key, value in updates.items():
        if hasattr(resume, key):
            setattr(resume, key, value)
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


def delete_resume(db: Session, resume_id: int) -> Optional[str]:
    """删除简历并返回其 vector_id（用于同步删除向量库）"""
    resume = get_resume_by_id(db, resume_id)
    if not resume:
        return None
    vector_id = resume.vector_id
    db.delete(resume)
    db.commit()
    return vector_id
