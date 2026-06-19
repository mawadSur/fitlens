"""Edge cases for parsing.py not covered by test_parsing_immigration.py."""
import pytest
from app.parsing import extract_skills, extract_text


# ─── extract_skills ───────────────────────────────────────────────────────────

def test_extract_skills_empty_string():
    assert extract_skills("") == []


def test_extract_skills_none_like_whitespace():
    assert extract_skills("   ") == []


def test_extract_skills_multi_word_term():
    text = "We build machine learning models for NLP."
    skills = extract_skills(text)
    assert "machine learning" in skills
    assert "nlp" in skills


def test_extract_skills_deduped():
    text = "Python Python PYTHON python"
    skills = extract_skills(text)
    assert skills.count("python") == 1


def test_extract_skills_no_false_positives():
    # "go" inside a word should NOT match the Go language skill.
    text = "Heptathletes undergo rigorous training."
    skills = extract_skills(text)
    assert "go" not in skills


def test_extract_skills_preserves_taxonomy_order():
    # Taxonomy order: python comes before spark.
    text = "Built Spark pipelines in Python."
    skills = extract_skills(text)
    assert skills.index("python") < skills.index("spark")


def test_extract_skills_case_insensitive():
    text = "Expert in KUBERNETES, Docker, and Terraform."
    skills = extract_skills(text)
    assert "kubernetes" in skills
    assert "docker" in skills
    assert "terraform" in skills


# ─── extract_text ─────────────────────────────────────────────────────────────

def test_extract_text_txt_fallback():
    data = b"Senior Python developer with AWS experience."
    result = extract_text("resume.txt", data)
    assert "Python" in result


def test_extract_text_unknown_extension_fallback():
    data = b"Some resume content."
    result = extract_text("resume.xyz", data)
    assert "resume content" in result


def test_extract_text_pdf_corrupt_falls_through():
    # Corrupt PDF bytes → exception caught → UTF-8 decode fallback.
    data = b"%PDF-not-really-a-pdf"
    result = extract_text("resume.pdf", data)
    # Should not raise; returns decoded string.
    assert isinstance(result, str)


def test_extract_text_empty_bytes():
    result = extract_text("empty.txt", b"")
    assert result == ""


def test_extract_text_utf8_with_errors_ignored():
    data = b"Python \xff\xfe developer"
    result = extract_text("cv.txt", data)
    assert "Python" in result
    assert "developer" in result
