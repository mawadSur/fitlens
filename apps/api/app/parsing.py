"""Resume text extraction (PDF/DOCX/TXT) + skill extraction over a taxonomy."""
from __future__ import annotations

import io
import re

# Compact but representative IT-staffing skill taxonomy. Multi-word entries are
# matched as phrases; short/ambiguous tokens use word boundaries.
SKILL_TAXONOMY: list[str] = [
    "python", "java", "javascript", "typescript", "c#", ".net", "go", "rust", "scala",
    "react", "angular", "vue", "next.js", "node.js", "spring boot", "django", "fastapi",
    "flask", "express", "graphql", "rest", "microservices",
    "aws", "azure", "gcp", "kubernetes", "docker", "terraform", "ansible", "jenkins",
    "ci/cd", "devops", "linux",
    "sql", "postgresql", "mysql", "mongodb", "oracle", "snowflake", "redshift",
    "databricks", "spark", "kafka", "airflow", "hadoop", "etl",
    "machine learning", "deep learning", "tensorflow", "pytorch", "nlp", "llm",
    "data engineering", "data science", "tableau", "power bi",
    "salesforce", "servicenow", "sap", "workday",
    "selenium", "cypress", "playwright", "qa automation",
    "agile", "scrum", "jira",
]

_PHRASE_PATTERNS = [
    (skill, re.compile(r"(?<![a-z0-9])" + re.escape(skill) + r"(?![a-z0-9])", re.IGNORECASE))
    for skill in SKILL_TAXONOMY
]


def extract_text(filename: str, data: bytes) -> str:
    name = (filename or "").lower()
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        if name.endswith(".docx"):
            import docx  # python-docx

            doc = docx.Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)
    except Exception:  # noqa: BLE001 — fall through to raw decode
        pass
    return data.decode("utf-8", errors="ignore")


def extract_skills(text: str) -> list[str]:
    """Return taxonomy skills present in the text, preserving taxonomy order."""
    if not text:
        return []
    found = [skill for skill, pat in _PHRASE_PATTERNS if pat.search(text)]
    # de-dupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for s in found:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out
