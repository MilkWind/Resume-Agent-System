# 数据模型说明

## SQLite 表：`resumes`
- **定义**: `backend/app/database/models.py` → `Resume`
- **字段**:
  - `id: int` 主键，自增
  - `filename: str` 原始文件名
  - `raw_content: Text` OCR提取的完整文本
  - `metadata_json: Text` LLM 结构化结果的 JSON 串
  - `vector_id: str?` 对应 Chroma 文档 ID（`resume_{id}`）
  - `created_at: datetime`
  - `updated_at: datetime`

## Pydantic：简历元数据 `ResumeMetadata`
- **定义**: `backend/app/model/resume.py`
- **字段**:
  - `name: str`
  - `phone: Optional[str]`
  - `email: Optional[str]`
  - `skills: List[str]`
  - `domain: str`
  - `education: str`（专科/本科/硕士/博士）
  - `work_years: int`
  - `major: Optional[str]`
  - `expected_salary: str`（默认“面议”）
  - `current_location: List[str]`
  - `custom_tags: List[str]`
  - `projects: List[str]`
  - `internships: List[str]`

## Pydantic：职位需求 `JDRequirement`
- **定义**: `backend/app/model/job_requirement.py`
- **字段**:
  - `title: Optional[str]`
  - `domain: Optional[str]`
  - `skills_required: List[str]`
  - `skills_nice: List[str]`
  - `min_education: Optional[str]`
  - `min_work_years: int`
  - `locations: List[str]`
  - `salary: Optional[str]`
  - `description: Optional[str]`

## 向量库 Chroma（集合：`resumes`）
- **文档ID**: `resume_{id}`
- **metadatas**:
  - `resume_id: int`
  - `name: str`
  - `skills: str`（逗号分隔）
  - `domain: str`
- **documents**: `raw_content` 的前 500 字作为预览

## 配置与路径
- `./data/resume.db`：SQLite 数据库
- `./data/chroma_db`：Chroma 持久化目录
- `./cache`：Embedding 模型缓存（`shibing624/text2vec-base-chinese`）
- `.env`：需配 `GEMINI_API_KEY` 等
