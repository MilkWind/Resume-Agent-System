from pydantic import BaseModel, Field
from typing import List, Optional

# === 简历元数据模型（LLM提取的结构化信息）===
class ResumeMetadata(BaseModel):
    """简历结构化元数据"""
    # 基本信息
    name: str = Field(..., description="候选人姓名")
    phone: Optional[str] = Field(None, description="联系电话")
    email: Optional[str] = Field(None, description="电子邮箱")
    
    # 核心信息
    skills: List[str] = Field(default_factory=list, description="技能列表，最多10个核心技能")
    domain: str = Field(default="未知", description="所属领域，如：IT/金融/销售")
    education: str = Field(default="未知", description="最高学历：专科/本科/硕士/博士")
    work_years: int = Field(default=0, description="工作年限（整数）", ge=0)
    major: Optional[str] = Field(None, description="专业名称，例如'人工智能'、'软件工程'")
    
    # 期望信息
    expected_salary: str = Field(default="面议", description="期望薪资，如'15-20K'，未提及则为'面议'")
    current_location: List[str] = Field(default_factory=list, description="现居地")
    
    # 附加信息
    custom_tags: List[str] = Field(default_factory=list, description="个性标签，如'技术专家'")
    projects: List[str] = Field(default_factory=list, description="项目经验摘要列表（每项建议一句话摘要）")
    internships: List[str] = Field(default_factory=list, description="实习经历摘要列表（每项建议一句话摘要）")

# === API响应模型 ===
class ResumeExtractResponse(BaseModel):
    """简历提取响应（OCR）"""
    success: bool
    filename: str
    pages: int
    content: str

class ResumeParseResponse(BaseModel):
    """简历解析响应（OCR + LLM结构化）"""
    success: bool
    filename: str
    pages: int
    raw_content: str           # OCR原始文本
    metadata: ResumeMetadata   # LLM提取的结构化信息

# === 批量解析响应模型 ===
class ResumeParseItemResult(BaseModel):
    """批量解析中的单个文件结果"""
    filename: str
    success: bool
    pages: Optional[int] = None
    raw_content: Optional[str] = None
    metadata: Optional[ResumeMetadata] = None
    error: Optional[str] = None

class ResumeParseBatchResponse(BaseModel):
    """批量解析响应（多文件）"""
    results: List[ResumeParseItemResult]
    success_count: int
    fail_count: int
