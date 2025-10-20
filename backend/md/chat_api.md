# /api/chat/send

- **方法**: POST
- **路径**: `/api/chat/send`
- **说明**: 发送对话消息给 Gemini，返回 AI 回复（支持多轮对话历史 + 工具调用查询简历数据库）
- **实现位置**: `backend/app/routers/chat.py` 的 `chat_send()`
- **特性**: 
  - 使用 LangChain Agent 架构
  - 自动识别用户意图并调用相应工具
  - 支持查询简历列表、语义搜索、获取详情

## 请求
- **Content-Type**: `application/json`
- **Body**:
```json
{
  "messages": [
    { "role": "user", "content": "什么是智能简历筛选？" },
    { "role": "assistant", "content": "智能简历筛选是..." },
    { "role": "user", "content": "如何提高匹配准确率？" }
  ]
}
```

## 响应
- **模型**: `ChatResponse`
```json
{
  "reply": "可以通过优化评分权重、增加训练数据等方式提高匹配准确率..."
}
```

## cURL 示例
```bash
curl -X POST "http://localhost:8000/api/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好"}]}'
```

## 可用工具

Agent 可自动调用以下工具查询数据库（位置：`backend/app/routers/chat.py`）：

### 1. get_resume_list(limit: int = 20)
- **功能**: 获取最近上传的简历基本信息
- **示例**: "列出最近的简历"

### 2. search_resumes(query: str, top_k: int = 5)
- **功能**: 语义搜索简历
- **示例**: "找3年Python后端、熟悉FastAPI的人"

### 3. get_resume_detail(resume_id: int)
- **功能**: 获取指定简历的结构化详情（`metadata_json`）
- **示例**: "查看ID为1的简历详情"

### 4. get_resume_count()
- **功能**: 返回简历总数量
- **示例**: "目前有几份简历？"

### 5. count_resumes_by_candidate_name(name_substr: str)
- **功能**: 按姓名包含关键词统计份数，返回匹配ID列表
- **示例**: "名叫小明的简历有几份？"

### 6. count_resumes_by_filename(filename_substr: str)
- **功能**: 按文件名包含关键词统计份数，返回匹配ID列表

### 7. list_candidates_by_skill(skill: str, limit: int = 100)
- **功能**: 按技能关键词列出候选（`id/name/filename`）
- **示例**: "会 Python 的都有谁，列 20 个"

### 8. count_candidates_by_skill(skill: str)
- **功能**: 统计具备某技能的人数，返回姓名列表

### 9. count_by_education(level: str)
- **功能**: 按学历包含匹配统计（如：本科/硕士/博士）

### 10. count_by_location(city_substr: str)
- **功能**: 按地点模糊统计（如：上海/北京）

### 11. list_by_years(min_years: int, max_years: int)
- **功能**: 按工作年限闭区间列出候选（`id/name/years/filename`）

### 12. list_by_multi_skills(skills: List[str], mode: str = "intersection")
- **功能**: 多技能查询；`intersection` 同时具备全部技能，`union` 任一技能匹配

### 13. count_by_time_range(start: str, end: str)
- **功能**: 按上传时间段统计（ISO8601），返回数量与ID列表

## 使用示例

```bash
# 查询简历列表
curl -X POST "http://localhost:8000/api/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"有多少份简历？"}]}'

# 搜索候选人
curl -X POST "http://localhost:8000/api/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"找一个Python后端工程师"}]}'

# 获取详情
curl -X POST "http://localhost:8000/api/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"查看ID为1的简历详情"}]}'

# 统计示例：会 Python 的都有谁
curl -X POST "http://localhost:8000/api/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"会 Python 的都有谁？列 20 个"}]}'

# 统计示例：硕士有几人
curl -X POST "http://localhost:8000/api/chat/send" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"硕士有几人？"}]}'
```

## 备注
- 需要 `.env` 中配置 `GEMINI_API_KEY`
- `temperature` 设为 0.7，适合对话场景
- 支持多轮对话上下文
- Agent 会自动判断何时调用工具，无需手动指定
- 工具调用过程在后端日志中可见（`verbose=True`）
