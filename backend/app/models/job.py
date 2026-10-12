from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, Boolean
from backend.app.database.session import Base


class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), default="")
    work_mode = Column(String(50), default="remote")  # remote, hybrid, onsite
    employment_type = Column(String(50), default="full_time")  # full_time, contract, part_time, internship
    
    # Compensation
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default="USD")
    
    # Requirements
    experience_min_years = Column(Float, default=0.0)
    experience_level = Column(String(50), default="mid")  # entry, mid, senior, lead
    required_skills = Column(JSON, default=list)  # ["Python", "FastAPI", "React"]
    
    description = Column(Text, default="")
    source_platform = Column(String(100), default="manual", index=True)  # remoteok, jobicy, manual, csv, etc.
    original_url = Column(String(1000), default="")
    normalized_url = Column(String(1000), default="", index=True)
    source_job_id = Column(String(255), nullable=True, index=True)
    application_method = Column(String(50), default="EXTERNAL_SITE")  # EASY_APPLY, ONE_CLICK, EXTERNAL_SITE, SYNTHETIC
    
    # Matching and Eligibility
    match_score = Column(Float, default=0.0)
    match_breakdown = Column(JSON, default=dict)
    eligibility_assessment = Column(JSON, default=lambda: {"is_eligible": True, "reasons": []})
    
    # Status
    status = Column(String(50), default="DISCOVERED", index=True)  # DISCOVERED, MATCHED, QUEUED, SKIPPED, EXPIRED, APPLIED
    is_archived = Column(Boolean, default=False)
    
    discovered_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
