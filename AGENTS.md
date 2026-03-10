# 智能简历筛选 Agent 系统 - Agent 上下文文档

## 项目概述

这是一个基于 FastAPI + Next.js 的智能简历筛选系统，支持 PDF 简历 OCR 解析、LLM 结构化抽取、语义检索、三阶段筛选与自然语言对话查询。

### 核心功能

- **简历解析**：PDF → OCR 提取文本 → SiliconFlow LLM 结构化元数据（姓名/技能/年限/学历/期望等），写入 SQLite 与向量库
- **语义检索**：基于 Sentence-Transformers 中文嵌入与 ChromaDB 的 Top-K 检索
- **三阶段筛选引擎**：
  - 阶段 1：语义检索初筛
  - 阶段 2：硬性过滤（年限/学历/技能等）
  - 阶段 3：综合评分 + 二次多维度评分（技能/行业/薪资/学历/地点/标签）
- **自然语言对话**：基于 SiliconFlow (DeepSeek-V3.2) + 工具调用，支持查询简历列表/搜索/详情/统计
- **前端控制台**：上传与批量上传、列表与删除、JD 筛选、对话等

### 技术栈

**后端：**
- `FastAPI` - Web 框架
- `SQLAlchemy` - ORM
- `ChromaDB` - 向量数据库
- `sentence-transformers` - 文本嵌入（中文模型：shibing624/text2vec-base-chinese）
- `LangChain` + `langchain-google-genai` - LLM 集成
- `PaddleOCR API` - PDF OCR 识别（PaddleOCR-CL-1.5，异步解析）
- `Pydantic` - 数据验证

**前端：**
- `Next.js 15` - React 框架
- `React 19` - UI 库
- `Ant Design 5` - 组件库
- `TypeScript` - 类型安全

**数据库：**
- SQLite - 结构化数据存储
- ChromaDB - 向量检索存储

## 构建和运行

### 环境要求

- Python 3.12+
- Node.js 18+
- PaddleOCR API Token（aistudio 获取，用于 PDF OCR）
- SiliconFlow API Key（LLM：简历抽取、JD 解析、智能对话）

### 后端启动

```bash
cd backend
pip install -r requirements.txt
# 复制 env.example 为 .env 并填写 PADDLEOCR_TOKEN、SILICONFLOW_API_KEY
cp env.example .env
uvicorn main:app --reload --port 8000
```

后端将在 `http://localhost:8000` 启动

### 前端启动

```bash
cd frontend
npm install
# 可选：创建 .env.local 设置 NEXT_PUBLIC_API_BASE
npm run dev
```

前端将在 `http://localhost:3000` 启动

### 数据存储路径

- SQLite 数据库：`backend/data/resume.db`
- ChromaDB 向量库：`backend/data/chroma_db/`
- 模型缓存：`backend/cache/`

## 项目结构

```
Resume-Agent-System/
├── backend/                          # FastAPI 后端
│   ├── main.py                       # 入口文件，注册路由与 CORS
│   ├── requirements.txt              # Python 依赖
│   ├── env.example                   # 环境变量示例
│   ├── app/
│   │   ├── routers/                  # API 路由
│   │   │   ├── pdf_ocr.py            # /api/resume 提取/解析/批量解析
│   │   │   ├── resume_search.py      # /api/resume 列表/搜索/详情/数量
│   │   │   ├── resume_delete.py      # /api/resume/{id} 删除
│   │   │   ├── jd.py                 # /api/jd 解析
│   │   │   ├── screening.py          # /api/screening 运行筛选
│   │   │   └── chat.py               # /api/chat 对话
│   │   ├── services/                 # 核心服务
│   │   │   ├── llm_service.py        # SiliconFlow + Pydantic 输出
│   │   │   ├── embedding_service.py  # text2vec 中文嵌入
│   │   │   ├── vector_store.py       # ChromaDB 封装
│   │   │   ├── jd_parser.py          # JD 解析 + 检索文本生成
│   │   │   ├── resume_parser.py      # 简历文本 → 元数据
│   │   │   ├── paddle_ocr_service.py # PaddleOCR-CL-1.5 API 异步解析
│   │   │   ├── semantic_filter.py    # 阶段1：语义过滤
│   │   │   ├── hard_filter.py        # 阶段2：硬性过滤
│   │   │   ├── scoring_engine.py     # 阶段3：一轮评分
│   │   │   └── multi_scoring.py      # 阶段3：二次多维评分
│   │   ├── database/                 # 数据库层
│   │   │   ├── base.py               # SQLAlchemy 引擎/会话/基类
│   │   │   ├── models.py             # Resume 表模型
│   │   │   └── crud.py               # 简历增删改查
│   │   ├── model/                    # Pydantic 数据模型
│   │   │   ├── resume.py             # ResumeMetadata 等
│   │   │   └── job_requirement.py    # JDRequirement 等
│   │   ├── utils/
│   │   │   └── config.py             # 环境与路径配置
│   │   └── prompts/                  # 提示词模板
│   │       ├── jd_extraction.py      # JD 提取提示词
│   │       └── resume_extraction.py  # 简历提取提示词
│   ├── data/                         # 数据存储目录（运行时创建）
│   │   ├── resume.db                 # SQLite 数据库
│   │   └── chroma_db/                # ChromaDB 向量库
│   └── cache/                        # 模型缓存目录
├── frontend/                         # Next.js 前端
│   ├── src/app/
│   │   ├── page.tsx                  # 主页面：上传/列表/筛选/对话
│   │   ├── layout.tsx                # 布局组件
│   │   └── globals.css               # 全局样式
│   ├── package.json                  # Node.js 依赖
│   └── next.config.ts                # Next.js 配置
└── README.md                         # 项目说明文档
```

## API 端点概览

### 简历处理 (`/api/resume`)

- `POST /api/resume/extract` - OCR 提取 PDF 文本
  - 请求：FormData `{ file: PDF }`
  - 响应：`{ success, filename, pages, content }`

- `POST /api/resume/parse` - 解析简历（OCR + LLM）
  - 请求：FormData `{ file: PDF }`
  - 响应：`{ success, filename, pages, raw_content, metadata }`

- `POST /api/resume/parse/batch` - 批量解析简历
  - 请求：FormData `{ files: PDF[] }`
  - 响应：`{ results: [], success_count, fail_count }`

- `GET /api/resume/list` - 获取简历列表
  - 响应：`{ results: [{ id, filename, name, created_at }] }`

- `GET /api/resume/count` - 获取简历总数
  - 响应：`{ count }`

- `GET /api/resume/detail/{id}` - 获取简历详情
  - 响应：`{ id, filename, created_at, meta }`

- `POST /api/resume/search` - 语义搜索
  - 请求：`{ query, top_k }`
  - 响应：`{ results: [{ id, filename, similarity }] }`

- `DELETE /api/resume/{id}` - 删除简历
  - 响应：`{ success }`

### JD 解析 (`/api/jd`)

- `POST /api/jd/parse` - 解析 JD 文本
  - 请求：`{ jd_text }`
  - 响应：`{ jd: JDRequirement, search_text }`

### 筛选引擎 (`/api/screening`)

- `POST /api/screening/run` - 运行三阶段筛选
  - 请求：`{ jd_text, top_k }`
  - 响应：`{ results: [{ id, filename, score, explain, score2, explain2, metadata }] }`

### 对话接口 (`/api/chat`)

- `POST /api/chat/send` - 发送对话消息
  - 请求：`{ messages: [{ role, content }] }`
  - 响应：`{ reply }`

## 核心数据模型

### 简历元数据 (ResumeMetadata)

```python
{
    "name": str,                    # 候选人姓名
    "phone": str,                   # 联系电话
    "email": str,                   # 电子邮箱
    "skills": List[str],            # 技能列表（最多10个）
    "domain": str,                  # 所属领域（IT/金融/销售）
    "education": str,               # 最高学历（专科/本科/硕士/博士）
    "work_years": int,              # 工作年限
    "major": str,                   # 专业名称
    "expected_salary": str,         # 期望薪资
    "current_location": List[str],  # 现居地
    "custom_tags": List[str],       # 个性标签
    "projects": List[str],          # 项目经验摘要
    "internships": List[str]        # 实习经历摘要
}
```

### JD 要求 (JDRequirement)

```python
{
    "title": str,                   # 职位标题
    "domain": str,                  # 领域
    "skills_required": List[str],   # 必备技能
    "skills_nice": List[str],       # 加分技能
    "min_education": str,           # 最低学历
    "min_work_years": int,          # 最低年限
    "location": str,                # 地点
    "salary_range": str             # 薪资范围
}
```

### 数据库表 (Resume)

- `id` - 主键
- `filename` - 文件名
- `raw_content` - OCR 原始文本
- `metadata_json` - 结构化元数据（JSON）
- `vector_id` - 向量库 ID
- `created_at` - 创建时间
- `updated_at` - 更新时间

## 开发约定

### 环境配置

- 后端环境变量在 `backend/.env` 中配置
- 必需：`PADDLEOCR_TOKEN`（aistudio 获取）、`SILICONFLOW_API_KEY`（LLM）
- 可选：`PADDLEOCR_MODEL`、`SILICONFLOW_CHAT_MODEL`（默认：Pro/deepseek-ai/DeepSeek-V3.2）、`SILICONFLOW_TEMPERATURE`、`SILICONFLOW_MAX_TOKENS`
- 前端环境变量：`NEXT_PUBLIC_API_BASE`（默认：http://localhost:8000）

### 代码规范

- 后端使用 Python 3.12+，遵循 PEP 8 规范
- 前端使用 TypeScript + React 19，遵循 ESLint 配置
- API 响应使用 Pydantic 模型进行验证
- 数据库操作使用 SQLAlchemy ORM
- 向量检索使用 ChromaDB

### 筛选流程

三阶段筛选流程：

1. **阶段 1 - 语义检索**：使用 Sentence-Transformers 中文嵌入模型进行 Top-K 检索
2. **阶段 2 - 硬性过滤**：根据 JD 的硬性要求（年限、学历、技能等）进行过滤
3. **阶段 3 - 综合评分**：
   - 一轮评分：相似度（50%）+ 技能覆盖（30%）+ 加分技能（10%）+ 年限匹配（10%）
   - 二次多维评分：技能/行业/薪资/学历/地点/标签六个维度分别评分

### OCR 处理

- 使用 PaddleOCR API（PaddleOCR-CL-1.5）进行 PDF 文本提取
- 异步提交任务并轮询结果，无需本地模型
- 处理期间使用系统临时目录

## 扩展建议

- 替换嵌入模型（当前使用：shibing624/text2vec-base-chinese）
- 引入更强的 OCR/结构化抽取 Prompt
- 丰富硬过滤规则与评分项
- 增加导出与面试流程联动
- 支持更多简历格式（Word、图片等）
- 添加用户认证与权限管理
- 实现简历标注与反馈机制

## 注意事项

- 首次运行会在 `backend/data/` 与 `backend/cache/` 下创建数据库、向量库与模型缓存
- OCR 处理可能较慢，建议批量上传时控制文件数量
- SiliconFlow API 有调用频率限制，注意控制并发请求
- 删除简历时需要先删除向量库记录，再删除 SQLite 记录
- 前端默认使用 Ant Design 组件，保持 UI 一致性