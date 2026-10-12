from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.application import JobApplication, ApplicationStatus
from backend.app.models.job import JobListing
from backend.app.models.settings import AutomationSettings
from backend.app.services.task_manager import task_manager
from backend.app.core.logging import log_activity

router = APIRouter(prefix="/automation", tags=["Automation Controls"])


@router.get("/status")
def get_automation_status():
    return task_manager.get_status()


@router.post("/start")
def start_automation(
    target: Optional[int] = Body(None, embed=True),
    delay: Optional[float] = Body(None, embed=True)
):
    if target is not None and not (1 <= target <= 15):
        raise HTTPException(status_code=400, detail="Target must be between 1 and 15 applications")
    if delay is not None and not (1.0 <= delay <= 5.0):
        raise HTTPException(status_code=400, detail="Delay must be between 1.0 and 5.0 seconds")

    res = task_manager.start_session(target=target, delay=delay)
    return res


@router.post("/pause")
def pause_automation():
    return task_manager.pause_session()


@router.post("/resume")
def resume_automation():
    return task_manager.resume_session()


@router.post("/stop")
def stop_automation():
    return task_manager.stop_session()


@router.post("/retry-failed")
def retry_failed(db: Session = Depends(get_db)):
    """Reset failed applications back to QUEUED for another attempt"""
    failed_apps = db.query(JobApplication).filter(JobApplication.status == ApplicationStatus.FAILED.value).all()
    count = 0
    for app in failed_apps:
        app.status = ApplicationStatus.QUEUED.value
        app.last_action = "Reset to QUEUED for retry"
        app.error_message = ""
        count += 1
    db.commit()
    log_activity(db, "ACTION", "RETRY_FAILED", f"Reset {count} failed applications to QUEUED")
    return {"success": True, "reset_count": count}


@router.post("/build-queue")
def auto_build_queue(
    target_count: Optional[int] = Body(15, embed=True),
    db: Session = Depends(get_db)
):
    """Automatically populate the queue with top-matching eligible jobs"""
    settings_obj = db.query(AutomationSettings).first() or AutomationSettings()
    min_score = settings_obj.min_match_score

    # Find jobs not yet in applications with score >= min_score
    existing_job_ids = [r[0] for r in db.query(JobApplication.job_id).all()]
    candidate_jobs = db.query(JobListing).filter(
        JobListing.id.notin_(existing_job_ids),
        JobListing.is_archived == False,
        JobListing.match_score >= min_score,
        JobListing.status.in_(["DISCOVERED", "MATCHED"])
    ).order_by(JobListing.match_score.desc()).limit(target_count).all()

    added_count = 0
    max_pos = db.query(JobApplication.queue_position).order_by(JobApplication.queue_position.desc()).first()
    curr_pos = (max_pos[0] + 1) if max_pos and max_pos[0] is not None else 1

    for job in candidate_jobs:
        app_record = JobApplication(
            job_id=job.id,
            status=ApplicationStatus.QUEUED.value,
            queue_position=curr_pos,
            last_action="Auto-queued by recommendation engine"
        )
        job.status = "QUEUED"
        db.add(app_record)
        curr_pos += 1
        added_count += 1

    db.commit()
    log_activity(db, "INFO", "BUILD_QUEUE", f"Auto-built queue with {added_count} high-match jobs")
    return {"success": True, "added_count": added_count}
