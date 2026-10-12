from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON
from backend.app.database.session import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), default="")
    email = Column(String(255), default="")
    phone = Column(String(100), default="")
    current_location = Column(String(255), default="")
    headline = Column(String(255), default="")
    summary = Column(Text, default="")
    
    # Skills and Structured History as JSON
    skills = Column(JSON, default=list)  # ["Python", "React", "TypeScript", ...]
    work_experience = Column(JSON, default=list)  # list of {title, company, location, start_date, end_date, current, description}
    education = Column(JSON, default=list)  # list of {degree, institution, field_of_study, graduation_year, gpa}
    projects = Column(JSON, default=list)  # list of {name, description, url, technologies}
    certifications = Column(JSON, default=list)  # list of {name, issuer, issue_date, url}
    
    # Social & Portfolio links
    portfolio_url = Column(String(500), default="")
    github_url = Column(String(500), default="")
    linkedin_url = Column(String(500), default="")
    
    # Job Search Preferences
    preferred_job_titles = Column(JSON, default=list)  # ["Software Engineer", "Full Stack Developer"]
    preferred_locations = Column(JSON, default=list)  # ["Remote", "United States", "New York, NY"]
    remote_preference = Column(String(50), default="remote_only")  # remote_only, hybrid, onsite, any
    salary_expectation_min = Column(Integer, default=0)
    salary_expectation_max = Column(Integer, default=0)
    salary_currency = Column(String(10), default="USD")
    years_of_experience = Column(Float, default=0.0)
    experience_level = Column(String(50), default="mid")  # entry, mid, senior, lead, executive
    employment_types = Column(JSON, default=lambda: ["full_time"])  # ["full_time", "contract", "part_time"]
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
