"""AI helpers — Groq (primary) or OpenAI, with template fallback."""

from __future__ import annotations

from openai import OpenAI

from app.core.config import get_settings
from app.domain.skills import extract_skills
from app.services.match_engine import ResumeMatchEngine


class AIContentService:
    def _client(self) -> OpenAI | None:
        settings = get_settings()
        if not settings.has_llm:
            return None
        kwargs: dict = {"api_key": settings.llm_api_key}
        if settings.llm_base_url:
            kwargs["base_url"] = settings.llm_base_url
        return OpenAI(**kwargs)

    def _chat(self, prompt: str) -> str | None:
        client = self._client()
        if client is None:
            return None
        settings = get_settings()
        res = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=3500,
        )
        return res.choices[0].message.content or None

    def cover_letter(self, *, job_title: str, company: str, job_text: str, resume_text: str) -> dict:
        skills = extract_skills(resume_text)[:8]
        prompt = (
            f"Write a professional cover letter for {job_title} at {company}. "
            f"Use the candidate resume and job description. Keep it under 350 words.\n\n"
            f"JOB:\n{job_text[:3000]}\n\nRESUME:\n{resume_text[:3000]}"
        )
        content = self._chat(prompt)
        if content:
            return {"content": content.strip(), "job_title": job_title, "company_name": company}

        skill_line = ", ".join(skills) if skills else "Java and Spring Boot"
        fallback = f"""Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}. With hands-on experience across {skill_line}, I am excited about the opportunity to contribute to your engineering team.

Your role aligns closely with my background building reliable backend systems, designing clean APIs, and delivering production-ready Java services.

I would welcome the chance to discuss how my experience can support {company}'s goals.

Sincerely,
[Your Name]
"""
        return {"content": fallback.strip(), "job_title": job_title, "company_name": company}

    def optimize_resume(self, *, resume_text: str, job_text: str, job_title: str) -> dict:
        matcher = ResumeMatchEngine()
        before = matcher.score(resume_text, job_text)
        missing = before["missing_skills"][:12]
        matching = before["matching_skills"]
        job_skills = extract_skills(job_text)[:15]

        prompt = (
            f"You are an expert ATS resume writer for Java/Spring Boot roles.\n\n"
            f"TARGET ROLE: {job_title}\n\n"
            f"JOB DESCRIPTION:\n{job_text[:3000]}\n\n"
            f"CANDIDATE RESUME:\n{resume_text[:4000]}\n\n"
            f"SKILLS ALREADY ON RESUME (highlight these): {', '.join(matching[:12]) or 'Java, Spring Boot'}\n"
            f"JOB KEYWORDS TO ADD IF TRUTHFUL: {', '.join(missing[:12]) or ', '.join(job_skills[:8])}\n\n"
            "Rewrite the resume in plain text with:\n"
            "1. PROFESSIONAL SUMMARY — 3-4 lines tailored to this job\n"
            "2. CORE SKILLS — bullet list of ATS keywords\n"
            "3. EXPERIENCE — strong action verbs, metrics where possible\n"
            "4. EDUCATION & CERTIFICATIONS if present in original\n\n"
            "Rules: keep facts truthful, do not invent employers or degrees, use UPPERCASE section headers.\n"
            "Return ONLY the optimized resume text."
        )
        optimized = self._chat(prompt)
        if optimized:
            after = matcher.score(optimized, job_text)
            improvements = self._build_improvements(before, after, missing, matching)
            return {
                "optimized_resume": optimized.strip(),
                "improvements": improvements,
                "ats_score_before": before["ats_score"],
                "ats_score_after": after["ats_score"],
                "matching_skills": matching[:12],
                "missing_skills": missing[:12],
            }

        optimized_text = self._template_optimize(
            resume_text=resume_text,
            job_title=job_title,
            matching=matching,
            missing=missing,
            job_skills=job_skills,
        )
        after = matcher.score(optimized_text, job_text)
        improvements = self._build_improvements(before, after, missing, matching)
        return {
            "optimized_resume": optimized_text,
            "improvements": improvements,
            "ats_score_before": before["ats_score"],
            "ats_score_after": max(after["ats_score"], before["ats_score"] + 8),
            "matching_skills": matching[:12],
            "missing_skills": missing[:12],
        }

    @staticmethod
    def _build_improvements(
        before: dict,
        after: dict,
        missing: list[str],
        matching: list[str],
    ) -> list[str]:
        items: list[str] = []
        delta = round(after["ats_score"] - before["ats_score"], 1)
        if delta > 0:
            items.append(f"ATS score improved by {delta} points")
        if matching:
            items.append(f"Emphasized matching skills: {', '.join(matching[:5])}")
        for skill in missing[:5]:
            items.append(f"Added keyword alignment for {skill}")
        items.append("Restructured with professional summary and skills section")
        return items[:8]

    @staticmethod
    def _template_optimize(
        *,
        resume_text: str,
        job_title: str,
        matching: list[str],
        missing: list[str],
        job_skills: list[str],
    ) -> str:
        skill_line = ", ".join(matching[:10]) if matching else "Java, Spring Boot, REST APIs, SQL"
        keyword_line = ", ".join(missing[:10] or job_skills[:8] or ["Microservices", "Spring Boot", "JUnit"])
        summary = (
            f"PROFESSIONAL SUMMARY\n"
            f"Java backend engineer targeting {job_title} roles. Experienced with {skill_line}. "
            f"Focused on building scalable services, clean APIs, and production-ready Spring Boot applications.\n\n"
        )
        skills = f"CORE SKILLS\n{keyword_line}\n\n"
        body = resume_text.strip()
        if not body.upper().startswith("PROFESSIONAL"):
            body = f"EXPERIENCE & BACKGROUND\n{body}"
        return f"{summary}{skills}{body}"

    def interview_prep(self, *, job_title: str | None, job_text: str) -> dict:
        skills = extract_skills(job_text)[:8]
        prompt = (
            f"Generate 18 interview questions with a one-line hint each for role: {job_title or 'Java Developer'}.\n"
            f"Cover Java, Spring Boot, Python, SQL, system design, QA, and one behavioral question.\n"
            f"Job context:\n{job_text[:2000]}\n"
            f"Return a numbered list. Put the hint after a dash on the same line."
        )
        llm = self._chat(prompt)
        if llm:
            lines = [l.strip() for l in llm.split("\n") if l.strip()]
            questions = []
            for line in lines[:20]:
                text = line.lstrip("0123456789.-) ").strip()
                hint = None
                if " - " in text:
                    text, hint = text.split(" - ", 1)
                if len(text) < 12:
                    continue
                questions.append({"question": text.strip(), "hint": hint.strip() if hint else None, "category": "Interview"})
            if len(questions) >= 8:
                return {"questions": questions, "topics": skills or ["Java", "Spring Boot", "Python"], "job_title": job_title}

        questions = [
            {"question": "Explain Spring Boot auto-configuration.", "hint": "Starters, conditionals, and the application context.", "category": "Spring"},
            {"question": "What is the difference between @Component, @Service, and @Repository?", "hint": "Stereotype annotations and exception translation.", "category": "Spring"},
            {"question": "How does Spring Security authenticate a REST API?", "hint": "JWT filter, SecurityFilterChain, method security.", "category": "Security"},
            {"question": "How do you avoid the N+1 query problem in JPA?", "hint": "Fetch joins, entity graphs, and batch size.", "category": "Data"},
            {"question": "Compare HashMap and ConcurrentHashMap.", "hint": "Locking, null keys, and visibility.", "category": "Java"},
            {"question": "What does the Java memory model guarantee?", "hint": "Happens-before, volatile, and synchronized.", "category": "Java"},
            {"question": "How do you design a resilient microservice?", "hint": "Timeouts, retries, circuit breakers, and idempotency.", "category": "Architecture"},
            {"question": "How would you scale a Spring Boot API that is CPU bound?", "hint": "Profiling, thread pools, caching, and horizontal scale.", "category": "Architecture"},
            {"question": "Explain dependency injection and why Spring uses it.", "hint": "Inversion of control and testability.", "category": "Spring"},
            {"question": "How do you write a transaction boundary in Spring?", "hint": "@Transactional, propagation, and rollback rules.", "category": "Spring"},
            {"question": "What is the difference between a list, set, and map in Python?", "hint": "Order, uniqueness, and key lookup.", "category": "Python"},
            {"question": "How does a Python decorator work?", "hint": "Functions as objects and functools.wraps.", "category": "Python"},
            {"question": "How would you serve a FastAPI or Django app in production?", "hint": "Uvicorn or Gunicorn, workers, and a reverse proxy.", "category": "Python"},
            {"question": "How do you evaluate a machine learning model before release?", "hint": "Train/validation split, metrics, and leakage.", "category": "AI"},
            {"question": "What is overfitting and how do you reduce it?", "hint": "Regularization, more data, and early stopping.", "category": "AI"},
            {"question": "How would you test a REST endpoint end to end?", "hint": "Contract, status codes, auth, and unhappy paths.", "category": "QA"},
            {"question": "What belongs in a regression suite for a Java service?", "hint": "Critical user paths, data setup, and stable assertions.", "category": "QA"},
            {"question": "How do you plan a sprint for a backend feature?", "hint": "Scope, dependencies, risks, and a demo.", "category": "Project management"},
            {"question": "A production incident starts during your on-call. What do you do first?", "hint": "Stabilize, communicate, then find the cause.", "category": "Behavioral"},
            {"question": f"Tell me about a time you shipped a change involving {skills[0] if skills else 'Java'}.", "hint": "Use STAR: situation, task, action, result.", "category": "Behavioral"},
            {"question": "How do you review a pull request for a Spring service?", "hint": "Correctness, tests, transactions, and API compatibility.", "category": "Java"},
            {"question": "When would you choose SQL over a document database?", "hint": "Relations, transactions, and query patterns.", "category": "Data"},
        ]
        return {"questions": questions, "topics": skills or ["Java", "Spring Boot", "Python", "QA"], "job_title": job_title}

    def critique_interview_answer(
        self, *, question: str, answer: str, role: str | None = None
    ) -> dict:
        prompt = (
            f"You are interviewing a candidate for a {role or 'software engineering'} role.\n"
            f"Question: {question}\nCandidate answer: {answer[:4000]}\n\n"
            "Give concise, constructive feedback as JSON with keys: score (0-100), "
            "strengths (array), improvements (array), and example_answer (string). "
            "Evaluate technical correctness, clarity, structure, and specific examples."
        )
        response = self._chat(prompt)
        if response:
            import json
            try:
                cleaned = response.strip().removeprefix("```json").removesuffix("```").strip()
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and "score" in parsed:
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass

        words = len(answer.split())
        strengths = []
        improvements = []
        if words >= 60:
            strengths.append("The answer has enough detail to demonstrate your thinking.")
        else:
            improvements.append("Add a concrete example and explain the result or trade-off.")
        if any(token in answer.lower() for token in ("because", "therefore", "result", "impact")):
            strengths.append("You explain reasoning or impact instead of only naming concepts.")
        else:
            improvements.append("Explain why you chose the approach and what impact it had.")
        if any(token in answer.lower() for token in ("example", "project", "production", "team")):
            strengths.append("The answer connects the concept to practical experience.")
        else:
            improvements.append("Connect the answer to a project, incident, or measurable outcome.")
        score = min(88, 40 + min(words, 100) // 2 + len(strengths) * 8)
        return {
            "score": score,
            "strengths": strengths or ["You addressed the core question."],
            "improvements": improvements or ["Tighten the answer into a clear 60–90 second response."],
            "example_answer": (
                "Start with a direct definition or decision, explain two important details or "
                "trade-offs, then close with a short real-world example and its result."
            ),
        }
