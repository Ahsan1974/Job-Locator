"""Unit tests for Java job relevance filter."""

from app.domain.java_filter import (
    detect_experience_level,
    detect_visa_sponsorship,
    detect_work_mode,
    is_java_related_job,
)


def test_java_developer_title_accepted():
    assert is_java_related_job("Senior Java Developer", "Build APIs")


def test_spring_boot_title_accepted():
    assert is_java_related_job("Spring Boot Engineer", "")


def test_generic_frontend_rejected():
    assert not is_java_related_job("React Frontend Developer", "TypeScript and CSS")


def test_python_and_ai_accepted():
    assert is_java_related_job("Python Backend Engineer", "Django and FastAPI")
    assert is_java_related_job("Machine Learning Engineer", "PyTorch models")
    assert is_java_related_job("AI Engineer", "LLM applications")
    assert is_java_related_job("QA Engineer", "Test automation for Java services")
    assert is_java_related_job("Technical Project Manager", "Agile software delivery")


def test_unrelated_still_rejected():
    assert not is_java_related_job("Marketing Manager", "Social media campaigns")


def test_visa_detection():
    assert detect_visa_sponsorship("We offer H-1B visa sponsorship for qualified candidates")
    assert not detect_visa_sponsorship("Unfortunately we cannot sponsor visas at this time")


def test_work_mode_detection():
    assert detect_work_mode("This is a fully remote role") == "remote"
    assert detect_work_mode("Hybrid — 3 days in office") == "hybrid"
    assert detect_work_mode("On-site in Berlin") == "onsite"
    assert detect_work_mode("No remote work available") == "onsite"
    assert detect_work_mode("This is not a remote position") == "onsite"


def test_experience_level():
    assert detect_experience_level("Senior Java Developer") == "senior"
    assert detect_experience_level("Principal Java Architect") == "principal"
    assert detect_experience_level("Junior Java Developer") == "junior"
