import csv
import io
from typing import List, Dict, Any


def parse_csv_jobs(file_content: str) -> List[Dict[str, Any]]:
    """Parse CSV text into normalized job dictionaries"""
    jobs: List[Dict[str, Any]] = []
    reader = csv.DictReader(io.StringIO(file_content))
    
    for row in reader:
        # Flexible key matching
        title = row.get("title") or row.get("job_title") or row.get("Title") or ""
        company = row.get("company") or row.get("company_name") or row.get("Company") or ""
        if not title or not company:
            continue
            
        location = row.get("location") or row.get("Location") or "Remote"
        work_mode = row.get("work_mode") or ("remote" if "remote" in location.lower() else "hybrid")
        url = row.get("url") or row.get("original_url") or row.get("link") or ""
        skills_raw = row.get("skills") or row.get("required_skills") or ""
        skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
        
        salary_min = None
        try:
            if row.get("salary_min"):
                salary_min = int(float(row.get("salary_min")))
        except Exception:
            pass
            
        salary_max = None
        try:
            if row.get("salary_max"):
                salary_max = int(float(row.get("salary_max")))
        except Exception:
            pass
            
        jobs.append({
            "title": title.strip(),
            "company": company.strip(),
            "location": location.strip(),
            "work_mode": work_mode.strip().lower(),
            "employment_type": (row.get("employment_type") or "full_time").strip().lower(),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "salary_currency": row.get("salary_currency", "USD").strip(),
            "experience_min_years": float(row.get("experience_min_years") or 2.0),
            "experience_level": row.get("experience_level", "mid").strip(),
            "required_skills": skills,
            "description": (row.get("description") or "").strip(),
            "source_platform": "csv_import",
            "original_url": url.strip(),
            "source_job_id": row.get("id") or None,
            "application_method": (row.get("application_method") or "EXTERNAL_SITE").strip(),
        })
    return jobs


def export_jobs_to_csv(jobs: List[Dict[str, Any]]) -> str:
    """Generate CSV string from list of job dictionaries"""
    if not jobs:
        return ""
    
    fieldnames = [
        "id", "title", "company", "location", "work_mode", "employment_type",
        "salary_min", "salary_max", "match_score", "status", "source_platform", "original_url"
    ]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for j in jobs:
        writer.writerow(j)
    return output.getvalue()


def export_history_to_csv(history: List[Dict[str, Any]]) -> str:
    """Generate CSV string from list of application history records"""
    if not history:
        return ""
    
    fieldnames = [
        "application_id", "job_title", "company", "source_platform", "match_score",
        "status", "last_action", "applied_at", "original_url"
    ]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for h in history:
        writer.writerow(h)
    return output.getvalue()
