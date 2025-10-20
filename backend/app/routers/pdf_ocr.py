import warnings
import os
import shutil
import uuid
from pathlib import Path
import fitz
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from paddleocr import PaddleOCR
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from app.model.resume import (
    ResumeExtractResponse,
    ResumeParseResponse,
    ResumeParseBatchResponse,
    ResumeParseItemResult,
)
from app.services.resume_parser import resume_parser
from app.database.base import SessionLocal, Base, engine
from app.database.models import Resume as ResumeModel
from app.database.crud import create_resume, update_resume
from app.services.vector_store import vector_store

# 抑制警告信息
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*ccache.*")
warnings.filterwarnings("ignore", message=".*No ccache found.*")

router = APIRouter(prefix="/api/resume", tags=["简历处理"])

# 初始化 PaddleOCR
ocr = PaddleOCR(
    use_textline_orientation=True,  
    lang='ch'
)

# 使用系统临时目录，避免中文路径问题
import tempfile
TEMP_BASE_DIR = Path(tempfile.gettempdir()) / "resume_ocr_temp"
TEMP_BASE_DIR.mkdir(exist_ok=True)

@router.post("/extract", response_model=ResumeExtractResponse)
async def extract_resume_info(file: UploadFile = File(...)):
    """提取PDF简历信息"""
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持PDF格式文件")
    
    # 创建唯一的临时子目录（使用短UUID避免路径过长）
    session_id = uuid.uuid4().hex[:8]
    temp_dir = TEMP_BASE_DIR / session_id
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # 读取上传的PDF文件
        pdf_content = await file.read()
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")
        
        # 提取所有页面的文本
        all_text = []
        total_pages = len(pdf_document)
        
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            
            # 将页面转换为图像（和test.py一样）
            mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放提高清晰度
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # 保存临时图像文件
            temp_img_path = str(temp_dir / f"temp_page_{page_num + 1}.png")
            with open(temp_img_path, "wb") as f:
                f.write(img_data)
            
            # 对图像执行OCR（使用predict方法）
            result = ocr.predict(temp_img_path)
            
            # 提取文本（从result对象中获取rec_texts）
            for res in result:
                # res本身就是字典类型，直接访问
                if 'rec_texts' in res:
                    rec_texts = res['rec_texts']
                    if rec_texts:
                        page_text = "\n".join(rec_texts)
                        all_text.append(page_text)
                # 或者通过json属性访问
                elif hasattr(res, 'json') and res.json:
                    json_data = res.json
                    if isinstance(json_data, list):
                        # 从json列表中提取rec_text字段
                        texts = [item.get('rec_text', '') for item in json_data if isinstance(item, dict)]
                        if texts:
                            page_text = "\n".join(texts)
                            all_text.append(page_text)
        
        pdf_document.close()
        
        return {
            "success": True,
            "filename": file.filename,
            "pages": total_pages,
            "content": "\n\n".join(all_text)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        # 清理临时目录
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


# 批量解析端点：支持一次上传多个PDF进行解析与入库
@router.post("/parse/batch", response_model=ResumeParseBatchResponse)
async def parse_resume_batch(files: List[UploadFile] = File(...)):
    """批量解析PDF简历（OCR + LLM），逐个写入SQLite与向量库，返回每个文件的处理结果。

    表单字段名为 `files`，可重复添加多个文件。
    """
    results: List[ResumeParseItemResult] = []

    for file in files:
        if not file.filename.endswith('.pdf'):
            results.append(ResumeParseItemResult(filename=file.filename, success=False, error="仅支持PDF格式文件"))
            continue

        session_id = uuid.uuid4().hex[:8]
        temp_dir = TEMP_BASE_DIR / session_id
        temp_dir.mkdir(exist_ok=True)

        try:
            pdf_content = await file.read()
            pdf_document = fitz.open(stream=pdf_content, filetype="pdf")

            all_text_parts = []
            total_pages = len(pdf_document)

            for page_num in range(total_pages):
                page = pdf_document[page_num]
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")

                temp_img_path = str(temp_dir / f"temp_page_{page_num + 1}.png")
                with open(temp_img_path, "wb") as f:
                    f.write(img_data)

                # OCR
                result = ocr.predict(temp_img_path)
                page_text = []
                for res in result:
                    if isinstance(res, dict) and 'rec_texts' in res:
                        texts = res.get('rec_texts') or []
                        if texts:
                            page_text.extend(texts)
                    elif hasattr(res, 'json') and res.json:
                        data = res.json
                        if isinstance(data, list):
                            page_text.extend([item.get('rec_text', '') for item in data if isinstance(item, dict)])

                if page_text:
                    all_text_parts.append("\n".join([t for t in page_text if t]))

            pdf_document.close()

            raw_text = "\n\n".join(all_text_parts)
            metadata = await resume_parser.parse_resume_content(raw_text)

            # 建表与入库
            Base.metadata.create_all(bind=engine)
            db = SessionLocal()
            try:
                resume_row = create_resume(
                    db,
                    filename=file.filename,
                    raw_content=raw_text,
                    metadata_json=metadata.model_dump_json(),
                )

                # 写入向量库
                doc_id = vector_store.add_resume(
                    resume_id=resume_row.id,
                    raw_content=raw_text,
                    metadata=metadata.model_dump(),
                )
                update_resume(db, resume_row.id, {"vector_id": doc_id})
            finally:
                db.close()

            results.append(ResumeParseItemResult(
                filename=file.filename,
                success=True,
                pages=total_pages,
                raw_content=raw_text,
                metadata=metadata
            ))
        except Exception as e:
            results.append(ResumeParseItemResult(filename=file.filename, success=False, error=str(e)))
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count
    return ResumeParseBatchResponse(results=results, success_count=success_count, fail_count=fail_count)


# 新增API端点
@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)):
    """解析PDF简历并提取结构化信息（OCR + LLM）"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="仅支持PDF格式文件")

    session_id = uuid.uuid4().hex[:8]
    temp_dir = TEMP_BASE_DIR / session_id
    temp_dir.mkdir(exist_ok=True)

    try:
        pdf_content = await file.read()
        pdf_document = fitz.open(stream=pdf_content, filetype="pdf")

        all_text_parts = []
        total_pages = len(pdf_document)

        for page_num in range(total_pages):
            page = pdf_document[page_num]
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")

            temp_img_path = str(temp_dir / f"temp_page_{page_num + 1}.png")
            with open(temp_img_path, "wb") as f:
                f.write(img_data)

            # 兼容PaddleOCR高版本predict返回结果
            result = ocr.predict(temp_img_path)
            page_text = []
            for res in result:
                if isinstance(res, dict) and 'rec_texts' in res:
                    texts = res.get('rec_texts') or []
                    if texts:
                        page_text.extend(texts)
                elif hasattr(res, 'json') and res.json:
                    data = res.json
                    if isinstance(data, list):
                        page_text.extend([item.get('rec_text', '') for item in data if isinstance(item, dict)])

            if page_text:
                all_text_parts.append("\n".join([t for t in page_text if t]))

        pdf_document.close()

        raw_text = "\n\n".join(all_text_parts)
        metadata = await resume_parser.parse_resume_content(raw_text)

        # === Step 3：写入SQLite并建立表（若首次运行） ===
        # 创建表（幂等）
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            # 先写入SQLite，拿到自增ID
            resume_row = create_resume(
                db,
                filename=file.filename,
                raw_content=raw_text,
                metadata_json=metadata.model_dump_json(),
            )

            # 写入向量库，使用 resume_{id} 作为向量ID
            doc_id = vector_store.add_resume(
                resume_id=resume_row.id,
                raw_content=raw_text,
                metadata=metadata.model_dump(),
            )

            # 回写 vector_id 至 SQLite（可用于排错与一致性校验）
            update_resume(db, resume_row.id, {"vector_id": doc_id})
        finally:
            db.close()

        return ResumeParseResponse(
            success=True,
            filename=file.filename,
            pages=total_pages,
            raw_content=raw_text,
            metadata=metadata
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)