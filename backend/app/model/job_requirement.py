from typing import List, Optional
from pydantic import BaseModel, Field


class JDRequirement(BaseModel):
    """职位需求结构化模型（由JD文本解析而来）

    大白话：把岗位的硬性条件和关键信息结构化，方便筛选与打分
    """

    title: Optional[str] = Field(default=None, description="职位名称")
    domain: Optional[str] = Field(default=None, description="所属领域/部门")
    skills_required: List[str] = Field(default_factory=list, description="必须具备的技能列表")
    skills_nice: List[str] = Field(default_factory=list, description="加分技能列表")
    min_education: Optional[str] = Field(default=None, description="最低学历要求：专科/本科/硕士/博士")
    min_work_years: int = Field(default=0, ge=0, description="最低工作年限要求（年）")
    locations: List[str] = Field(default_factory=list, description="工作城市/地点")
    salary: Optional[str] = Field(default=None, description="薪资范围，如'20-30K' 或 '面议'")
    description: Optional[str] = Field(default=None, description="JD原文摘要或关键说明")


class JDParseResponse(BaseModel):
    success: bool
    jd: JDRequirement
    query_text: str


