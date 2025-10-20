"""对话接口 - 使用 Gemini 提供咨询与问答，支持查询简历数据库"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
import json

from app.utils.config import get_settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.database.base import SessionLocal
from app.database.crud import get_all_resumes, get_resume_by_id, count_resumes
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/chat", tags=["对话"])


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


# 定义工具函数
@tool
def get_resume_list(limit: int = 20) -> str:
    """获取简历列表，返回最近上传的简历基本信息（姓名、文件名、ID）。
    
    Args:
        limit: 返回的简历数量，默认20条
    """
    try:
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=limit)
            results = []
            for row in rows:
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                results.append({
                    "id": row.id,
                    "filename": row.filename,
                    "name": meta.get("name", "未知"),
                    "skills": meta.get("skills", []),
                    "education": meta.get("education", ""),
                    "work_years": meta.get("work_years", 0),
                })
            return json.dumps(results, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"获取简历列表失败: {str(e)}"


@tool
def search_resumes(query: str, top_k: int = 5) -> str:
    """根据自然语言描述语义搜索简历，返回最匹配的候选人。
    
    Args:
        query: 搜索描述，如"3年Python后端经验"
        top_k: 返回结果数量，默认5条
    """
    try:
        vector_results = vector_store.search(query, top_k)
        db = SessionLocal()
        try:
            results = []
            for r in vector_results:
                resume_id = r.get("resume_id")
                if not resume_id:
                    continue
                row = get_resume_by_id(db, resume_id)
                if not row:
                    continue
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                results.append({
                    "id": row.id,
                    "filename": row.filename,
                    "name": meta.get("name", "未知"),
                    "similarity": round(float(r.get("similarity", 0.0)), 4),
                    "skills": meta.get("skills", []),
                    "domain": meta.get("domain", ""),
                    "education": meta.get("education", ""),
                    "work_years": meta.get("work_years", 0),
                })
            return json.dumps(results, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"搜索简历失败: {str(e)}"


@tool
def get_resume_detail(resume_id: int) -> str:
    """获取指定简历的完整详细信息。
    
    Args:
        resume_id: 简历ID
    """
    try:
        db = SessionLocal()
        try:
            row = get_resume_by_id(db, resume_id)
            if not row:
                return f"未找到ID为{resume_id}的简历"
            meta = json.loads(row.metadata_json) if row.metadata_json else {}
            return json.dumps(meta, ensure_ascii=False, indent=2)
        finally:
            db.close()
    except Exception as e:
        return f"获取简历详情失败: {str(e)}"


tools = [get_resume_list, search_resumes, get_resume_detail]
@tool
def get_resume_count() -> str:
    """获取简历总数量，用于统计与概览。"""
    try:
        db = SessionLocal()
        try:
            total = count_resumes(db)
            return json.dumps({"total": int(total)}, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"获取简历总数失败: {str(e)}"

@tool
def count_resumes_by_candidate_name(name_substr: str) -> str:
    """按候选人姓名包含关键词统计简历份数并返回匹配ID列表。支持模糊匹配。"""
    try:
        q = (name_substr or "").strip().lower()
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=10000)
            ids = []
            for row in rows:
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                name = str(meta.get("name", "")).lower()
                if q and q in name:
                    ids.append(row.id)
            return json.dumps({"query": name_substr, "count": len(ids), "ids": ids}, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"按姓名统计失败: {str(e)}"


@tool
def count_resumes_by_filename(filename_substr: str) -> str:
    """按文件名包含关键词统计简历份数并返回匹配ID列表。支持模糊匹配。"""
    try:
        q = (filename_substr or "").strip().lower()
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=10000)
            ids = [row.id for row in rows if q and q in str(row.filename).lower()]
            return json.dumps({"query": filename_substr, "count": len(ids), "ids": ids}, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"按文件名统计失败: {str(e)}"


def _has_skill(meta: dict, skill: str) -> bool:
    if not meta:
        return False
    skills = meta.get("skills") or []
    # 支持字符串或对象列表
    norm = str(skill or "").strip().lower()
    for s in skills:
        val = str(s if not isinstance(s, dict) else s.get("name", "")).strip().lower()
        if not norm:
            continue
        if norm in val:
            return True
    return False


@tool
def list_candidates_by_skill(skill: str, limit: int = 100) -> str:
    """列出具备某项技能的候选人，返回姓名/ID/文件名。支持包含式匹配与大小写不敏感。"""
    try:
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=10000)
            results = []
            for row in rows:
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                if _has_skill(meta, skill):
                    results.append({
                        "id": row.id,
                        "name": meta.get("name", "未知"),
                        "filename": row.filename,
                    })
                if len(results) >= max(1, int(limit or 100)):
                    break
            return json.dumps(results, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"按技能列出候选失败: {str(e)}"


@tool
def count_candidates_by_skill(skill: str) -> str:
    """统计具备某项技能的候选人数，并返回姓名列表。"""
    try:
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=10000)
            names = []
            for row in rows:
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                if _has_skill(meta, skill):
                    names.append(meta.get("name", "未知"))
            return json.dumps({"skill": skill, "count": len(names), "names": names}, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"按技能统计失败: {str(e)}"


tools = [
    get_resume_list,
    search_resumes,
    get_resume_detail,
    get_resume_count,
    count_resumes_by_candidate_name,
    count_resumes_by_filename,
    list_candidates_by_skill,
    count_candidates_by_skill,
]


@tool
def count_by_education(level: str) -> str:
    """按学历统计（如“硕士”、“本科”、“博士”等，大小写不敏感，包含式匹配）。返回总数与姓名列表。"""
    try:
        key = (level or "").strip().lower()
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=10000)
            names: List[str] = []
            for row in rows:
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                edu = str(meta.get("education", "")).strip().lower()
                if key and key in edu:
                    names.append(meta.get("name", "未知"))
            return json.dumps({"education": level, "count": len(names), "names": names}, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"按学历统计失败: {str(e)}"


@tool
def count_by_location(city_substr: str) -> str:
    """按地点模糊统计（如“上海”、“北京”），大小写不敏感。返回总数与姓名列表。"""
    try:
        key = (city_substr or "").strip().lower()
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=10000)
            names: List[str] = []
            for row in rows:
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                loc = str(meta.get("location", "")).strip().lower()
                if key and key in loc:
                    names.append(meta.get("name", "未知"))
            return json.dumps({"location": city_substr, "count": len(names), "names": names}, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"按地点统计失败: {str(e)}"


@tool
def list_by_years(min_years: int, max_years: int) -> str:
    """按工作年限区间列出候选（闭区间）。返回 id/name/years/filename。"""
    try:
        lo = float(min_years if min_years is not None else 0)
        hi = float(max_years if max_years is not None else 100)
        if lo > hi:
            lo, hi = hi, lo
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=10000)
            results = []
            for row in rows:
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                years = meta.get("work_years")
                try:
                    years = float(years)
                except Exception:
                    years = 0.0
                if lo <= years <= hi:
                    results.append({
                        "id": row.id,
                        "name": meta.get("name", "未知"),
                        "years": years,
                        "filename": row.filename,
                    })
            return json.dumps(results, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"按年限列出失败: {str(e)}"


@tool
def list_by_multi_skills(skills: List[str], mode: str = "intersection") -> str:
    """多技能查询。mode='intersection' 为同时具备全部技能；'union' 为具备任一技能。返回 id/name/filename。"""
    try:
        want = [str(s or "").strip().lower() for s in (skills or []) if str(s or "").strip()]
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=10000)
            results = []
            for row in rows:
                meta = json.loads(row.metadata_json) if row.metadata_json else {}
                skill_vals: List[str] = []
                for s in meta.get("skills") or []:
                    val = str(s if not isinstance(s, dict) else s.get("name", ""))
                    if val:
                        skill_vals.append(val.strip().lower())
                if not want:
                    continue
                if mode == "union":
                    ok = any(any(w in v for v in skill_vals) for w in want)
                else:
                    # intersection: 每个 w 都至少匹配一个技能字符串的子串
                    ok = all(any(w in v for v in skill_vals) for w in want)
                if ok:
                    results.append({
                        "id": row.id,
                        "name": meta.get("name", "未知"),
                        "filename": row.filename,
                    })
            return json.dumps(results, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"多技能查询失败: {str(e)}"


@tool
def count_by_time_range(start: str, end: str) -> str:
    """按上传时间段统计。时间格式 ISO8601（例如 '2025-01-01T00:00:00'）。返回数量与ID列表。"""
    try:
        sdt = datetime.fromisoformat(start) if start else datetime.min
        edt = datetime.fromisoformat(end) if end else datetime.max
        if sdt > edt:
            sdt, edt = edt, sdt
        db = SessionLocal()
        try:
            rows = get_all_resumes(db, skip=0, limit=10000)
            ids: List[int] = []
            for row in rows:
                ts = row.created_at
                if ts and sdt <= ts <= edt:
                    ids.append(row.id)
            return json.dumps({"start": start, "end": end, "count": len(ids), "ids": ids}, ensure_ascii=False)
        finally:
            db.close()
    except Exception as e:
        return f"按时间段统计失败: {str(e)}"


tools = [
    get_resume_list,
    search_resumes,
    get_resume_detail,
    get_resume_count,
    count_resumes_by_candidate_name,
    count_resumes_by_filename,
    list_candidates_by_skill,
    count_candidates_by_skill,
    count_by_education,
    count_by_location,
    list_by_years,
    list_by_multi_skills,
    count_by_time_range,
]


@router.post("/send", response_model=ChatResponse)
async def chat_send(req: ChatRequest):
    """发送对话消息，返回 Gemini 回复（支持工具调用查询简历数据库）"""
    try:
        settings = get_settings()
        llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
            max_output_tokens=2000,
        )
        
        # 构建带工具的 Agent 提示词
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个智能简历筛选助手。你可以帮助用户查询简历数据库、搜索候选人、获取简历详情。"
                      "当用户询问简历相关信息时，使用提供的工具查询数据库。"
                      "回答要简洁明了，使用中文。"),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        
        # 创建 Agent
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
        
        # 构建对话历史
        from langchain_core.messages import HumanMessage, AIMessage
        
        chat_history = []
        for msg in req.messages[:-1]:  # 最后一条消息作为当前输入
            if msg.role == "user":
                chat_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                chat_history.append(AIMessage(content=msg.content))
        
        current_input = req.messages[-1].content if req.messages else ""
        
        # 调用 Agent
        result = await agent_executor.ainvoke({
            "input": current_input,
            "chat_history": chat_history,
        })
        
        return ChatResponse(reply=result["output"])
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"对话失败: {str(e)}")
