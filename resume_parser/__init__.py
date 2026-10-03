"""Phase 2 stub — resume parsing pipeline."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ParsedResume:
    skills: list[str]
    technologies: list[str]
    experience_years: int | None
    education: list[dict]
    projects: list[dict]
    certifications: list[str]
    languages: list[str]
    raw_text: str


class ResumeParser:
    """Parse PDF/DOCX resumes into structured data (Phase 2)."""

    supported_types = {".pdf", ".docx"}

    def parse(self, path: Path) -> ParsedResume:
        raise NotImplementedError("Resume parsing lands in Phase 2")
