# 简历信息提取API文档

## 接口概述

本接口用于从PDF格式的简历文件中提取文本内容，基于PaddleOCR实现高精度的中英文识别。

---

## 接口信息

### 基本信息
- **接口路径**: `/api/resume/extract`
- **请求方法**: `POST`
- **Content-Type**: `multipart/form-data`
- **认证方式**: 无需认证

---

## 请求参数

### Body参数（form-data）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | PDF格式的简历文件 |

### 参数说明
- 仅支持 `.pdf` 格式文件
- 建议文件大小不超过 10MB
- 支持中英文混合识别

---

## 响应结果

### 成功响应 (200 OK)

```json
{
  "success": true,
  "filename": "kyt.pdf",
  "pages": 1,
  "content": "况宇桐\n年龄：23岁|性别：男|城市：成都\n电话：17612329669|邮箱：2287185537@qq.com\n..."
}
```

### 响应字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| success | boolean | 处理是否成功 |
| filename | string | 上传的文件名 |
| pages | integer | PDF总页数 |
| content | string | 提取的文本内容，多页用双换行符分隔 |

### 错误响应

#### 1. 文件格式错误 (400 Bad Request)
```json
{
  "detail": "仅支持PDF格式文件"
}
```

#### 2. 服务器处理失败 (500 Internal Server Error)
```json
{
  "detail": "处理失败: [具体错误信息]"
}
```

---

## 调用示例

### 1. cURL 调用

```bash
curl -X POST "http://localhost:8000/api/resume/extract" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/resume.pdf"
```

### 2. Python 调用

```python
import requests

url = "http://localhost:8000/api/resume/extract"
files = {"file": open("resume.pdf", "rb")}

response = requests.post(url, files=files)
result = response.json()

print(f"文件名: {result['filename']}")
print(f"页数: {result['pages']}")
print(f"内容:\n{result['content']}")
```

### 3. JavaScript (Fetch) 调用

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/resume/extract', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('文件名:', data.filename);
  console.log('页数:', data.pages);
  console.log('内容:', data.content);
})
.catch(error => console.error('错误:', error));
```

### 4. Postman 调用步骤

1. 创建新请求，选择 `POST` 方法
2. 输入URL: `http://localhost:8000/api/resume/extract`
3. 切换到 `Body` 标签
4. 选择 `form-data`
5. 添加键值对：
   - Key: `file` (类型选择 `File`)
   - Value: 选择本地PDF文件
6. 点击 `Send` 发送请求

---

## 技术实现

### 核心技术栈
- **OCR引擎**: PaddleOCR (PP-OCRv5)
- **PDF处理**: PyMuPDF (fitz)
- **Web框架**: FastAPI
- **图像处理**: OpenCV, NumPy

### 处理流程
1. 接收上传的PDF文件
2. 逐页将PDF渲染为高分辨率图像（2倍缩放）
3. 保存为临时PNG文件（系统临时目录）
4. 调用PaddleOCR进行文本识别
5. 提取识别结果中的文本内容
6. 自动清理临时文件
7. 返回JSON格式的结果

### 特性说明
- ✅ 支持中英文混合识别
- ✅ 自动文档方向校正
- ✅ 高精度文本检测与识别
- ✅ 自动清理临时文件
- ✅ 异常处理与错误追踪

---

## 注意事项

1. **性能考虑**
   - 首次调用需要下载OCR模型，可能需要较长时间
   - 后续调用会使用缓存模型，速度较快
   - 大文件或多页PDF处理时间较长，请耐心等待

2. **文件要求**
   - 仅支持PDF格式
   - 建议使用清晰的扫描件或原生PDF
   - 图片质量越高，识别准确率越高

3. **安全性**
   - 临时文件存储在系统临时目录
   - 处理完成后自动删除
   - 无需担心文件泄露问题

---

## 错误码说明

| HTTP状态码 | 错误原因 | 解决方案 |
|-----------|---------|---------|
| 400 | 文件格式不正确 | 确保上传的是PDF格式文件 |
| 422 | 缺少必需参数 | 检查是否正确上传了file参数 |
| 500 | 服务器内部错误 | 查看日志或联系管理员 |

---

## 更新日志

### v1.0.0 (2025-01-12)
- ✨ 初始版本发布
- ✨ 支持PDF简历文本提取
- ✨ 支持中英文混合识别
- ✨ 自动文档方向校正
- ✨ 自动清理临时文件

---

## 联系方式

如有问题或建议，请联系开发团队。

