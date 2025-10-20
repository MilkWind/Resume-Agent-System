from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import pdf_ocr, resume_search, resume_delete, jd, screening, chat

app = FastAPI(title="智能简历筛选系统", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册简历处理路由
app.include_router(pdf_ocr.router)
# 注册简历搜索路由
app.include_router(resume_search.router)
# 注册简历删除路由
app.include_router(resume_delete.router)
# 注册JD解析路由
app.include_router(jd.router)
# 注册筛选引擎路由
app.include_router(screening.router)
# 注册对话路由
app.include_router(chat.router)
