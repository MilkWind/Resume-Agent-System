from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.jd_parser import jd_parser
from app.model.job_requirement import JDParseResponse


router = APIRouter(prefix="/api/jd", tags=["JD解析"])


class JDParseRequest(BaseModel):
    jd_text: str


@router.post("/parse", response_model=JDParseResponse)
async def parse_jd(req: JDParseRequest):
    try:
        jd = await jd_parser.parse(req.jd_text)
        q = jd_parser.build_query_text(jd)
        return JDParseResponse(success=True, jd=jd, query_text=q)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD解析失败: {e}")


