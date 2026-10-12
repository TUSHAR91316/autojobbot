import re
from typing import Dict, Any, List, Tuple
from backend.app.models.profile import CandidateProfile
from backend.app.models.settings import JobPreferences


def normalize_weights(prefs: JobPreferences) -> Dict[str, float]:
    """Normalize user configured weights so they sum up to 100%"""
    def _get_val(attr: str, default: float) -> float:
        v = getattr(prefs, attr, None)
        return float(v) if v is not None else default

    w_skills = max(0.0, _get_val("weight_skills", 40.0))
    w_title = max(0.0, _get_val("weight_title", 25.0))
    w_exp = max(0.0, _get_val("weight_experience", 15.0))
    w_loc = max(0.0, _get_val("weight_location", 10.0))
    w_emp = max(0.0, _get_val("weight_employment_type", 10.0))
    
    total = w_skills + w_title + w_exp + w_loc + w_emp
    if total <= 0:
        return {
            "skills": 0.40,
            "title": 0.25,
            "experience": 0.15,
            "location": 0.10,
            "employment_type": 0.10,
        }
    
    return {
        "skills": w_skills / total,
        "title": w_title / total,
        "experience": w_exp / total,
        "location": w_loc / total,
        "employment_type": w_emp / total,
    }


def compute_skills_score(job_skills: List[str], candidate_skills: List[str], job_description: str) -> Tuple[float, List[str], List[str]]:
    """Calculate skill match percentage and matched/missing lists"""
    cand_norm = {str(s).strip().lower() for s in candidate_skills if s and str(s).strip()}
    
    # If explicit job_skills list is empty, extract candidate skills mentioned in description
    target_skills = [str(s).strip().lower() for s in job_skills if s and str(s).strip()]
    if not target_skills and job_description:
        desc_lower = job_description.lower()
        target_skills = [s for s in cand_norm if re.search(r"\b" + re.escape(s) + r"\b", desc_lower)]
    
    if not target_skills:
        return 75.0, list(cand_norm)[:5], []  # Neutral high baseline if no specific skills requested
    
    matched = [s for s in target_skills if s in cand_norm]
    missing = [s for s in target_skills if s not in cand_norm]
    
    score = (len(matched) / len(target_skills)) * 100.0
    return round(score, 1), matched, missing


def compute_title_score(job_title: str, preferred_titles: List[str], candidate_headline: str) -> float:
    """Calculate title relevance score (0-100)"""
    title_norm = job_title.lower()
    
    # Check exact substring
    for pref in preferred_titles:
        pref_norm = pref.strip().lower()
        if pref_norm and pref_norm in title_norm:
            return 100.0
    
    # Token overlap
    title_words = set(re.findall(r"\w+", title_norm))
    pref_words = set()
    for pref in preferred_titles:
        pref_words.update(re.findall(r"\w+", pref.lower()))
    
    if not pref_words:
        if candidate_headline:
            pref_words.update(re.findall(r"\w+", candidate_headline.lower()))
    
    if not pref_words:
        return 70.0
    
    common = title_words.intersection(pref_words)
    if common:
        overlap_ratio = len(common) / min(len(title_words), len(pref_words))
        return min(100.0, round(overlap_ratio * 100.0, 1))
    
    return 30.0


def compute_experience_score(job_exp_years: float, candidate_years: float, job_level: str, candidate_level: str) -> float:
    """Calculate experience compatibility score (0-100)"""
    diff = candidate_years - job_exp_years
    if diff >= 0:
        return 100.0
    elif diff >= -1.0:
        return 85.0
    elif diff >= -2.0:
        return 65.0
    elif diff >= -3.0:
        return 40.0
    else:
        return 20.0


def compute_location_score(
    job_work_mode: str,
    job_location: str,
    pref_remote_only: bool,
    pref_locations: List[str],
    candidate_location: str = "",
) -> float:
    """Calculate location & work mode score (0-100) with India preference support"""
    mode = (job_work_mode or "").lower()
    loc_norm = (job_location or "").lower()
    cand_norm = (candidate_location or "").lower()

    # India tech hub aliases
    india_keywords = [
        "india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai",
        "delhi", "noida", "gurgaon", "gurugram", "chennai", "kolkata",
        "ahmedabad", "remote - india", "remote (india)"
    ]
    user_prefers_india = (
        any(k in cand_norm for k in india_keywords) or
        any(k in p.lower() for p in pref_locations for k in ["india", "bengaluru", "bangalore", "hyderabad", "pune", "mumbai", "delhi", "gurgaon"])
    )
    job_is_in_india = any(k in loc_norm for k in india_keywords)

    if user_prefers_india and job_is_in_india:
        return 100.0

    if pref_remote_only:
        if "remote" in mode:
            return 100.0
        elif "hybrid" in mode:
            return 50.0
        else:
            return 20.0
    else:
        if "remote" in mode:
            return 100.0
        for ploc in pref_locations:
            if ploc.lower() in loc_norm:
                return 100.0
        return 70.0


def compute_employment_score(job_type: str, candidate_types: List[str]) -> float:
    """Calculate employment type score (0-100)"""
    j_type = (job_type or "full_time").lower().replace("-", "_")
    cand_types = [t.lower().replace("-", "_") for t in candidate_types]
    if not cand_types or j_type in cand_types or "any" in cand_types:
        return 100.0
    return 40.0


def evaluate_job_match(job_dict: Dict[str, Any], profile: CandidateProfile, prefs: JobPreferences) -> Tuple[float, Dict[str, Any], Dict[str, Any]]:
    """
    Transparent weighted matching algorithm.
    Returns:
      (total_score, match_breakdown, eligibility_assessment)
    """
    weights = normalize_weights(prefs)
    
    # 1. Skills
    cand_skills = profile.skills or []
    job_skills = job_dict.get("required_skills") or []
    skills_score, matched_skills, missing_skills = compute_skills_score(
        job_skills, cand_skills, job_dict.get("description", "")
    )
    
    # 2. Title
    pref_titles = prefs.title_keywords or profile.preferred_job_titles or []
    title_score = compute_title_score(
        job_dict.get("title", ""), pref_titles, profile.headline or ""
    )
    
    # 3. Experience
    cand_exp = profile.years_of_experience or 0.0
    job_exp = float(job_dict.get("experience_min_years") or 0.0)
    exp_score = compute_experience_score(
        job_exp, cand_exp, job_dict.get("experience_level", "mid"), profile.experience_level or "mid"
    )
    
    # 4. Location
    loc_score = compute_location_score(
        job_dict.get("work_mode", "remote"),
        job_dict.get("location", ""),
        prefs.remote_only,
        prefs.preferred_locations or [],
        candidate_location=profile.current_location or "",
    )
    
    # 5. Employment Type
    emp_score = compute_employment_score(
        job_dict.get("employment_type", "full_time"),
        profile.employment_types or ["full_time"]
    )
    
    # Weighted total
    total_score = (
        skills_score * weights["skills"] +
        title_score * weights["title"] +
        exp_score * weights["experience"] +
        loc_score * weights["location"] +
        emp_score * weights["employment_type"]
    )
    total_score = round(min(100.0, max(0.0, total_score)), 1)
    
    # Detailed breakdown
    match_breakdown = {
        "skills_score": skills_score,
        "skills_weight": round(weights["skills"] * 100, 1),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "title_score": title_score,
        "title_weight": round(weights["title"] * 100, 1),
        "experience_score": exp_score,
        "experience_weight": round(weights["experience"] * 100, 1),
        "location_score": loc_score,
        "location_weight": round(weights["location"] * 100, 1),
        "employment_type_score": emp_score,
        "employment_type_weight": round(weights["employment_type"] * 100, 1),
    }
    
    # Eligibility assessment
    is_eligible = True
    ineligible_reasons = []
    
    # Check negative title keywords
    job_title_lower = (job_dict.get("title") or "").lower()
    for neg in (prefs.negative_keywords or []):
        if neg.strip() and neg.lower() in job_title_lower:
            is_eligible = False
            ineligible_reasons.append(f"Title contains excluded keyword: '{neg}'")
    
    # Check excluded companies
    job_company_lower = (job_dict.get("company") or "").lower()
    for exc_co in (prefs.excluded_companies or []):
        if exc_co.strip() and exc_co.lower() in job_company_lower:
            is_eligible = False
            ineligible_reasons.append(f"Company is in excluded list: '{exc_co}'")
            
    # Check strict remote requirement if configured
    if prefs.remote_only and job_dict.get("work_mode") == "onsite":
        is_eligible = False
        ineligible_reasons.append("Job is Onsite only but preference is Remote Only")
    
    # Check if experience gap is too large (> 4 years underqualified)
    if (job_exp - cand_exp) > 4.0:
        is_eligible = False
        ineligible_reasons.append(f"Experience requirement ({job_exp}y) exceeds profile ({cand_exp}y) by >4 years")
        
    eligibility_assessment = {
        "is_eligible": is_eligible,
        "reasons": ineligible_reasons,
    }
    
    return total_score, match_breakdown, eligibility_assessment
