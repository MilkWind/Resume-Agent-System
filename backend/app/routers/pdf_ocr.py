import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from app.model.resume import (
    ResumeExtractResponse,
    ResumeParseResponse,
    ResumeParseBatchResponse,
    ResumeParseItemResult,
)
from app.services.resume_parser import resume_parser
from app.services.paddle_ocr_service import paddle_ocr_service, PaddleOCRServiceError
from app.database.base import SessionLocal, Base, engine
from app.database.crud import create_resume, update_resume
from app.services.vector_store import vector_store

import tempfile

router = APIRouter(prefix="/api/resume", tags=["简历处理"])

TEMP_BASE_DIR = Path(tempfile.gettempdir()) / "resume_ocr_temp"
TEMP_BASE_DIR.mkdir(exist_ok=True)


def _save_upload_to_temp(file: UploadFile) -> tuple[Path, Path]:
    """创建临时目录并返回 PDF 保存路径与目录（调用方负责写入文件）"""
    session_id = uuid.uuid4().hex[:8]
    temp_dir = TEMP_BASE_DIR / session_id
    temp_dir.mkdir(exist_ok=True)
    safe_name = Path(file.filename or "upload.pdf").name
    temp_path = temp_dir / safe_name
    return temp_path, temp_dir


@router.post("/extract", response_model=ResumeExtractResponse)
async def extract_resume_info(file: UploadFile = File(...)):
    """提取 PDF 简历信息（使用 PaddleOCR-CL-1.5 API 异步解析）"""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")

    temp_path, temp_dir = _save_upload_to_temp(file)
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        raw_text, total_pages = await paddle_ocr_service.extract_text_from_pdf(temp_path)

        return ResumeExtractResponse(
            success=True,
            filename=file.filename,
            pages=total_pages,
            content=raw_text,
        )
    except PaddleOCRServiceError as e:
        raise HTTPException(status_code=502, detail=f"OCR 服务异常: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


@router.post("/parse/batch", response_model=ResumeParseBatchResponse)
async def parse_resume_batch(files: List[UploadFile] = File(...)):
    """批量解析 PDF 简历（PaddleOCR-CL-1.5 API + LLM），逐个写入 SQLite 与向量库"""
    results: List[ResumeParseItemResult] = []

    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            results.append(
                ResumeParseItemResult(filename=file.filename or "unknown", success=False, error="仅支持 PDF 格式文件")
            )
            continue

        temp_path, temp_dir = _save_upload_to_temp(file)
        try:
            with open(temp_path, "wb") as f:
                content = await file.read()
                f.write(content)

            raw_text, total_pages = await paddle_ocr_service.extract_text_from_pdf(temp_path)
            metadata = await resume_parser.parse_resume_content(raw_text)

            Base.metadata.create_all(bind=engine)
            db = SessionLocal()
            try:
                resume_row = create_resume(
                    db,
                    filename=file.filename,
                    raw_content=raw_text,
                    metadata_json=metadata.model_dump_json(),
                )
                doc_id = vector_store.add_resume(
                    resume_id=resume_row.id,
                    raw_content=raw_text,
                    metadata=metadata.model_dump(),
                )
                update_resume(db, resume_row.id, {"vector_id": doc_id})
            finally:
                db.close()

            results.append(
                ResumeParseItemResult(
                    filename=file.filename,
                    success=True,
                    pages=total_pages,
                    raw_content=raw_text,
                    metadata=metadata,
                )
            )
        except PaddleOCRServiceError as e:
            results.append(
                ResumeParseItemResult(filename=file.filename, success=False, error=f"OCR 服务异常: {str(e)}")
            )
        except Exception as e:
            results.append(
                ResumeParseItemResult(filename=file.filename, success=False, error=str(e))
            )
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

    success_count = sum(1 for r in results if r.success)
    fail_count = len(results) - success_count
    return ResumeParseBatchResponse(results=results, success_count=success_count, fail_count=fail_count)


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(file: UploadFile = File(...)):
    """解析 PDF 简历并提取结构化信息（PaddleOCR-CL-1.5 API + LLM）"""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 格式文件")

    temp_path, temp_dir = _save_upload_to_temp(file)
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        raw_text, total_pages = await paddle_ocr_service.extract_text_from_pdf(temp_path)
        metadata = await resume_parser.parse_resume_content(raw_text)

        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            resume_row = create_resume(
                db,
                filename=file.filename,
                raw_content=raw_text,
                metadata_json=metadata.model_dump_json(),
            )
            doc_id = vector_store.add_resume(
                resume_id=resume_row.id,
                raw_content=raw_text,
                metadata=metadata.model_dump(),
            )
            update_resume(db, resume_row.id, {"vector_id": doc_id})
        finally:
            db.close()

        return ResumeParseResponse(
            success=True,
            filename=file.filename,
            pages=total_pages,
            raw_content=raw_text,
            metadata=metadata,
        )
    except PaddleOCRServiceError as e:
        raise HTTPException(status_code=502, detail=f"OCR 服务异常: {str(e)}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
