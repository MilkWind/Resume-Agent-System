# /api/resume/detail/{id}

- 方法: GET
- 路径: `/api/resume/detail/{id}`
- 说明: 获取单份简历的结构化详情，`meta` 字段为入库时解析的 `metadata_json`
- 实现位置: `backend/app/routers/resume_search.py` 的 `resume_detail()`

## 请求
- 路径参数:
  - `id` (int): 简历 ID

## 响应
```json
{
  "id": 1,
  "filename": "a.pdf",
  "created_at": "2025-10-19T12:00:00",
  "meta": {
    "name": "张三",
    "phone": "138xxxx",
    "email": "xx@xx.com",
    "location": "上海",
    "education": "本科",
    "work_years": 3,
    "skills": ["Python", "SQL"],
    "experiences": [
      {"company":"XX科技","title":"后端工程师","duration":"2022-至今","desc":"负责..."}
    ]
  }
}
```

## 异常
- 404: `未找到该简历`
- 500: `获取详情失败: ...`

## cURL 示例
```bash
curl -X GET "http://localhost:8000/api/resume/detail/1"
```
