from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class AutomationSettingsBase(BaseModel):
    target_applications_per_session: int = Field(default=15, ge=1, le=15)
    delay_between_attempts_sec: float = Field(default=2.0, ge=1.0, le=5.0)
    min_match_score: int = Field(default=60, ge=0, le=100)
    max_jobs_to_inspect: int = Field(default=50, ge=5, le=500)
    preferred_job_sources: List[str] = ["remoteok", "jobicy", "manual", "csv"]
    prioritize_easy_apply: bool = True
    include_external_in_manual_queue: bool = True
    require_review_before_submit: bool = False
    stop_after_failures: int = Field(default=3, ge=1, le=20)
    skip_duplicates: bool = True
    stop_on_captcha_mfa: bool = True
    simulation_mode: bool = True
    log_retention_days: int = Field(default=30, ge=1, le=365)


class AutomationSettingsUpdate(BaseModel):
    target_applications_per_session: Optional[int] = Field(default=None, ge=1, le=15)
    delay_between_attempts_sec: Optional[float] = Field(default=None, ge=1.0, le=5.0)
    min_match_score: Optional[int] = Field(default=None, ge=0, le=100)
    max_jobs_to_inspect: Optional[int] = None
    preferred_job_sources: Optional[List[str]] = None
    prioritize_easy_apply: Optional[bool] = None
    include_external_in_manual_queue: Optional[bool] = None
    require_review_before_submit: Optional[bool] = None
    stop_after_failures: Optional[int] = None
    skip_duplicates: Optional[bool] = None
    stop_on_captcha_mfa: Optional[bool] = None
    simulation_mode: Optional[bool] = None
    log_retention_days: Optional[int] = None


class AutomationSettingsResponse(AutomationSettingsBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True


class JobPreferencesBase(BaseModel):
    title_keywords: List[str] = ["Software Engineer", "Full Stack Developer", "Backend Engineer", "Python Developer"]
    negative_keywords: List[str] = ["Sales", "Accountant", "Marketing", "Recruiter"]
    preferred_locations: List[str] = ["Remote", "United States", "Worldwide"]
    remote_only: bool = True
    min_salary: int = 80000
    max_salary: int = 180000
    experience_level: str = "mid"
    required_skills: List[str] = ["Python", "JavaScript", "TypeScript", "React", "FastAPI"]
    preferred_companies: List[str] = []
    excluded_companies: List[str] = []
    
    weight_skills: float = 40.0
    weight_title: float = 25.0
    weight_experience: float = 15.0
    weight_location: float = 10.0
    weight_employment_type: float = 10.0


class JobPreferencesUpdate(BaseModel):
    title_keywords: Optional[List[str]] = None
    negative_keywords: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    remote_only: Optional[bool] = None
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    experience_level: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_companies: Optional[List[str]] = None
    excluded_companies: Optional[List[str]] = None
    
    weight_skills: Optional[float] = None
    weight_title: Optional[float] = None
    weight_experience: Optional[float] = None
    weight_location: Optional[float] = None
    weight_employment_type: Optional[float] = None


class JobPreferencesResponse(JobPreferencesBase):
    id: int
    updated_at: datetime

    class Config:
        from_attributes = True
