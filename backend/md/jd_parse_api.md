# /api/jd/parse

- **方法**: POST
- **路径**: `/api/jd/parse`
- **说明**: 解析 JD 文本为结构化 `JDRequirement`，并生成语义检索用的 `query_text`。
- **实现位置**: `backend/app/routers/jd.py` 的 `parse_jd()`

## 请求
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "jd_text": "【职位名称】AI 应用后端工程师（Python/LLM）..."
}
```

## 响应
- **模型**: `JDParseResponse`
```json
{
  "success": true,
  "jd": {
    "title": "...",
    "domain": "信息技术",
    "skills_required": ["Python", "SQL"],
    "skills_nice": ["LangChain"],
    "min_education": "本科",
    "min_work_years": 1,
    "locations": ["上海"],
    "salary": "20-30K",
    "description": "..."
  },
  "query_text": "必须技能:Python,SQL\n加分技能:LangChain\n信息技术\n最低学历:本科\n年限>=1\n地点:上海\n薪资:20-30K\n摘要:..."
}
```

## cURL 示例
```bash
curl -X POST "http://localhost:8000/api/jd/parse" \
  -H "Content-Type: application/json" \
  -d '{"jd_text":"【职位名称】AI 应用后端工程师（Python/LLM）..."}'
```
