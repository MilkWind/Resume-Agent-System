# /api/resume/parse

- **方法**: POST
- **路径**: `/api/resume/parse`
- **说明**: 上传 PDF 简历，后端执行 OCR → LLM 结构化解析 → 写入 SQLite 与 Chroma 向量库，返回解析结果。
- **实现位置**: `backend/app/routers/pdf_ocr.py` 的 `parse_resume()`

## 请求
- **Content-Type**: `multipart/form-data`
- **Form 字段**:
  - `file`: PDF 文件（后缀 `.pdf`）

## 响应
- **模型**: `ResumeParseResponse`（`backend/app/model/resume.py`）
```json
{
  "success": true,
  "filename": "xxx.pdf",
  "pages": 2,
  "raw_content": "...OCR提取的原始文本...",
  "metadata": {
    "name": "张三",
    "phone": "...",
    "email": "...",
    "skills": ["Python", "SQL"],
    "domain": "信息技术",
    "education": "本科",
    "work_years": 3,
    "major": "软件工程",
    "expected_salary": "15-20K",
    "current_location": ["上海"],
    "custom_tags": ["沟通能力强"],
    "projects": ["..."],
    "internships": ["..."]
  }
}
```

## cURL 示例
```bash
curl -X POST "http://localhost:8000/api/resume/parse" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./kyt.pdf"
```

## 备注
- 需要 `.env` 中配置 `GEMINI_API_KEY`。
- 数据将写入 `SQLite(./data/resume.db)` 与 `Chroma(./data/chroma_db)`。

---

# 批量上传解析 /api/resume/parse/batch

- **方法**: POST
- **路径**: `/api/resume/parse/batch`
- **说明**: 支持一次上传多个 PDF，逐个执行 OCR → LLM 解析并入库，返回每个文件的处理结果。
- **实现位置**: `backend/app/routers/pdf_ocr.py` 的 `parse_resume_batch()`

## 请求
- **Content-Type**: `multipart/form-data`
- **Form 字段**:
  - `files`: 多个 PDF 文件（可重复追加此字段）

## 响应
- **模型**: `ResumeParseBatchResponse`
```json
{
  "results": [
    {
      "filename": "a.pdf",
      "success": true,
      "pages": 2,
      "raw_content": "...",
      "metadata": { "name": "张三", "skills": ["Python"] }
    },
    {
      "filename": "b.txt",
      "success": false,
      "error": "仅支持PDF格式文件"
    }
  ],
  "success_count": 1,
  "fail_count": 1
}
```

## cURL 示例
```bash
curl -X POST "http://localhost:8000/api/resume/parse/batch" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@./a.pdf" \
  -F "files=@./b.pdf"
```
