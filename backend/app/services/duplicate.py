import re
from urllib.parse import urlparse, urlunparse
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models.job import JobListing


def normalize_job_url(raw_url: str) -> str:
    """Normalize URL by stripping query tracking params, fragments, and trailing slashes"""
    if not raw_url:
        return ""
    try:
        parsed = urlparse(raw_url.strip())
        # Rebuild without query string and fragments for canonical comparison
        netloc = parsed.netloc.lower().replace("www.", "")
        path = parsed.path.rstrip("/")
        normalized = f"{parsed.scheme.lower()}://{netloc}{path}"
        return normalized
    except Exception:
        return raw_url.strip().lower()


def normalize_string(val: str) -> str:
    """Lowercase and remove punctuation for comparison"""
    if not val:
        return ""
    return re.sub(r"[^\w\s]", "", val.lower()).strip()


def check_for_duplicate_job(
    db: Session,
    raw_url: str,
    title: str,
    company: str,
    source_job_id: Optional[str] = None
) -> Tuple[bool, Optional[JobListing], str]:
    """
    Check if a job is already in the database using:
    1. Normalized URL
    2. Source Job ID (if present)
    3. Company + normalized Title match
    Returns: (is_duplicate, existing_job_record, match_reason)
    """
    norm_url = normalize_job_url(raw_url)
    
    # 1. URL match
    if norm_url:
        existing_by_url = db.query(JobListing).filter(JobListing.normalized_url == norm_url).first()
        if existing_by_url:
            return True, existing_by_url, "Matching URL found in database"
            
    # 2. Source ID match
    if source_job_id:
        existing_by_id = db.query(JobListing).filter(JobListing.source_job_id == source_job_id).first()
        if existing_by_id:
            return True, existing_by_id, f"Matching source job ID '{source_job_id}' found"

    # 3. Company & Title match
    norm_title = normalize_string(title)
    norm_company = normalize_string(company)
    
    if norm_title and norm_company:
        all_same_company = db.query(JobListing).filter(JobListing.company.ilike(f"%{company.strip()}%")).all()
        for cand in all_same_company:
            if normalize_string(cand.title) == norm_title:
                return True, cand, f"Same company ('{cand.company}') and title ('{cand.title}') already exists"

    return False, None, ""
