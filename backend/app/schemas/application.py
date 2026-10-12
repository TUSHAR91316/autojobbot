from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from backend.app.schemas.job import JobListingResponse
from backend.app.schemas.resume import ResumeVersionResponse


class JobApplicationBase(BaseModel):
    job_id: int
    resume_version_id: Optional[int] = None
    status: str = "QUEUED"
    queue_position: int = 0
    prepared_data: Dict[str, Any] = {}
    unanswered_questions: List[Dict[str, Any]] = []
    review_notes: str = ""
    cover_letter: str = ""
    manual_notes: str = ""


class JobApplicationCreate(BaseModel):
    job_id: int
    resume_version_id: Optional[int] = None


class JobApplicationUpdate(BaseModel):
    status: Optional[str] = None
    queue_position: Optional[int] = None
    prepared_data: Optional[Dict[str, Any]] = None
    unanswered_questions: Optional[List[Dict[str, Any]]] = None
    review_notes: Optional[str] = None
    cover_letter: Optional[str] = None
    manual_notes: Optional[str] = None
    last_action: Optional[str] = None
    error_message: Optional[str] = None


class JobApplicationResponse(JobApplicationBase):
    id: int
    last_action: str
    error_message: str
    screenshot_path: str
    session_id: Optional[str] = None
    applied_at: Optional[datetime] = None
    last_action_at: datetime
    created_at: datetime
    updated_at: datetime
    job: Optional[JobListingResponse] = None
    resume: Optional[ResumeVersionResponse] = None

    class Config:
        from_attributes = True
