"""多维度二次评分（技能/行业/薪资/学历/地点/个性标签）

输入：
- jd: dict（来自 JDRequirement.model_dump()）
- rows: List[Dict]，元素包含至少：
  { id, filename, metadata_json 或 metadata(dict), similarity, score(第一轮), explain(第一轮) ... }

输出：
- 返回在原元素基础上新增：
  score2: float
  explain2: {skills, domain, salary, education, location, tags}
并按 score2 降序排序。
"""
from __future__ import annotations
from typing import List, Dict, Any
import json
import math

# 学历映射
_EDU_RANK = {"专科": 1, "大专": 1, "本科": 2, "硕士": 3, "研究生": 3, "博士": 4}

def _edu_rank(edu: str) -> int:
    return _EDU_RANK.get((edu or "").strip(), 0)

# 解析薪资区间，如 "20-30K"、"30K"、"面议"
# 返回 (min_k, max_k)，单位K；无法解析返回 (None, None)
import re
_SALARY_RE = re.compile(r"(\d+)(?:\s*[-~到至]\s*(\d+))?\s*[kK]?")

def _parse_salary_to_k_range(s: str):
    if not s:
        return (None, None)
    s = s.strip()
    if "面议" in s:
        return (None, None)
    m = _SALARY_RE.search(s)
    if not m:
        return (None, None)
    a = int(m.group(1))
    b = m.group(2)
    if b is None:
        return (a, a)
    return (min(a, int(b)), max(a, int(b)))

# 文本相等或包含的简单行业匹配

def _domain_match_score(cand: str, need: str) -> float:
    c = (cand or "").strip().lower()
    n = (need or "").strip().lower()
    if not n:
        return 0.5  # 无要求给中性分
    if not c:
        return 0.0
    if c == n:
        return 1.0
    if c in n or n in c:
        return 0.7
    return 0.0

# 地点匹配：候选现居地与JD地点交集

def _location_match_score(cities: List[str], need_locs: List[str]) -> float:
    cset = set([x.strip().lower() for x in (cities or []) if x and str(x).strip()])
    nset = set([x.strip().lower() for x in (need_locs or []) if x and str(x).strip()])
    if not nset:
        return 0.5  # 无要求给中性分
    if not cset:
        return 0.0
    return 1.0 if cset & nset else 0.0

# 技能匹配：必须技能覆盖 + 加分技能命中（限制在[0,1]）

def _skills_match_score(cand_skills: List[str], req: List[str], nice: List[str]) -> float:
    cset = set([(s or "").strip().lower() for s in (cand_skills or []) if s and str(s).strip()])
    rset = set([(s or "").strip().lower() for s in (req or []) if s and str(s).strip()])
    nset = set([(s or "").strip().lower() for s in (nice or []) if s and str(s).strip()])
    cover = (len(cset & rset) / len(rset)) if rset else 1.0
    bonus = (len(cset & nset) / len(nset)) if nset else 0.0
    score = 0.8 * cover + 0.2 * bonus  # 技能维度内部加权
    return max(0.0, min(1.0, score))

# 薪资匹配：候选期望 vs JD 提供
# - 若JD无薪资要求 => 0.5
# - 若候选无期望 => 0.5
# - 若有区间：候选期望区间落在 JD 区间内 => 1；部分重叠 => 0.7；候选高于JD上限越多，分越低

def _salary_match_score(cand_salary: str, jd_salary: str) -> float:
    c = _parse_salary_to_k_range(cand_salary)
    j = _parse_salary_to_k_range(jd_salary)
    if j == (None, None):
        return 0.5
    if c == (None, None):
        return 0.5
    cmin, cmax = c
    jmin, jmax = j
    if cmin is None or cmax is None or jmin is None or jmax is None:
        return 0.5
    # 完全包含
    if cmin >= jmin and cmax <= jmax:
        return 1.0
    # 有交集
    if not (cmax < jmin or cmin > jmax):
        return 0.7
    # 候选高于JD上限：按超出比例衰减（>100%则0分）
    if cmin > jmax:
        over = cmin - jmax
        base = max(1, jmax)
        penalty = min(1.0, over / base)
        return max(0.0, 0.7 * (1 - penalty))
    # 候选远低于JD下限：也给一定分（可能可谈）
    return 0.6

# 个性标签匹配：JD若提供期望标签，命中比率；否则根据候选是否有标签给予轻微加分

def _tags_match_score(cand_tags: List[str], jd_tags: List[str]) -> float:
    cset = set([(s or "").strip().lower() for s in (cand_tags or []) if s and str(s).strip()])
    tset = set([(s or "").strip().lower() for s in (jd_tags or []) if s and str(s).strip()])
    if not tset:
        return 0.6 if cset else 0.5
    return len(cset & tset) / len(tset) if tset else 0.5

class MultiScoringEngine:
    """六维度评分：
    - 技能匹配度：35%
    - 行业领域匹配度：35%
    - 薪资匹配度：10%
    - 学历匹配度：10%
    - 地理位置匹配度：5%
    - 个性标签匹配度：5%
    """

    WEIGHTS = {
        "skills": 0.35,
        "domain": 0.35,
        "salary": 0.10,
        "education": 0.10,
        "location": 0.05,
        "tags": 0.05,
    }

    def score(self, jd: Dict[str, Any], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        req_skills = jd.get("skills_required") or []
        nice_skills = jd.get("skills_nice") or []
        jd_domain = jd.get("domain") or ""
        jd_salary = jd.get("salary") or ""
        jd_locations = jd.get("locations") or []
        jd_tags = jd.get("custom_tags") or []  # 若模型未来扩展支持
        jd_min_edu = jd.get("min_education") or None

        for row in rows:
            meta = json.loads(row.get("metadata_json")) if isinstance(row.get("metadata_json"), str) else (row.get("metadata") or {})

            # 候选信息
            cand_skills = meta.get("skills") or []
            cand_domain = meta.get("domain") or ""
            cand_salary = meta.get("expected_salary") or ""
            cand_edu = meta.get("education") or ""
            cand_locs = meta.get("current_location") or []
            cand_tags = meta.get("custom_tags") or []

            # 子分
            s_skills = _skills_match_score(cand_skills, req_skills, nice_skills)
            s_domain = _domain_match_score(cand_domain, jd_domain)
            s_salary = _salary_match_score(cand_salary, jd_salary)
            # 学历：达到最低要求给满分；低于则按等级比例
            if jd_min_edu:
                s_edu = 1.0 if _edu_rank(cand_edu) >= _edu_rank(jd_min_edu) else max(0.0, _edu_rank(cand_edu) / max(1, _edu_rank(jd_min_edu)))
            else:
                s_edu = 0.5  # 无要求给中性分
            s_loc = _location_match_score(cand_locs, jd_locations)
            s_tags = _tags_match_score(cand_tags, jd_tags)

            # 总分
            score2 = (
                self.WEIGHTS["skills"] * s_skills
                + self.WEIGHTS["domain"] * s_domain
                + self.WEIGHTS["salary"] * s_salary
                + self.WEIGHTS["education"] * s_edu
                + self.WEIGHTS["location"] * s_loc
                + self.WEIGHTS["tags"] * s_tags
            )

            results.append({
                **row,
                "score2": round(float(score2), 6),
                "explain2": {
                    "skills": round(s_skills, 4),
                    "domain": round(s_domain, 4),
                    "salary": round(s_salary, 4),
                    "education": round(s_edu, 4),
                    "location": round(s_loc, 4),
                    "tags": round(s_tags, 4),
                }
            })

        # 二次评分降序
        return sorted(results, key=lambda x: x["score2"], reverse=True)


multi_scoring_engine = MultiScoringEngine()
