"""
Shared fixtures for Insuretechdaily test suite.
"""
import os
import sys
import pytest

# Ensure the project root is on sys.path so source modules are importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


@pytest.fixture
def sample_job():
    return {
        "title": "Insurance Operations Manager",
        "company": "Acme Insurtech",
        "source": "Ashby",
        "link": "https://example.com/jobs/ops-manager",
        "location": "Remote EU",
        "location_type": "remote",
        "salary": "€70K–€85K",
        "description": "Leading operations at a growing insurtech MGA.",
    }


@pytest.fixture
def sample_ai_result():
    return {
        "score": 85,
        "reason": "Strong match: remote EU, MGA environment, operations focus.",
        "location_type": "remote",
        "salary_info": "€70K–€85K",
        "cv_summary_en": "Experienced insurance ops manager.",
        "cv_summary_es": "Experto en operaciones de seguros.",
        "cover_letter_en": "Dear Hiring Team,",
        "cover_letter_es": "Estimado equipo,",
    }


@pytest.fixture
def sample_article():
    return {
        "source": "InsTech London",
        "title": "New Insurtech Startup Raises €20M for EU Expansion",
        "url": "https://example.com/article",
        "snippet": "A new digital insurance platform focused on parametric products.",
        "date": "2026-04-05",
    }
