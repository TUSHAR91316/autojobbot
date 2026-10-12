import httpx
import logging
from typing import List, Dict, Any
from backend.app.providers.base import BaseJobProvider

logger = logging.getLogger("applypilot.providers.remoteok")


class RemoteOKProvider(BaseJobProvider):
    @property
    def provider_name(self) -> str:
        return "remoteok"

    async def fetch_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        url = "https://remoteok.com/api"
        headers = {
            "User-Agent": "ApplyPilot-LocalAssistant/1.0 (Local-First Engineering Job Search)",
            "Accept": "application/json",
        }
        jobs: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    raw_data = res.json()
                    # First element in remoteok response is legal info, jobs follow
                    for item in raw_data:
                        if not isinstance(item, dict) or "position" not in item:
                            continue
                        
                        tags = item.get("tags") or []
                        skills = [t for t in tags if isinstance(t, str)]
                        salary_min = item.get("salary_min")
                        salary_max = item.get("salary_max")
                        
                        job_dict = {
                            "title": item.get("position", "Software Engineer"),
                            "company": item.get("company", "Remote Company"),
                            "location": item.get("location") or "Worldwide (Remote)",
                            "work_mode": "remote",
                            "employment_type": "full_time",
                            "salary_min": int(salary_min) if salary_min else None,
                            "salary_max": int(salary_max) if salary_max else None,
                            "salary_currency": "USD",
                            "experience_min_years": 2.0,
                            "experience_level": "mid",
                            "required_skills": skills,
                            "description": item.get("description", ""),
                            "source_platform": "remoteok",
                            "original_url": item.get("url", f"https://remoteok.com/l/{item.get('id', '')}"),
                            "source_job_id": str(item.get("id", "")),
                            "application_method": "ONE_CLICK" if item.get("apply_url") else "EXTERNAL_SITE",
                        }
                        jobs.append(job_dict)
                        if len(jobs) >= limit:
                            break
        except Exception as e:
            logger.warning(f"Failed to fetch public feed from RemoteOK: {e}")
        return jobs
