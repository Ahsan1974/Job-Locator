"""Skill gap roadmap generation."""

from __future__ import annotations

from app.domain.skills import SKILL_LEARNING, extract_skills


class SkillGapEngine:
    def analyze(self, resume_text: str, job_text: str, resume_skills: list[str] | None = None) -> list[dict]:
        have = {s.lower() for s in (resume_skills or extract_skills(resume_text))}
        need = extract_skills(job_text)
        missing = [s for s in need if s.lower() not in have]
        results: list[dict] = []
        for skill in missing:
            meta = SKILL_LEARNING.get(
                skill,
                {
                    "hours": 30,
                    "priority": "medium",
                    "courses": [
                        {
                            "title": f"Learn {skill}",
                            "url": f"https://www.google.com/search?q={skill}+tutorial",
                            "provider": "Web",
                        }
                    ],
                    "docs": [{"title": f"{skill} docs", "url": f"https://www.google.com/search?q={skill}+documentation"}],
                    "projects": [f"Build a small demo using {skill} with Spring Boot"],
                    "improvement": 4,
                },
            )
            results.append(
                {
                    "skill": skill,
                    "priority": meta["priority"],
                    "learning_hours": meta["hours"],
                    "courses": meta["courses"],
                    "docs": meta["docs"],
                    "projects": meta["projects"],
                    "match_improvement": meta["improvement"],
                }
            )
        priority_rank = {"high": 0, "medium": 1, "low": 2}
        results.sort(key=lambda x: (priority_rank.get(x["priority"], 9), -x["match_improvement"]))
        return results
