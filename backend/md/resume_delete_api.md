# /api/resume/{id}

- **方法**: DELETE
- **路径**: `/api/resume/{resume_id}`
- **说明**: 先删除 Chroma 向量，再删除 SQLite 记录，保持一致性。
- **实现位置**: `backend/app/routers/resume_delete.py` 的 `delete_resume_api()`

## 请求
- **Path 参数**:
  - `resume_id`: 整数 ID

## 响应
- **模型**: `DeleteResponse`
```json
{
  "success": true,
  "message": "删除成功"
}
```

## cURL 示例
```bash
curl -X DELETE "http://localhost:8000/api/resume/123"
```
