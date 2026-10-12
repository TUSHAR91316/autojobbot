import httpx
import logging
from typing import List, Dict, Any
from backend.app.providers.base import BaseJobProvider

logger = logging.getLogger("applypilot.providers.jobicy")


class JobicyProvider(BaseJobProvider):
    @property
    def provider_name(self) -> str:
        return "jobicy"

    async def fetch_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        url = "https://jobicy.com/api/v2/remote-jobs?count=50&industry=dev"
        headers = {
            "User-Agent": "ApplyPilot-LocalAssistant/1.0",
            "Accept": "application/json",
        }
        jobs: List[Dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    job_items = data.get("jobs") or []
                    for item in job_items:
                        if not isinstance(item, dict):
                            continue
                        
                        salary_min = item.get("annualSalaryMin")
                        salary_max = item.get("annualSalaryMax")
                        
                        skills = []
                        ind = item.get("jobIndustry")
                        if isinstance(ind, list):
                            skills.extend([str(x) for x in ind if x])
                        elif isinstance(ind, str) and ind.strip():
                            skills.append(ind.strip())

                        job_dict = {
                            "title": item.get("jobTitle", "Software Engineer"),
                            "company": item.get("companyName", "Tech Employer"),
                            "location": item.get("jobGeo", "Worldwide (Remote)"),
                            "work_mode": "remote",
                            "employment_type": item.get("jobType", "full_time"),
                            "salary_min": int(salary_min) if salary_min else None,
                            "salary_max": int(salary_max) if salary_max else None,
                            "salary_currency": item.get("salaryCurrency", "USD"),
                            "experience_min_years": 2.0,
                            "experience_level": item.get("jobLevel", "mid"),
                            "required_skills": skills,
                            "description": item.get("jobDescription", ""),
                            "source_platform": "jobicy",
                            "original_url": item.get("url", ""),
                            "source_job_id": str(item.get("id", "")),
                            "application_method": "EXTERNAL_SITE",
                        }
                        jobs.append(job_dict)
                        if len(jobs) >= limit:
                            break
        except Exception as e:
            logger.warning(f"Failed to fetch public feed from Jobicy: {e}")
        return jobs
