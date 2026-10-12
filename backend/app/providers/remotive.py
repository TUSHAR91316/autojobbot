import httpx
import logging
from typing import List, Dict, Any
from backend.app.providers.base import BaseJobProvider

logger = logging.getLogger("applypilot.providers.remotive")


class RemotiveProvider(BaseJobProvider):
    """
    Fetches real software development remote jobs from Remotive API.
    Remotive curates high-quality tech jobs with verified companies.
    """
    @property
    def provider_name(self) -> str:
        return "remotive"

    async def fetch_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=50"
        headers = {
            "User-Agent": "ApplyPilot-LocalAssistant/1.0",
            "Accept": "application/json",
        }
        jobs: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    job_items = data.get("jobs") or []
                    for item in job_items:
                        if not isinstance(item, dict):
                            continue

                        tags = [str(t).strip() for t in (item.get("tags") or []) if t]
                        loc = item.get("candidate_required_location") or "Worldwide (Remote)"

                        job_dict = {
                            "title": item.get("title", "Software Engineer"),
                            "company": item.get("company_name", "Tech Company"),
                            "location": loc,
                            "work_mode": "remote",
                            "employment_type": item.get("job_type", "full_time").lower().replace("-", "_"),
                            "salary_min": None,
                            "salary_max": None,
                            "salary_currency": "USD",
                            "experience_min_years": 3.0,
                            "experience_level": "senior" if "senior" in (item.get("title", "")).lower() else "mid",
                            "required_skills": tags[:8],
                            "description": item.get("description", ""),
                            "source_platform": "remotive",
                            "original_url": item.get("url", ""),
                            "source_job_id": str(item.get("id", "")),
                            "application_method": "EXTERNAL_SITE",
                        }
                        jobs.append(job_dict)
                        if len(jobs) >= limit:
                            break
        except Exception as e:
            logger.warning(f"Failed to fetch real jobs from Remotive: {e}")
        return jobs
