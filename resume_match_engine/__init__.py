"""Phase 2 stub — embedding-based resume ↔ job matching."""


class ResumeMatchEngine:
    """Compute 0–100 match scores using embeddings (Phase 2)."""

    def score(self, resume_text: str, job_text: str) -> dict:
        raise NotImplementedError("Resume match engine lands in Phase 2")
