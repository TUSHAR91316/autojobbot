from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database.session import get_db
from backend.app.models.log import ActivityLog
from backend.app.models.settings import AutomationSettings
from backend.app.schemas.log import ActivityLogResponse

router = APIRouter(prefix="/logs", tags=["Activity Logs"])


@router.get("", response_model=List[ActivityLogResponse])
def get_activity_logs(
    level: Optional[str] = None,
    action: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(ActivityLog)
    if level and level != "all":
        query = query.filter(ActivityLog.level == level.upper())
    if action and action != "all":
        query = query.filter(ActivityLog.action == action)
    if search:
        query = query.filter(ActivityLog.message.ilike(f"%{search.strip()}%"))

    return query.order_by(desc(ActivityLog.created_at)).offset(skip).limit(limit).all()


@router.delete("/clear")
def clear_activity_logs(db: Session = Depends(get_db)):
    db.query(ActivityLog).delete()
    db.commit()
    return {"success": True, "message": "All activity logs cleared"}


@router.post("/prune")
def prune_logs(db: Session = Depends(get_db)):
    settings_obj = db.query(AutomationSettings).first() or AutomationSettings()
    retention_days = settings_obj.log_retention_days or 30
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    deleted = db.query(ActivityLog).filter(ActivityLog.created_at < cutoff).delete()
    db.commit()
    return {"success": True, "pruned_count": deleted}
