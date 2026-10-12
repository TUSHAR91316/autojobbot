import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from backend.app.core.config import LOGS_DIR
from backend.app.models.log import ActivityLog

# Setup file logger
log_file = LOGS_DIR / "applypilot.log"
file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))

app_logger = logging.getLogger("applypilot")
app_logger.setLevel(logging.INFO)
if not app_logger.handlers:
    app_logger.addHandler(file_handler)


def log_activity(
    db: Optional[Session],
    level: str,
    action: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    job_id: Optional[int] = None,
    application_id: Optional[int] = None
) -> None:
    """Log an event to both the activity_logs table and the persistent log file"""
    details = details or {}
    
    # 1. Log to file
    log_msg = f"[{action}] {message} (job_id={job_id}, app_id={application_id})"
    if level == "ERROR":
        app_logger.error(log_msg)
    elif level == "WARNING":
        app_logger.warning(log_msg)
    else:
        app_logger.info(log_msg)
        
    # 2. Persist to DB if session provided
    if db:
        try:
            entry = ActivityLog(
                level=level,
                action=action,
                message=message,
                details=details,
                job_id=job_id,
                application_id=application_id,
                created_at=datetime.utcnow()
            )
            db.add(entry)
            db.commit()
        except Exception as e:
            app_logger.error(f"Failed to persist activity log to database: {e}")
