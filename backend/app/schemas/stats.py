from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from backend.app.schemas.job import JobListingResponse
from backend.app.schemas.application import JobApplicationResponse
from backend.app.schemas.log import ActivityLogResponse


class SessionProgress(BaseModel):
    is_active: bool = False
    is_paused: bool = False
    status: str = "IDLE"  # IDLE, RUNNING, PAUSED, STOPPING
    target_count: int = 15
    processed_count: int = 0
    submitted_count: int = 0
    manual_count: int = 0
    failed_count: int = 0
    current_job_id: Optional[int] = None
    current_job_title: Optional[str] = None
    current_action: Optional[str] = None
    session_id: Optional[str] = None
    started_at: Optional[datetime] = None


class LastRunDetails(BaseModel):
    session_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    target: int = 0
    submitted: int = 0
    failed: int = 0
    manual: int = 0
    status: str = "None"


class DashboardStatsResponse(BaseModel):
    # Core Counts from real DB
    jobs_discovered: int = 0
    jobs_matching_preferences: int = 0
    applications_prepared: int = 0
    applications_submitted: int = 0
    applications_awaiting_review: int = 0
    external_manual_action_required: int = 0
    applications_failed_or_cancelled: int = 0
    
    # Distributions
    status_distribution: Dict[str, int] = {}
    source_distribution: Dict[str, int] = {}
    
    # Active Session & Last Run telemetry
    session_progress: SessionProgress
    last_run: LastRunDetails
    
    # Recent feeds
    recent_jobs: List[JobListingResponse] = []
    recent_activity: List[ActivityLogResponse] = []
