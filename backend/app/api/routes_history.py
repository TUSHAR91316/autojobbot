from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from backend.app.database.session import get_db
from backend.app.models.application import JobApplication
from backend.app.models.job import JobListing
from backend.app.schemas.application import JobApplicationResponse
from backend.app.providers.csv_provider import export_history_to_csv

router = APIRouter(prefix="/history", tags=["Application History"])


@router.get("", response_model=List[JobApplicationResponse])
def get_history(
    status: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(JobApplication).join(JobApplication.job)

    if status and status != "all":
        query = query.filter(JobApplication.status == status)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(JobListing.title.ilike(term), JobListing.company.ilike(term)))

    return query.order_by(desc(JobApplication.updated_at)).offset(skip).limit(limit).all()


@router.get("/export/csv")
def export_history(db: Session = Depends(get_db)):
    apps = db.query(JobApplication).join(JobApplication.job).all()
    history_records = []
    for a in apps:
        history_records.append({
            "application_id": a.id,
            "job_title": a.job.title if a.job else "Unknown",
            "company": a.job.company if a.job else "Unknown",
            "source_platform": a.job.source_platform if a.job else "Unknown",
            "match_score": a.job.match_score if a.job else 0,
            "status": a.status,
            "last_action": a.last_action,
            "applied_at": a.applied_at.isoformat() if a.applied_at else "",
            "original_url": a.job.original_url if a.job else "",
        })
    csv_data = export_history_to_csv(history_records)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applypilot_history.csv"}
    )
