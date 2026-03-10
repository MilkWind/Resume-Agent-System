# 智能简历筛选 Agent 系统

基于 FastAPI + Next.js 的智能简历筛选系统，支持 PDF 简历 OCR 解析、LLM 结构化抽取、语义检索、三阶段筛选与对话查询。

## 功能概览

- **简历解析**：PDF → OCR 提取文本 → SiliconFlow LLM 结构化元数据（姓名/技能/年限/学历/期望等），写入 SQLite 与向量库。
- **语义检索**：基于 Sentence-Transformers 中文嵌入与 ChromaDB 的 Top-K 检索。
- **筛选引擎**：
  - 阶段1 语义检索初筛。
  - 阶段2 硬性过滤（年限/学历/技能等）。
  - 阶段3 综合评分 + 二次多维度评分（技能/行业/薪资/学历/地点/标签）。
- **自然语言对话**：基于 SiliconFlow + 工具调用，支持查询简历列表/搜索/详情/统计。
- **前端控制台**：上传与批量上传、列表与删除、JD 筛选、对话等。

## 目录结构

```
智能简历筛选Agent系统/
├── backend/                 # FastAPI 后端
│   ├── main.py              # 入口，注册路由与 CORS
│   ├── app/
│   │   ├── routers/         # API 路由
│   │   │   ├── pdf_ocr.py       # /api/resume 提取/解析/批量解析
│   │   │   ├── resume_search.py # /api/resume 列表/搜索/详情/数量
│   │   │   ├── resume_delete.py # /api/resume/{id} 删除
│   │   │   ├── jd.py            # /api/jd 解析
│   │   │   ├── screening.py     # /api/screening 运行筛选
│   │   │   └── chat.py          # /api/chat 对话
│   │   ├── services/        # LLM/嵌入/筛选/向量库等服务
│   │   │   ├── llm_service.py       # SiliconFlow + Pydantic 输出
│   │   │   ├── embedding_service.py # text2vec 中文嵌入
│   │   │   ├── vector_store.py      # ChromaDB 封装
│   │   │   ├── jd_parser.py         # JD 解析 + 检索文本生成
│   │   │   ├── resume_parser.py     # 简历文本 → 元数据
│   │   │   ├── semantic_filter.py   # 阶段1
│   │   │   ├── hard_filter.py       # 阶段2
│   │   │   ├── scoring_engine.py    # 阶段3-一轮评分
│   │   │   └── multi_scoring.py     # 阶段3-二次多维评分
│   │   ├── database/
│   │   │   ├── base.py          # SQLAlchemy 引擎/会话/基类
│   │   │   ├── models.py        # `resumes` 表
│   │   │   └── crud.py          # 简历增删改查
│   │   ├── model/               # Pydantic 数据模型
│   │   │   ├── resume.py        # `ResumeMetadata` 等
│   │   │   └── job_requirement.py
│   │   ├── utils/config.py      # 环境与路径配置
│   │   └── prompts/             # 提示词模板
│   ├── requirements.txt
│   └── .env / env.example
├── frontend/                # Next.js 前端（Ant Design）
│   ├── src/app/page.tsx     # UI：上传/列表/筛选/对话
│   └── ...
└── data/ & backend/data/    # SQLite 与 Chroma 持久化目录
```

## 技术栈

- 后端：`FastAPI`、`SQLAlchemy`、`ChromaDB`、`sentence-transformers`、`LangChain`、`langchain-openai`、`PaddleOCR API`
- 前端：`Next.js 15`、`React 19`、`Ant Design 5`

## 环境与配置

- Python 3.12+
- Node.js 18+
- PaddleOCR API Token、SiliconFlow API Key

后端环境变量（`backend/.env`，参考 `backend/env.example`）：

```
PADDLEOCR_TOKEN=xxxxxx
SILICONFLOW_API_KEY=xxxxxx
```

存储路径（见 `backend/app/utils/config.py`）：

- `SQLITE_DB_URL = "sqlite:///./data/resume.db"` → SQLite 文件位于 `backend/data/resume.db`
- `VECTOR_DB_PATH = "./data/chroma_db"` → ChromaDB 索引位于 `backend/data/chroma_db/`
- `EMBEDDING_MODEL = "shibing624/text2vec-base-chinese"`，缓存目录 `./backend/cache`

前端可选环境变量：

```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

## 启动步骤

- **后端**
  - 进入 `backend/`
  - `pip install -r requirements.txt`
  - 复制 `env.example` 为 `.env` 并填写 `PADDLEOCR_TOKEN`、`SILICONFLOW_API_KEY`
  - 运行：
    ```bash
    uvicorn main:app --reload --port 8000
    ```

- **前端**
  - 进入 `frontend/`
  - `npm install`
  - 如需自定义后端地址，创建 `.env.local` 设置 `NEXT_PUBLIC_API_BASE`
  - 运行：
    ```bash
    npm run dev
    ```

访问前端：http://localhost:3000

## API 速览（主要请求/响应）

- **简历处理 `app/routers/pdf_ocr.py`（前缀 `/api/resume`）**
  - `POST /extract` 表单 `file=pdf` → OCR 文本
  - `POST /parse` 表单 `file=pdf` → OCR+LLM 元数据，写 SQLite 与 Chroma
  - `POST /parse/batch` 表单多文件 `files=pdf...` → 批量解析入库

- **简历列表与检索 `app/routers/resume_search.py`（前缀 `/api/resume`）**
  - `GET /list` → 最近简历列表（id/filename/name/created_at）
  - `GET /count` → 总数
  - `GET /detail/{id}` → 元数据详情
  - `POST /search` `{query, top_k}` → 语义检索（Chroma）

- **删除 `app/routers/resume_delete.py`（前缀 `/api/resume`）**
  - `DELETE /{id}` → 先删向量，再删 SQLite 记录

- **JD 解析 `app/routers/jd.py`（前缀 `/api/jd`）**
  - `POST /parse` `{jd_text}` → 结构化 JD 与检索文本

- **筛选引擎 `app/routers/screening.py`（前缀 `/api/screening`）**
  - `POST /run` `{jd_text, top_k}` → 阶段1语义检索 → 阶段2硬过滤 → 阶段3评分+二次多维评分，返回 `score`、`score2` 与解释项

- **对话 `app/routers/chat.py`（前缀 `/api/chat`）**
  - `POST /send` `{messages:[{role,content}]}` → SiliconFlow Agent 调用工具（列表/搜索/详情/统计）并回复

## 数据模型要点

- **数据库表 `resumes`（见 `app/database/models.py`）**：`id`、`filename`、`raw_content`、`metadata_json`、`vector_id`、时间戳。
- **简历元数据 `ResumeMetadata`（见 `app/model/resume.py`）**：姓名、技能列表、领域、学历、年限、期望薪资、地点、标签、项目/实习摘要等。
- **JD 结构 `JDRequirement`（见 `app/model/job_requirement.py`）**：标题、领域、必备/加分技能、最低学历、年限、地点、薪资等。

## 前端使用说明（`frontend/src/app/page.tsx`）

- **上传/批量上传**：仅支持 PDF，完成后自动入库与向量化。
- **列表与详情**：展示解析出的 `name/skills/...`，支持删除。
- **JD 筛选**：输入 JD 文本与 TopK，查看排序结果与多维度评分解释。
- **简历对话**：与 SiliconFlow 对话，自动调用工具查询简历数据。

## 注意事项

- OCR 使用 PaddleOCR API（PaddleOCR-CL-1.5），异步提交任务并轮询结果。
- 首次运行会在 `backend/data/` 与 `backend/cache/` 下创建数据库、向量库与模型缓存。
---

如需扩展：可替换嵌入模型、引入更强的 OCR/结构化抽取 Prompt、丰富硬过滤规则与评分项、增加导出与面试流程联动等。

