from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl


class JobListingBase(BaseModel):
    title: str
    company: str
    location: str = ""
    work_mode: str = "remote"
    employment_type: str = "full_time"
    
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    
    experience_min_years: float = 0.0
    experience_level: str = "mid"
    required_skills: List[str] = []
    
    description: str = ""
    source_platform: str = "manual"
    original_url: str = ""
    source_job_id: Optional[str] = None
    application_method: str = "EXTERNAL_SITE"


class JobListingCreate(JobListingBase):
    pass


class JobListingUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_min_years: Optional[float] = None
    required_skills: Optional[List[str]] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_archived: Optional[bool] = None


class JobListingResponse(JobListingBase):
    id: int
    normalized_url: str
    match_score: float
    match_breakdown: Dict[str, Any]
    eligibility_assessment: Dict[str, Any]
    status: str
    is_archived: bool
    discovered_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobFilterParams(BaseModel):
    search: Optional[str] = None
    company: Optional[str] = None
    work_mode: Optional[str] = None
    experience_level: Optional[str] = None
    min_score: Optional[float] = None
    source_platform: Optional[str] = None
    status: Optional[str] = None
    skip: int = 0
    limit: int = 50
