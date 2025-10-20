# /api/resume/search

- **方法**: POST
- **路径**: `/api/resume/search`
- **说明**: 按自然语言语义检索简历，返回 Top-K 结果（含相似度与基础信息）。
- **实现位置**: `backend/app/routers/resume_search.py` 的 `search_resume()`

## 请求
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "query": "3年以上Python后端经验，熟悉LangChain",
  "top_k": 10
}
```

## 响应
- **模型**: `SearchResponse`
```json
{
  "results": [
    {
      "id": 12,
      "filename": "xxx.pdf",
      "similarity": 0.873421,
      "name": "张三"
    }
  ]
}
```

## cURL 示例
```bash
curl -X POST "http://localhost:8000/api/resume/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"Python 后端 LLM","top_k":10}'
```
