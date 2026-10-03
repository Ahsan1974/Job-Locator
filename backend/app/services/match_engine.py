"""Resume ↔ job matching using skill overlap + TF-IDF cosine (local)."""

from __future__ import annotations

import math
import re
from collections import Counter

from app.domain.skills import extract_skills


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.]{1,}", (text or "").lower())


def _tfidf_cosine(a: str, b: str) -> float:
    ta, tb = _tokenize(a), _tokenize(b)
    if not ta or not tb:
        return 0.0
    ca, cb = Counter(ta), Counter(tb)
    vocab = set(ca) | set(cb)
    # simple tf weights
    va = [ca.get(t, 0) for t in vocab]
    vb = [cb.get(t, 0) for t in vocab]
    dot = sum(x * y for x, y in zip(va, vb))
    na = math.sqrt(sum(x * x for x in va))
    nb = math.sqrt(sum(y * y for y in vb))
    if na == 0 or nb == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (na * nb)))


class ResumeMatchEngine:
    def score(self, resume_text: str, job_text: str, resume_skills: list[str] | None = None) -> dict:
        r_skills = resume_skills or extract_skills(resume_text)
        j_skills = extract_skills(job_text)
        r_set = {s.lower() for s in r_skills}
        j_set = {s.lower() for s in j_skills}
        matching = sorted({s for s in j_skills if s.lower() in r_set}, key=str.lower)
        missing = sorted({s for s in j_skills if s.lower() not in r_set}, key=str.lower)

        skill_match = (len(matching) / len(j_skills) * 100) if j_skills else 55.0
        semantic = _tfidf_cosine(resume_text, job_text) * 100
        tech_match = skill_match
        exp_match = self._experience_match(resume_text, job_text)
        edu_match = 70.0 if re.search(r"\b(bachelor|master|b\.?s\.?|m\.?s\.?|degree)\b", resume_text, re.I) else 50.0
        ats = min(100.0, skill_match * 0.5 + semantic * 0.3 + (20 if len(resume_text) > 400 else 5))

        overall = round(
            skill_match * 0.35
            + tech_match * 0.2
            + exp_match * 0.2
            + edu_match * 0.1
            + semantic * 0.15,
            1,
        )

        strengths = matching[:8] or ["Java fundamentals present in profile"]
        weaknesses = missing[:8] or []
        missing_keywords = missing[:12]

        return {
            "overall": round(overall, 1),
            "skill_match": round(skill_match, 1),
            "experience_match": round(exp_match, 1),
            "education_match": round(edu_match, 1),
            "technology_match": round(tech_match, 1),
            "ats_score": round(ats, 1),
            "missing_skills": missing,
            "missing_keywords": missing_keywords,
            "strengths": [f"Strong overlap on {s}" for s in strengths[:5]]
            if matching
            else ["Solid Java baseline"],
            "weaknesses": [f"Missing {s}" for s in weaknesses[:5]] if weaknesses else [],
            "matching_skills": matching,
        }

    def _experience_match(self, resume: str, job: str) -> float:
        def years(text: str) -> int | None:
            m = re.search(r"(\d+)\+?\s*years?", text, re.I)
            return int(m.group(1)) if m else None

        ry, jy = years(resume), years(job)
        if ry is None or jy is None:
            return 65.0
        if ry >= jy:
            return 95.0
        gap = jy - ry
        return max(30.0, 90.0 - gap * 12)
