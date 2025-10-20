"""简历解析服务 - 整合OCR和LLM"""

from app.services.llm_service import llm_service
from app.model.resume import ResumeMetadata

class ResumeParserService:
    """简历解析服务"""
    
    async def parse_resume_content(self, raw_text: str) -> ResumeMetadata:
        """
        解析简历内容为结构化信息
        
        Args:
            raw_text: OCR提取的原始文本
            
        Returns:
            ResumeMetadata: 结构化的简历元数据
        """
        # 调用LLM服务提取结构化信息
        metadata = await llm_service.extract_resume_metadata(raw_text)
        return metadata

# 创建全局单例
resume_parser = ResumeParserService()