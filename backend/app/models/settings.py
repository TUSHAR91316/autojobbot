from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, DateTime, JSON, String
from backend.app.database.session import Base


class AutomationSettings(Base):
    __tablename__ = "automation_settings"

    id = Column(Integer, primary_key=True, index=True)
    target_applications_per_session = Column(Integer, default=15)
    delay_between_attempts_sec = Column(Float, default=2.0)
    min_match_score = Column(Integer, default=60)
    max_jobs_to_inspect = Column(Integer, default=50)
    preferred_job_sources = Column(JSON, default=lambda: ["remoteok", "jobicy", "manual", "csv"])
    prioritize_easy_apply = Column(Boolean, default=True)
    include_external_in_manual_queue = Column(Boolean, default=True)
    require_review_before_submit = Column(Boolean, default=False)
    stop_after_failures = Column(Integer, default=3)
    skip_duplicates = Column(Boolean, default=True)
    stop_on_captcha_mfa = Column(Boolean, default=True)
    simulation_mode = Column(Boolean, default=True)  # Safe simulation mode on by default
    log_retention_days = Column(Integer, default=30)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobPreferences(Base):
    __tablename__ = "job_preferences"

    id = Column(Integer, primary_key=True, index=True)
    title_keywords = Column(JSON, default=lambda: ["Software Engineer", "Full Stack Developer", "Backend Engineer", "Python Developer"])
    negative_keywords = Column(JSON, default=lambda: ["Sales", "Accountant", "Marketing", "Recruiter"])
    preferred_locations = Column(JSON, default=lambda: ["Remote", "United States", "Canada", "Worldwide"])
    remote_only = Column(Boolean, default=True)
    min_salary = Column(Integer, default=80000)
    max_salary = Column(Integer, default=180000)
    experience_level = Column(String(50), default="mid")  # entry, mid, senior, lead
    required_skills = Column(JSON, default=lambda: ["Python", "JavaScript", "TypeScript", "React", "FastAPI"])
    preferred_companies = Column(JSON, default=list)
    excluded_companies = Column(JSON, default=list)
    
    # Configurable scoring weights (normalized automatically to 100%)
    weight_skills = Column(Float, default=40.0)
    weight_title = Column(Float, default=25.0)
    weight_experience = Column(Float, default=15.0)
    weight_location = Column(Float, default=10.0)
    weight_employment_type = Column(Float, default=10.0)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
