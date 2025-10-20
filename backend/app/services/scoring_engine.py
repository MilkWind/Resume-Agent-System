"""第三阶段：综合评分（相似度/技能覆盖/年限/学历）"""

from typing import List, Dict, Any
import json


class ScoringEngine:
    def score(self, jd: Dict[str, Any], resume_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """返回带score的列表，并按score降序"""
        # 统一大小写与空白
        required_skills = set((s.strip().lower()) for s in (jd.get("skills_required") or []) if s and str(s).strip())
        nice_skills = set((s.strip().lower()) for s in (jd.get("skills_nice") or []) if s and str(s).strip())
        min_years = int(jd.get("min_work_years") or 0)

        results = []
        for row in resume_rows:
            meta = json.loads(row.get("metadata_json")) if isinstance(row.get("metadata_json"), str) else row.get("metadata")

            # 1) 相似度分（0~1）
            sim = float(row.get("similarity") or 0.0)

            # 2) 必须技能覆盖率（0~1）
            skills = set((s.strip().lower()) for s in (meta.get("skills") or []) if s and str(s).strip())
            cov = len(required_skills & skills) / len(required_skills) if required_skills else 1.0

            # 3) 加分技能命中（0~1）
            bonus = len(nice_skills & skills) / len(nice_skills) if nice_skills else 0.0

            # 4) 年限匹配度（>=要求给满1，否则按比例）
            years = int(meta.get("work_years") or 0)
            years_score = 1.0 if years >= min_years else (years / min_years if min_years > 0 else 1.0)

            # 简单加权（可调）
            score = 0.5 * sim + 0.3 * cov + 0.1 * bonus + 0.1 * years_score

            results.append({
                **row,
                "score": round(score, 6),
                "explain": {
                    "similarity": round(sim, 4),
                    "skills_cover": round(cov, 4),
                    "skills_bonus": round(bonus, 4),
                    "years_match": round(years_score, 4),
                }
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)


scoring_engine = ScoringEngine()


