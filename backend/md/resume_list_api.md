# /api/resume/list 与 /api/resume/count

## /api/resume/list
- **方法**: GET
- **路径**: `/api/resume/list`
- **说明**: 获取所有简历列表（最多1000条，按 `id` 倒序）
- **实现位置**: `backend/app/routers/resume_search.py` 的 `list_resumes()`

### 请求
- 无需参数

### 响应
```json
{
  "results": [
    { "id": 3, "filename": "b.pdf", "name": "李四", "created_at": "2025-10-19T12:34:56" },
    { "id": 2, "filename": "a.pdf", "name": "张三", "created_at": "2025-10-18T08:00:00" }
  ]
}
```

### cURL 示例
```bash
curl -X GET "http://localhost:8000/api/resume/list"
```

## /api/resume/count
- **方法**: GET
- **路径**: `/api/resume/count`
- **说明**: 返回数据库中的简历总数
- **实现位置**: `backend/app/routers/resume_search.py` 的 `resume_count()`

### 响应
```json
{ "total": 12 }
```

### cURL 示例
```bash
curl -X GET "http://localhost:8000/api/resume/count"
```

## 备注
- 默认返回最新 1000 条记录
- 按创建时间倒序排列
