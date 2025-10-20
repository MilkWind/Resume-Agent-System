"""LLM服务封装 - Gemini集成"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from app.utils.config import get_settings
from app.model.resume import ResumeMetadata
from app.prompts.resume_extraction import RESUME_EXTRACTION_PROMPT

class LLMService:
    """LLM服务类"""
    
    def __init__(self):
        settings = get_settings()
        
        # 初始化Gemini模型
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=settings.TEMPERATURE,
            max_output_tokens=settings.MAX_TOKENS
        )
        
        # 初始化输出解析器（自动将LLM输出转为Pydantic模型）
        self.parser = PydanticOutputParser(pydantic_object=ResumeMetadata)
        
        # 创建提示词模板
        self.prompt_template = PromptTemplate(
            template=RESUME_EXTRACTION_PROMPT + "\n\n{format_instructions}",
            input_variables=["resume_text"],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            }
        )
        
        # 构建处理链
        self.chain = self.prompt_template | self.llm | self.parser
    
    async def extract_resume_metadata(self, resume_text: str) -> ResumeMetadata:
        """提取简历结构化信息"""
        try:
            # 调用LLM链处理
            result = await self.chain.ainvoke({"resume_text": resume_text})
            return result
        except Exception as e:
            print(f" LLM提取失败: {e}")
            # 返回默认值
            return ResumeMetadata(
                name="未知",
                skills=[],
                domain="未知",
                education="未知",
                work_years=0
            )

# 创建全局单例
llm_service = LLMService()