from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from backend.app.database.session import get_db
from backend.app.models.settings import AutomationSettings, JobPreferences
from backend.app.models.job import JobListing
from backend.app.models.application import JobApplication, ApplicationStatus
from backend.app.models.log import ActivityLog
from backend.app.schemas.settings import (
    AutomationSettingsResponse, AutomationSettingsUpdate,
    JobPreferencesResponse, JobPreferencesUpdate
)
from backend.app.schemas.stats import DashboardStatsResponse, SessionProgress, LastRunDetails
from backend.app.services.task_manager import task_manager
from backend.app.services.matcher import evaluate_job_match
from backend.app.models.profile import CandidateProfile
from backend.app.services.duplicate import normalize_job_url

router = APIRouter(prefix="/settings", tags=["Settings & Dashboard Analytics"])


def get_or_create_settings(db: Session) -> AutomationSettings:
    st = db.query(AutomationSettings).first()
    if not st:
        st = AutomationSettings()
        db.add(st)
        db.commit()
        db.refresh(st)
    return st


def get_or_create_preferences(db: Session) -> JobPreferences:
    pref = db.query(JobPreferences).first()
    if not pref:
        pref = JobPreferences()
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.get("/automation", response_model=AutomationSettingsResponse)
def get_automation_settings(db: Session = Depends(get_db)):
    return get_or_create_settings(db)


@router.put("/automation", response_model=AutomationSettingsResponse)
def update_automation_settings(data: AutomationSettingsUpdate, db: Session = Depends(get_db)):
    st = get_or_create_settings(db)
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(st, field, val)
    db.commit()
    db.refresh(st)
    return st


@router.get("/preferences", response_model=JobPreferencesResponse)
def get_job_preferences(db: Session = Depends(get_db)):
    return get_or_create_preferences(db)


@router.put("/preferences", response_model=JobPreferencesResponse)
def update_job_preferences(data: JobPreferencesUpdate, db: Session = Depends(get_db)):
    pref = get_or_create_preferences(db)
    for field, val in data.model_dump(exclude_unset=True).items():
        setattr(pref, field, val)
    db.commit()
    db.refresh(pref)
    return pref


@router.get("/dashboard-stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Calculate real, live statistics strictly from local SQLite database"""
    jobs_total = db.query(JobListing).filter(JobListing.is_archived == False).count()
    jobs_matching = db.query(JobListing).filter(
        JobListing.is_archived == False,
        JobListing.match_score >= 60.0
    ).count()

    apps_prepared = db.query(JobApplication).filter(
        JobApplication.status.in_([
            ApplicationStatus.PREPARING.value,
            ApplicationStatus.READY_TO_SUBMIT.value,
            ApplicationStatus.SUBMITTED.value
        ])
    ).count()

    apps_submitted = db.query(JobApplication).filter(
        JobApplication.status == ApplicationStatus.SUBMITTED.value
    ).count()

    apps_awaiting_review = db.query(JobApplication).filter(
        JobApplication.status == ApplicationStatus.AWAITING_REVIEW.value
    ).count()

    apps_manual = db.query(JobApplication).filter(
        JobApplication.status == ApplicationStatus.MANUAL_ACTION_REQUIRED.value
    ).count()

    apps_failed = db.query(JobApplication).filter(
        JobApplication.status.in_([
            ApplicationStatus.FAILED.value,
            ApplicationStatus.CANCELLED.value
        ])
    ).count()

    # Application status distribution
    status_counts = db.query(
        JobApplication.status, func.count(JobApplication.id)
    ).group_by(JobApplication.status).all()
    status_distribution = {stat: count for stat, count in status_counts}

    # Job source distribution
    source_counts = db.query(
        JobListing.source_platform, func.count(JobListing.id)
    ).group_by(JobListing.source_platform).all()
    source_distribution = {src: count for src, count in source_counts}

    # Telemetry
    curr_status = task_manager.get_status()
    session_prog = SessionProgress(
        is_active=curr_status["is_active"],
        is_paused=curr_status["is_paused"],
        status=curr_status["status"],
        target_count=curr_status["target_count"],
        processed_count=curr_status["processed_count"],
        submitted_count=curr_status["submitted_count"],
        manual_count=curr_status["manual_count"],
        failed_count=curr_status["failed_count"],
        current_job_id=curr_status["current_job_id"],
        current_job_title=curr_status["current_job_title"],
        current_action=curr_status["current_action"],
        session_id=curr_status["session_id"],
        started_at=curr_status["started_at"]
    )

    last_run = LastRunDetails(
        session_id=task_manager.session_id,
        started_at=task_manager.started_at,
        ended_at=task_manager.ended_at,
        target=task_manager.target_count,
        submitted=task_manager.submitted_count,
        failed=task_manager.failed_count,
        manual=task_manager.manual_count,
        status="Finished" if not task_manager.is_active and task_manager.started_at else ("Running" if task_manager.is_active else "None")
    )

    recent_jobs = db.query(JobListing).filter(JobListing.is_archived == False).order_by(
        desc(JobListing.discovered_at)
    ).limit(5).all()

    recent_logs = db.query(ActivityLog).order_by(
        desc(ActivityLog.created_at)
    ).limit(6).all()

    return DashboardStatsResponse(
        jobs_discovered=jobs_total,
        jobs_matching_preferences=jobs_matching,
        applications_prepared=apps_prepared,
        applications_submitted=apps_submitted,
        applications_awaiting_review=apps_awaiting_review,
        external_manual_action_required=apps_manual,
        applications_failed_or_cancelled=apps_failed,
        status_distribution=status_distribution,
        source_distribution=source_distribution,
        session_progress=session_prog,
        last_run=last_run,
        recent_jobs=recent_jobs,
        recent_activity=recent_logs
    )


@router.post("/seed-demo")
async def seed_demo_data():
    """Mock demo data seeding has been removed."""
    return {"success": False, "message": "Mock demo data seeding has been disabled. ApplyPilot runs exclusively with real jobs."}
