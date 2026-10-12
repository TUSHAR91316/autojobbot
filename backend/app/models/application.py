from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


class ApplicationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    MATCHED = "MATCHED"
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    READY_TO_SUBMIT = "READY_TO_SUBMIT"
    SUBMITTED = "SUBMITTED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    MANUAL_ACTION_REQUIRED = "MANUAL_ACTION_REQUIRED"
    CANCELLED = "CANCELLED"


# Valid state transitions
VALID_TRANSITIONS = {
    ApplicationStatus.DISCOVERED: {ApplicationStatus.MATCHED, ApplicationStatus.SKIPPED, ApplicationStatus.QUEUED},
    ApplicationStatus.MATCHED: {ApplicationStatus.QUEUED, ApplicationStatus.SKIPPED},
    ApplicationStatus.QUEUED: {ApplicationStatus.PREPARING, ApplicationStatus.SKIPPED, ApplicationStatus.CANCELLED},
    ApplicationStatus.PREPARING: {
        ApplicationStatus.AWAITING_REVIEW,
        ApplicationStatus.READY_TO_SUBMIT,
        ApplicationStatus.MANUAL_ACTION_REQUIRED,
        ApplicationStatus.FAILED,
        ApplicationStatus.CANCELLED,
    },
    ApplicationStatus.AWAITING_REVIEW: {
        ApplicationStatus.READY_TO_SUBMIT,
        ApplicationStatus.SKIPPED,
        ApplicationStatus.CANCELLED,
        ApplicationStatus.MANUAL_ACTION_REQUIRED,
    },
    ApplicationStatus.READY_TO_SUBMIT: {
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.FAILED,
        ApplicationStatus.CANCELLED,
    },
    ApplicationStatus.MANUAL_ACTION_REQUIRED: {
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.SKIPPED,
        ApplicationStatus.CANCELLED,
    },
    ApplicationStatus.FAILED: {ApplicationStatus.QUEUED, ApplicationStatus.SKIPPED},
    ApplicationStatus.SUBMITTED: set(),
    ApplicationStatus.SKIPPED: {ApplicationStatus.QUEUED},
    ApplicationStatus.CANCELLED: {ApplicationStatus.QUEUED},
}


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"), nullable=False, index=True)
    resume_version_id = Column(Integer, ForeignKey("resume_versions.id"), nullable=True)
    
    status = Column(String(50), default=ApplicationStatus.QUEUED.value, index=True)
    queue_position = Column(Integer, default=0, index=True)
    
    # Form data & truthful extraction
    prepared_data = Column(JSON, default=dict)
    unanswered_questions = Column(JSON, default=list)  # Questions needing human review
    review_notes = Column(Text, default="")
    
    # External and manual assistance metadata
    cover_letter = Column(Text, default="")
    manual_notes = Column(Text, default="")
    external_portal_url = Column(String(1000), default="")
    
    # Execution telemetry
    last_action = Column(String(255), default="Initialized")
    error_message = Column(Text, default="")
    screenshot_path = Column(String(500), default="")
    session_id = Column(String(100), nullable=True)
    
    applied_at = Column(DateTime, nullable=True)
    last_action_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    job = relationship("JobListing", backref="applications")
    resume = relationship("ResumeVersion")
