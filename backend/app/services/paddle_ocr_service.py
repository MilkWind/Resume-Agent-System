"""PaddleOCR API 服务 - 基于 PaddleOCR-CL-1.5 的异步解析"""

import asyncio
import json
from pathlib import Path
from typing import Optional

import httpx

from app.utils.config import get_settings

JOB_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
MODEL = "PaddleOCR-CL-1.5"
POLL_INTERVAL = 5
POLL_TIMEOUT = 600  # 10 minutes max


class PaddleOCRServiceError(Exception):
    """PaddleOCR API 异常"""
    pass


class PaddleOCRService:
    """PaddleOCR API 异步服务"""

    def __init__(self):
        settings = get_settings()
        self.token: str = settings.PADDLEOCR_TOKEN or ""
        self.job_url: str = settings.PADDLEOCR_JOB_URL or JOB_URL
        self.model: str = settings.PADDLEOCR_MODEL or MODEL

    def _headers(self) -> dict:
        return {
            "Authorization": f"bearer {self.token}",
        }

    async def extract_text_from_pdf(self, pdf_path: Path) -> tuple[str, int]:
        """
        从 PDF 文件提取文本（异步）

        Args:
            pdf_path: 本地 PDF 文件路径

        Returns:
            (extracted_text, total_pages)

        Raises:
            PaddleOCRServiceError: API 调用失败或任务失败
        """
        if not self.token:
            raise PaddleOCRServiceError("PADDLEOCR_TOKEN 未配置，请在 .env 中设置")

        if not pdf_path.exists():
            raise PaddleOCRServiceError(f"文件不存在: {pdf_path}")

        optional_payload = {
            "useDocOrientationClassify": False,
            "useDocUnwarping": False,
            "useChartRecognition": False,
        }

        data = {
            "model": self.model,
            "optionalPayload": json.dumps(optional_payload),
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            # 1. 提交任务
            with open(pdf_path, "rb") as f:
                files = {"file": (pdf_path.name, f, "application/pdf")}
                job_response = await client.post(
                    self.job_url,
                    headers=self._headers(),
                    data=data,
                    files=files,
                )

            if job_response.status_code != 200:
                raise PaddleOCRServiceError(
                    f"提交任务失败: {job_response.status_code} - {job_response.text}"
                )

            job_data = job_response.json()
            job_id = job_data.get("data", {}).get("jobId")
            if not job_id:
                raise PaddleOCRServiceError(f"响应中缺少 jobId: {job_data}")

            # 2. 轮询任务状态
            jsonl_url = await self._poll_job(client, job_id)

            if not jsonl_url:
                raise PaddleOCRServiceError("任务未返回结果 URL")

            # 3. 下载并解析 JSONL 结果
            text_parts, total_pages = await self._fetch_and_parse_jsonl(client, jsonl_url)
            return "\n\n".join(text_parts), total_pages

    async def _poll_job(self, client: httpx.AsyncClient, job_id: str) -> Optional[str]:
        """异步轮询任务状态，返回结果 JSONL URL"""
        url = f"{self.job_url.rstrip('/')}/{job_id}"
        elapsed = 0

        while elapsed < POLL_TIMEOUT:
            resp = await client.get(url, headers=self._headers())
            if resp.status_code != 200:
                raise PaddleOCRServiceError(f"查询任务失败: {resp.status_code} - {resp.text}")

            data = resp.json().get("data", {})
            state = data.get("state", "")

            if state == "done":
                result_urls = data.get("resultUrl", {})
                return result_urls.get("jsonUrl") or result_urls.get("jsonlUrl")
            elif state == "failed":
                error_msg = data.get("errorMsg", "未知错误")
                raise PaddleOCRServiceError(f"OCR 任务失败: {error_msg}")

            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

        raise PaddleOCRServiceError(f"任务超时（{POLL_TIMEOUT}s）")

    async def _fetch_and_parse_jsonl(
        self, client: httpx.AsyncClient, jsonl_url: str
    ) -> tuple[list[str], int]:
        """下载 JSONL 并解析出每页的 markdown 文本"""
        resp = await client.get(jsonl_url)
        resp.raise_for_status()

        lines = resp.text.strip().split("\n")
        text_parts: list[str] = []
        page_num = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                result = obj.get("result", {})
                layout_results = result.get("layoutParsingResults", [])
                for res in layout_results:
                    markdown = res.get("markdown", {})
                    text = markdown.get("text", "")
                    if text:
                        text_parts.append(text)
                    page_num += 1
            except (json.JSONDecodeError, KeyError):
                continue

        return text_parts, max(page_num, 1)


paddle_ocr_service = PaddleOCRService()
