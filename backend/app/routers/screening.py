from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json

from app.services.jd_parser import jd_parser
from app.services.semantic_filter import semantic_filter
from app.services.hard_filter import hard_filter
from app.services.scoring_engine import scoring_engine
from app.services.multi_scoring import multi_scoring_engine
from app.database.base import SessionLocal
from app.database.crud import get_resume_by_id

router = APIRouter(prefix="/api/screening", tags=["筛选引擎"])

class ScreeningRequest(BaseModel):
    jd_text: str
    top_k: int = 10

class ScreeningResultItem(BaseModel):
    id: int
    filename: str
    score: float
    explain: Dict[str, float]
    score2: float
    explain2: Dict[str, float]
    metadata: Dict[str, Any]

class ScreeningResponse(BaseModel):
    results: List[ScreeningResultItem]

@router.post("/run", response_model=ScreeningResponse)
async def run_screening(req: ScreeningRequest):
    try:
        # 1. 解析JD
        jd = await jd_parser.parse(req.jd_text)
        query_text = jd_parser.build_query_text(jd)

        # 2. 语义检索TopK
        vec_res = semantic_filter.search(query_text, req.top_k)

        # 3. 回表读取完整简历数据
        db = SessionLocal()
        try:
            rows: List[Dict[str, Any]] = []
            for r in vec_res:
                rid = r.get("resume_id")
                if rid is None:
                    continue
                row = get_resume_by_id(db, rid)
                if not row:
                    continue
                rows.append({
                    "id": row.id,
                    "filename": row.filename,
                    "metadata_json": row.metadata_json,
                    "similarity": r.get("similarity", 0.0),
                })
        finally:
            db.close()

        # 4. 硬过滤（若结果为空，则回退到语义TopK，避免空结果）
        filtered = hard_filter.filter(jd.model_dump(), rows)
        candidate_rows = filtered if filtered else rows

        # 5. 第一轮综合评分
        ranked = scoring_engine.score(jd.model_dump(), candidate_rows)

        # 6. 第二轮多维度评分（对第一轮候选再次评分，而非优化第一轮得分）
        ranked2 = multi_scoring_engine.score(jd.model_dump(), ranked)

        # 7. 构造返回（包含二次评分字段）
        results: List[ScreeningResultItem] = []
        for item in ranked2:
            meta = json.loads(item["metadata_json"]) if isinstance(item.get("metadata_json"), str) else item.get("metadata", {})
            results.append(ScreeningResultItem(
                id=item["id"],
                filename=item["filename"],
                score=item.get("score", 0.0),
                explain=item.get("explain", {}),
                score2=item.get("score2", 0.0),
                explain2=item.get("explain2", {}),
                metadata=meta,
            ))

        return ScreeningResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"筛选失败: {e}")
