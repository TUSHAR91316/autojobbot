from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from backend.app.database.session import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), default="INFO", index=True)  # INFO, WARNING, ERROR, ACTION, SUCCESS
    action = Column(String(100), index=True)  # SESSION_START, DISCOVERY, MATCH, PREPARE, REVIEW, SUBMIT, MANUAL, ERROR
    message = Column(Text, nullable=False)
    details = Column(JSON, default=dict)
    job_id = Column(Integer, nullable=True, index=True)
    application_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
