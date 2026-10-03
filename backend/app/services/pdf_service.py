"""Generate resume PDF files."""

from fpdf import FPDF


def build_resume_pdf(*, title: str, resume_text: str, subtitle: str | None = None) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, _safe_text(title))
    if subtitle:
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 6, _safe_text(subtitle))
        pdf.set_text_color(0, 0, 0)
        pdf.ln(4)
    pdf.set_font("Helvetica", "", 10)
    for line in resume_text.splitlines():
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
        if line.isupper() and len(line) < 60:
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, _safe_text(line))
            pdf.set_font("Helvetica", "", 10)
        else:
            pdf.multi_cell(0, 5, _safe_text(line))
    return bytes(pdf.output())


def build_application_pack_pdf(
    *,
    candidate: str,
    job_title: str,
    company: str,
    match_score: float,
    resume_text: str,
    cover_letter: str,
    strengths: list[str],
    missing_skills: list[str],
) -> bytes:
    """Build one downloadable PDF containing score, tailored CV, and cover letter."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.multi_cell(0, 10, _safe_text("APPLICATION PACK"))
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 7, _safe_text(f"{candidate} | {job_title} at {company}"))
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(124, 92, 255)
    pdf.multi_cell(0, 12, _safe_text(f"{round(match_score)}% MATCH"))
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    if strengths:
        pdf.multi_cell(0, 6, _safe_text("Strengths: " + ", ".join(strengths[:5])))
    if missing_skills:
        pdf.multi_cell(0, 6, _safe_text("Keywords to prepare: " + ", ".join(missing_skills[:8])))

    _add_text_section(pdf, "TAILORED RESUME", resume_text, new_page=True)
    _add_text_section(pdf, "COVER LETTER", cover_letter, new_page=True)
    return bytes(pdf.output())


def _add_text_section(pdf: FPDF, heading: str, content: str, *, new_page: bool = False) -> None:
    if new_page:
        pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, _safe_text(heading))
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 10)
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            pdf.ln(3)
        elif line.isupper() and len(line) < 70:
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, _safe_text(line))
            pdf.set_font("Helvetica", "", 10)
        else:
            pdf.multi_cell(0, 5, _safe_text(line))


def _safe_text(value: str) -> str:
    return value.encode("latin-1", errors="replace").decode("latin-1")
