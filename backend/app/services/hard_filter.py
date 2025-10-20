"""第二阶段：硬性条件过滤（学历/年限/技能）"""

from typing import List, Dict, Any
import json


def _edu_rank(edu: str) -> int:
    order = {"专科": 1, "大专": 1, "本科": 2, "硕士": 3, "研究生": 3, "博士": 4}
    return order.get(edu or "", 0)

class HardFilter:
    def filter(self, jd: Dict[str, Any], resume_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """入参：
        - jd: 字典（来自 JDRequirement.model_dump）
        - resume_rows: [{id, filename, metadata_json, similarity, ...}]
        返回：满足硬性要求的候选列表（宽松策略，避免全被过滤）
        """
        import math

        min_years = int(jd.get("min_work_years") or 0)
        min_edu = jd.get("min_education") or None
        # 统一必须技能为小写，去除首尾空格
        required_list = [
            (s.strip().lower()) for s in (jd.get("skills_required") or []) if s and str(s).strip()
        ]

        # 放宽：至少命中一半必须技能（向上取整），最少要求1个
        if required_list:
            min_required_match = max(1, math.ceil(len(required_list) * 0.5))
        else:
            min_required_match = 0

        required_set = set(required_list)

        filtered = []
        for row in resume_rows:
            meta = json.loads(row.get("metadata_json")) if isinstance(row.get("metadata_json"), str) else row.get("metadata")

            # 年限
            work_years = int(meta.get("work_years") or 0)
            if work_years < min_years:
                continue

            # 学历（包含式判断：支持“本科及以上”等）
            if min_edu and _edu_rank(meta.get("education")) < _edu_rank(min_edu):
                continue

            # 技能：至少命中N个必须技能（简历技能同样小写化）
            skills = set((s.strip().lower()) for s in (meta.get("skills") or []) if s and str(s).strip())
            if min_required_match > 0:
                hit = len(required_set & skills)
                if hit < min_required_match:
                    continue

            filtered.append(row)
        return filtered


hard_filter = HardFilter()


