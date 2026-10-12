from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from backend.app.database.session import Base


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String(255), nullable=False)  # e.g. "FullStack_Lead_2026", "Backend_Python"
    target_categories = Column(JSON, default=list)  # ["Full Stack", "Backend", "AI Engineer"]
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)
    file_type = Column(String(20), default="pdf")  # pdf or docx
    extracted_text = Column(Text, default="")
    is_primary = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
