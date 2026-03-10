"""JD解析服务：LLM解析 + 生成检索query文本"""

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.utils.config import get_settings
from app.model.job_requirement import JDRequirement
from app.prompts.jd_extraction import JD_EXTRACTION_PROMPT, JD_NORMALIZE_PROMPT
from app.services.embedding_service import EmbeddingService


class JDParserService:
    def __init__(self) -> None:
        s = get_settings()
        self.llm = ChatOpenAI(
            model=s.SILICONFLOW_CHAT_MODEL,
            api_key=s.SILICONFLOW_API_KEY,
            base_url=s.SILICONFLOW_BASE_URL,
            temperature=s.SILICONFLOW_TEMPERATURE,
            max_tokens=s.SILICONFLOW_MAX_TOKENS,
        )
        # 结构化解析器
        self.parser = PydanticOutputParser(pydantic_object=JDRequirement)

        # 阶段1：归一化要点
        self.normalize_prompt = PromptTemplate(
            template=JD_NORMALIZE_PROMPT,
            input_variables=["jd_text"],
        )

        # 阶段2：严格结构化提取
        self.extract_prompt = PromptTemplate(
            template=JD_EXTRACTION_PROMPT + "\n\n{format_instructions}",
            input_variables=["jd_text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )

        self.embedding = EmbeddingService()

    async def parse(self, jd_text: str) -> JDRequirement:
        # 第一阶段：归一化要点
        normalized = await (self.normalize_prompt | self.llm).ainvoke({"jd_text": jd_text})
        norm_text = getattr(normalized, "content", None) or str(normalized)

        # 第二阶段：结构化提取
        extracted = await (self.extract_prompt | self.llm).ainvoke({"jd_text": norm_text})
        raw = getattr(extracted, "content", None) or str(extracted)

        # 轻量清洗：去除可能的代码块围栏，并尝试直接用解析器解析
        raw_clean = raw.strip()
        if raw_clean.startswith("```"):
            raw_clean = raw_clean.strip("`\n ")
        try:
            return self.parser.parse(raw_clean)
        except Exception:
            # 兜底：提取第一段大括号 JSON
            import re
            m = re.search(r"\{[\s\S]*\}", raw_clean)
            if m:
                return self.parser.parse(m.group(0))
            raise

    def build_query_text(self, jd: JDRequirement) -> str:
        # 将关键字段拼接为检索友好的文本（把重要筛选条件拼成一段文本，便于向量检索）
        parts = []
        if jd.title:
            parts.append(jd.title)
        if jd.skills_required:
            parts.append("必须技能:" + ",".join(jd.skills_required))
        if jd.skills_nice:
            parts.append("加分技能:" + ",".join(jd.skills_nice))
        if jd.domain:
            parts.append(jd.domain)
        if jd.min_education:
            parts.append("最低学历:" + jd.min_education)
        if jd.min_work_years:
            parts.append(f"年限>={jd.min_work_years}")
        if jd.locations:
            parts.append("地点:" + ",".join(jd.locations))
        if jd.salary:
            parts.append("薪资:" + jd.salary)
        if jd.description:
            parts.append("摘要:" + jd.description)
        return " \n".join(parts)

    def embed_query(self, query_text: str):
        return self.embedding.encode_text(query_text)


jd_parser = JDParserService()


