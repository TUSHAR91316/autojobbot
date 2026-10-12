from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database.session import get_db
from backend.app.models.application import JobApplication, ApplicationStatus
from backend.app.models.job import JobListing
from backend.app.schemas.application import JobApplicationResponse, JobApplicationUpdate
from backend.app.core.logging import log_activity

router = APIRouter(prefix="/queue", tags=["Application Queue"])


@router.get("", response_model=List[JobApplicationResponse])
def get_queue(db: Session = Depends(get_db)):
    """Retrieve items currently in queue or awaiting review"""
    active_statuses = [
        ApplicationStatus.QUEUED.value,
        ApplicationStatus.PREPARING.value,
        ApplicationStatus.AWAITING_REVIEW.value,
        ApplicationStatus.READY_TO_SUBMIT.value,
    ]
    return db.query(JobApplication).filter(
        JobApplication.status.in_(active_statuses)
    ).order_by(JobApplication.queue_position.asc()).all()


@router.get("/external", response_model=List[JobApplicationResponse])
def get_external_queue(db: Session = Depends(get_db)):
    """Retrieve items requiring manual action on an external portal"""
    return db.query(JobApplication).filter(
        JobApplication.status == ApplicationStatus.MANUAL_ACTION_REQUIRED.value
    ).order_by(desc(JobApplication.updated_at)).all()


@router.put("/{app_id}/approve")
def approve_application(app_id: int, db: Session = Depends(get_db)):
    app = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = ApplicationStatus.READY_TO_SUBMIT.value
    app.last_action = "Approved by user - ready for submission"
    db.commit()
    log_activity(db, "ACTION", "APP_APPROVED", f"Approved application #{app_id} for '{app.job.title}'")
    return {"success": True, "status": app.status}


@router.put("/{app_id}/skip")
def skip_application(app_id: int, db: Session = Depends(get_db)):
    app = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = ApplicationStatus.SKIPPED.value
    app.last_action = "Skipped by user"
    if app.job:
        app.job.status = "SKIPPED"
    db.commit()
    log_activity(db, "ACTION", "APP_SKIPPED", f"Skipped application #{app_id}")
    return {"success": True, "status": app.status}


@router.put("/{app_id}/manual-applied")
def mark_manual_applied(
    app_id: int,
    notes: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    app = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.status = ApplicationStatus.SUBMITTED.value
    app.applied_at = datetime.utcnow()
    app.last_action = "User confirmed external submission"
    if notes:
        app.manual_notes = notes
    if app.job:
        app.job.status = "APPLIED"
    db.commit()
    log_activity(db, "SUCCESS", "MANUAL_SUBMITTED", f"External application #{app_id} confirmed applied by user")
    return {"success": True, "status": app.status}


@router.put("/{app_id}/notes")
def update_application_notes(
    app_id: int,
    notes: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    app = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app.manual_notes = notes
    db.commit()
    return {"success": True, "notes": app.manual_notes}


@router.delete("/{app_id}")
def remove_from_queue(app_id: int, db: Session = Depends(get_db)):
    app = db.query(JobApplication).filter(JobApplication.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app.job:
        app.job.status = "DISCOVERED"
    db.delete(app)
    db.commit()
    log_activity(db, "INFO", "QUEUE_REMOVE", f"Removed application #{app_id} from queue")
    return {"success": True}
