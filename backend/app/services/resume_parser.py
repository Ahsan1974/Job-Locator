"""Resume parsing — PDF/DOCX to structured text + skills (local, no Docker)."""

from __future__ import annotations

import re
from pathlib import Path

from app.domain.skills import extract_skills, dump_json


class ResumeParser:
    supported = {".pdf", ".docx", ".txt"}

    def parse_file(self, path: Path) -> dict:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            text = self._parse_pdf(path)
        elif suffix == ".docx":
            text = self._parse_docx(path)
        elif suffix == ".txt":
            text = path.read_text(encoding="utf-8", errors="ignore")
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        skills = extract_skills(text)
        years = self._years_of_experience(text)
        education = self._section(text, ("education", "academic"))
        projects = self._section(text, ("projects", "project experience"))
        certifications = self._section(text, ("certifications", "certificates"))
        return {
            "raw_text": text,
            "skills": skills,
            "technologies": skills,
            "experience_years": years,
            "education": education,
            "projects": projects,
            "certifications": certifications,
            "languages": self._languages(text),
            "parsed_json": dump_json(
                {
                    "skills": skills,
                    "experience_years": years,
                    "education": education,
                    "projects": projects,
                }
            ),
        }

    def _parse_pdf(self, path: Path) -> str:
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(path)
            parts = [page.get_text() for page in doc]
            doc.close()
            text = "\n".join(parts).strip()
            if text:
                return text
        except Exception:
            pass
        try:
            import pdfplumber

            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as exc:
            raise ValueError(f"Could not parse PDF: {exc}") from exc

    def _parse_docx(self, path: Path) -> str:
        from docx import Document

        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def _years_of_experience(self, text: str) -> int | None:
        patterns = [
            r"(\d+)\+?\s*\+?\s*years?\s+(?:of\s+)?experience",
            r"experience\s*[:\-]?\s*(\d+)\+?\s*years?",
        ]
        for p in patterns:
            m = re.search(p, text, re.I)
            if m:
                return int(m.group(1))
        return None

    def _section(self, text: str, headers: tuple[str, ...]) -> str:
        lower = text.lower()
        for h in headers:
            idx = lower.find(h)
            if idx >= 0:
                chunk = text[idx : idx + 800]
                return chunk.strip()
        return ""

    def _languages(self, text: str) -> list[str]:
        langs = ["English", "German", "French", "Spanish", "Arabic", "Urdu", "Hindi", "Dutch"]
        return [l for l in langs if re.search(rf"\b{l}\b", text, re.I)]
