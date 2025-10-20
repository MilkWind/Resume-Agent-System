from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database.base import SessionLocal
from app.database.crud import get_resume_by_id, delete_resume
from app.services.vector_store import vector_store


router = APIRouter(prefix="/api/resume", tags=["简历删除"])


class DeleteResponse(BaseModel):
    success: bool
    message: str


@router.delete("/{resume_id}", response_model=DeleteResponse)
async def delete_resume_api(resume_id: int):
    """删除简历：先删Chroma向量，再删SQLite记录"""
    db = SessionLocal()
    try:
        row = get_resume_by_id(db, resume_id)
        if not row:
            raise HTTPException(status_code=404, detail="简历不存在")

        # 1) 先删向量（幂等，不存在也不会报错）
        try:
            vector_store.delete_resume(resume_id)
        except Exception as e:
            # 若向量库异常，直接抛错，避免产生不一致
            raise HTTPException(status_code=500, detail=f"删除向量失败: {e}")

        # 2) 再删SQLite记录
        _ = delete_resume(db, resume_id)
        return DeleteResponse(success=True, message="删除成功")
    finally:
        db.close()


