from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import json

from app.services.vector_store import vector_store
from app.database.base import SessionLocal
from app.database.crud import get_resume_by_id, get_all_resumes, count_resumes


router = APIRouter(prefix="/api/resume", tags=["简历搜索"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10


class SearchResultItem(BaseModel):
    id: int
    filename: str
    similarity: float
    name: str


class SearchResponse(BaseModel):
    results: List[SearchResultItem]


@router.post("/search", response_model=SearchResponse)
async def search_resume(req: SearchRequest):
    """语义检索简历（Step 4）"""
    try:
        vector_results = vector_store.search(req.query, req.top_k)
        db = SessionLocal()
        items: List[SearchResultItem] = []
        try:
            for r in vector_results:
                resume_id = r.get("resume_id")
                if resume_id is None:
                    continue
                row = get_resume_by_id(db, resume_id)
                if not row:
                    continue
                items.append(SearchResultItem(
                    id=row.id,
                    filename=row.filename,
                    similarity=round(float(r.get("similarity", 0.0)), 6),
                    name=r.get("name") or "",
                ))
        finally:
            db.close()

        return SearchResponse(results=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {e}")


class ResumeListItem(BaseModel):
    id: int
    filename: str
    name: str
    created_at: str


class ResumeListResponse(BaseModel):
    results: List[ResumeListItem]


@router.get("/list", response_model=ResumeListResponse)
async def list_resumes():
    """获取所有简历列表"""
    try:
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=1000)
            items: List[ResumeListItem] = []
            for row in rows:
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                items.append(ResumeListItem(
                    id=row.id,
                    filename=row.filename,
                    name=meta.get("name", "未知"),
                    created_at=row.created_at.isoformat() if row.created_at else "",
                ))
            return ResumeListResponse(results=items)
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取列表失败: {e}")



class ResumeCountResponse(BaseModel):
    total: int


@router.get("/count", response_model=ResumeCountResponse)
async def resume_count():
    try:
        db = SessionLocal()
        try:
            total = count_resumes(db)
            return ResumeCountResponse(total=total)
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数量失败: {e}")


class ResumeDetailResponse(BaseModel):
    id: int
    filename: str
    created_at: str
    meta: dict


@router.get("/detail/{resume_id}", response_model=ResumeDetailResponse)
async def resume_detail(resume_id: int):
    try:
        db = SessionLocal()
        try:
            row = get_resume_by_id(db, resume_id)
            if not row:
                raise HTTPException(status_code=404, detail="未找到该简历")
            meta = json.loads(row.metadata_json) if row.metadata_json else {}
            return ResumeDetailResponse(
                id=row.id,
                filename=row.filename,
                created_at=row.created_at.isoformat() if row.created_at else "",
                meta=meta,
            )
        finally:
            db.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取详情失败: {e}")

