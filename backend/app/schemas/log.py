from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel


class ActivityLogBase(BaseModel):
    level: str = "INFO"
    action: str
    message: str
    details: Dict[str, Any] = {}
    job_id: Optional[int] = None
    application_id: Optional[int] = None


class ActivityLogCreate(ActivityLogBase):
    pass


class ActivityLogResponse(ActivityLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
