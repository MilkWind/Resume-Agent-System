# /api/screening/run

- **方法**: POST
- **路径**: `/api/screening/run`
- **说明**: 三阶段筛选（语义检索→硬过滤→第一轮评分）后，执行六维度二次评分并返回结果。
- **实现位置**: `backend/app/routers/screening.py` 的 `run_screening()`

## 请求
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "jd_text": "【职位名称】AI 应用后端工程师（Python/LLM）...",
  "top_k": 10
}
```

## 响应
- **模型**: `ScreeningResponse`
```json
{
  "results": [
    {
      "id": 1,
      "filename": "xxx.pdf",
      "score": 0.812345,
      "explain": {
        "similarity": 0.9,
        "skills_cover": 0.8,
        "skills_bonus": 0.2,
        "years_match": 1.0
      },
      "score2": 0.865432,
      "explain2": {
        "skills": 0.9,
        "domain": 1.0,
        "salary": 0.7,
        "education": 1.0,
        "location": 1.0,
        "tags": 0.5
      },
      "metadata": { "name": "张三", "skills": ["Python"], "education": "本科", "current_location": ["上海"] }
    }
  ]
}
```

## cURL 示例
```bash
curl -X POST "http://localhost:8000/api/screening/run" \
  -H "Content-Type: application/json" \
  -d '{"jd_text":"【职位名称】AI 应用后端工程师（Python/LLM）...","top_k":10}'
```
