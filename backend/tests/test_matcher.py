import pytest
from backend.app.services.matcher import (
    normalize_weights,
    compute_skills_score,
    compute_title_score,
    evaluate_job_match,
)
from backend.app.models.profile import CandidateProfile
from backend.app.models.settings import JobPreferences


def test_weight_normalization():
    prefs = JobPreferences(
        weight_skills=50.0,
        weight_title=25.0,
        weight_experience=25.0,
        weight_location=0.0,
        weight_employment_type=0.0,
    )
    weights = normalize_weights(prefs)
    assert round(sum(weights.values()), 4) == 1.0
    assert weights["skills"] == 0.50
    assert weights["title"] == 0.25
    assert weights["experience"] == 0.25


def test_skills_matching():
    job_skills = ["Python", "FastAPI", "Docker", "Kubernetes"]
    cand_skills = ["Python", "FastAPI", "React"]
    score, matched, missing = compute_skills_score(job_skills, cand_skills, "")
    
    assert score == 50.0
    assert "python" in matched
    assert "fastapi" in matched
    assert "docker" in missing


def test_title_matching():
    preferred = ["Senior Python Engineer", "Backend Developer"]
    score_exact = compute_title_score("Senior Python Engineer", preferred, "")
    assert score_exact == 100.0

    score_partial = compute_title_score("Staff Backend Developer", preferred, "")
    assert score_partial >= 60.0


def test_evaluate_job_match_ineligibility():
    profile = CandidateProfile(
        full_name="Jane Doe",
        skills=["Python", "FastAPI"],
        years_of_experience=2.0,
        experience_level="mid",
    )
    prefs = JobPreferences(
        title_keywords=["Software Engineer"],
        negative_keywords=["Sales", "Marketing"],
        remote_only=True,
    )
    
    # Negative keyword test
    job_sales = {
        "title": "Software Sales Representative",
        "company": "SaaS Co",
        "work_mode": "remote",
        "experience_min_years": 2.0,
        "required_skills": ["Sales"],
    }
    score, breakdown, elig = evaluate_job_match(job_sales, profile, prefs)
    assert elig["is_eligible"] is False
    assert any("Sales" in r for r in elig["reasons"])

    # Onsite mismatch when remote_only preferred
    job_onsite = {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "work_mode": "onsite",
        "experience_min_years": 2.0,
        "required_skills": ["Python"],
    }
    score2, breakdown2, elig2 = evaluate_job_match(job_onsite, profile, prefs)
    assert elig2["is_eligible"] is False
    assert any("Onsite" in r for r in elig2["reasons"])
