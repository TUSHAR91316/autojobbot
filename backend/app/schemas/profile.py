from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field


class WorkExperienceItem(BaseModel):
    title: str = ""
    company: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    current: bool = False
    description: str = ""


class EducationItem(BaseModel):
    degree: str = ""
    institution: str = ""
    field_of_study: str = ""
    graduation_year: str = ""
    gpa: str = ""


class ProjectItem(BaseModel):
    name: str = ""
    description: str = ""
    url: str = ""
    technologies: List[str] = []


class CertificationItem(BaseModel):
    name: str = ""
    issuer: str = ""
    issue_date: str = ""
    url: str = ""


class CandidateProfileBase(BaseModel):
    full_name: str = ""
    email: str = ""
    phone: str = ""
    current_location: str = ""
    headline: str = ""
    summary: str = ""
    
    skills: List[str] = []
    work_experience: List[WorkExperienceItem] = []
    education: List[EducationItem] = []
    projects: List[ProjectItem] = []
    certifications: List[CertificationItem] = []
    
    portfolio_url: str = ""
    github_url: str = ""
    linkedin_url: str = ""
    
    preferred_job_titles: List[str] = []
    preferred_locations: List[str] = []
    remote_preference: str = "remote_only"
    salary_expectation_min: int = 0
    salary_expectation_max: int = 0
    salary_currency: str = "USD"
    years_of_experience: float = 0.0
    experience_level: str = "mid"
    employment_types: List[str] = ["full_time"]


class CandidateProfileCreate(CandidateProfileBase):
    pass


class CandidateProfileUpdate(CandidateProfileBase):
    pass


class CandidateProfileResponse(CandidateProfileBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
