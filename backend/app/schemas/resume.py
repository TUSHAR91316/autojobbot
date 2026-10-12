from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ResumeVersionBase(BaseModel):
    label: str
    target_categories: List[str] = []
    is_primary: bool = False


class ResumeVersionCreate(ResumeVersionBase):
    pass


class ResumeVersionUpdate(BaseModel):
    label: Optional[str] = None
    target_categories: Optional[List[str]] = None
    is_primary: Optional[bool] = None


class ResumeVersionResponse(ResumeVersionBase):
    id: int
    file_name: str
    file_path: str
    file_size: int
    file_type: str
    extracted_text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
