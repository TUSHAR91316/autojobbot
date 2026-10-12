import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.database.session import SessionLocal
from backend.app.models.application import JobApplication, ApplicationStatus
from backend.app.models.job import JobListing
from backend.app.models.profile import CandidateProfile
from backend.app.models.settings import AutomationSettings, JobPreferences
from backend.app.core.logging import log_activity

logger = logging.getLogger("applypilot.task_manager")


class TaskManager:
    """
    Singleton thread-safe automation session manager.
    Coordinates queue processing, visible Playwright browser workflows,
    rate-limiting delays, pause/resume/stop controls, and simulation mode.
    """
    _instance: Optional["TaskManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._init_state()
        return cls._instance

    def _init_state(self):
        self.is_active: bool = False
        self.is_paused: bool = False
        self.status: str = "IDLE"  # IDLE, RUNNING, PAUSED, STOPPING
        self.session_id: Optional[str] = None
        self.target_count: int = 15
        self.delay_seconds: float = 2.0
        self.processed_count: int = 0
        self.submitted_count: int = 0
        self.manual_count: int = 0
        self.failed_count: int = 0
        self.current_job_id: Optional[int] = None
        self.current_job_title: Optional[str] = None
        self.current_action: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.ended_at: Optional[datetime] = None
        
        self._task: Optional[asyncio.Task] = None
        self._pause_event: asyncio.Event = asyncio.Event()
        self._pause_event.set()  # Not paused initially
        self._stop_requested: bool = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_active": self.is_active,
            "is_paused": self.is_paused,
            "status": self.status,
            "session_id": self.session_id,
            "target_count": self.target_count,
            "processed_count": self.processed_count,
            "submitted_count": self.submitted_count,
            "manual_count": self.manual_count,
            "failed_count": self.failed_count,
            "current_job_id": self.current_job_id,
            "current_job_title": self.current_job_title,
            "current_action": self.current_action,
            "started_at": self.started_at,
        }

    def start_session(self, target: Optional[int] = None, delay: Optional[float] = None) -> Dict[str, Any]:
        if self.is_active and not self._stop_requested:
            return {"success": False, "message": "A session is already active", "status": self.get_status()}

        db = SessionLocal()
        try:
            settings_obj = db.query(AutomationSettings).first()
            if not settings_obj:
                settings_obj = AutomationSettings()
                db.add(settings_obj)
                db.commit()

            self.target_count = target if target is not None else min(15, max(1, settings_obj.target_applications_per_session))
            self.delay_seconds = delay if delay is not None else min(5.0, max(1.0, settings_obj.delay_between_attempts_sec))
            self.session_id = f"sess_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            self.is_active = True
            self.is_paused = False
            self.status = "RUNNING"
            self._stop_requested = False
            self._pause_event.set()
            self.processed_count = 0
            self.submitted_count = 0
            self.manual_count = 0
            self.failed_count = 0
            self.current_job_id = None
            self.current_job_title = None
            self.current_action = "Initializing session"
            self.started_at = datetime.utcnow()
            self.ended_at = None

            log_activity(
                db, "INFO", "SESSION_START",
                f"Started automation session {self.session_id} with target {self.target_count} applications, {self.delay_seconds}s delay",
                details={"target": self.target_count, "delay": self.delay_seconds}
            )

            # Spawn bounded async worker task
            self._task = asyncio.create_task(self._run_session_worker())
            return {"success": True, "message": f"Session {self.session_id} started", "status": self.get_status()}
        finally:
            db.close()

    def pause_session(self) -> Dict[str, Any]:
        if not self.is_active or self.is_paused:
            return {"success": False, "message": "No running session to pause", "status": self.get_status()}
        
        self.is_paused = True
        self.status = "PAUSED"
        self._pause_event.clear()
        self.current_action = "Session paused by user"
        
        db = SessionLocal()
        try:
            log_activity(db, "ACTION", "SESSION_PAUSE", f"Paused session {self.session_id}")
        finally:
            db.close()
            
        return {"success": True, "message": "Session paused", "status": self.get_status()}

    def resume_session(self) -> Dict[str, Any]:
        if not self.is_active or not self.is_paused:
            return {"success": False, "message": "Session is not paused", "status": self.get_status()}
            
        self.is_paused = False
        self.status = "RUNNING"
        self._pause_event.set()
        self.current_action = "Resuming processing"
        
        db = SessionLocal()
        try:
            log_activity(db, "ACTION", "SESSION_RESUME", f"Resumed session {self.session_id}")
        finally:
            db.close()
            
        return {"success": True, "message": "Session resumed", "status": self.get_status()}

    def stop_session(self) -> Dict[str, Any]:
        if not self.is_active:
            return {"success": False, "message": "No active session to stop", "status": self.get_status()}
            
        self._stop_requested = True
        self.status = "STOPPING"
        self.current_action = "Stopping session"
        self._pause_event.set()  # Unblock if paused so worker can exit gracefully
        
        db = SessionLocal()
        try:
            log_activity(db, "ACTION", "SESSION_STOP", f"Immediate stop requested for session {self.session_id}")
        finally:
            db.close()
            
        return {"success": True, "message": "Stop requested", "status": self.get_status()}

    async def _run_session_worker(self):
        """Main bounded worker processing applications one by one with strict concurrency=1"""
        from backend.app.automation.simulator import process_application_workflow
        
        logger.info(f"Worker started for session {self.session_id}")
        
        try:
            while self.is_active and not self._stop_requested and self.submitted_count < self.target_count:
                # 1. Wait if paused
                await self._pause_event.wait()
                if self._stop_requested:
                    break

                # 2. Fetch next eligible queued application
                db = SessionLocal()
                app_obj = None
                settings_obj = None
                try:
                    settings_obj = db.query(AutomationSettings).first()
                    # Check failure limit
                    max_failures = settings_obj.stop_after_failures if settings_obj else 3
                    if self.failed_count >= max_failures:
                        log_activity(
                            db, "WARNING", "SESSION_LIMIT",
                            f"Stopping session: reached consecutive failure limit of {max_failures}"
                        )
                        break

                    # Retrieve next QUEUED or READY_TO_SUBMIT application
                    app_obj = db.query(JobApplication).filter(
                        JobApplication.status.in_([
                            ApplicationStatus.QUEUED.value,
                            ApplicationStatus.READY_TO_SUBMIT.value
                        ])
                    ).order_by(JobApplication.queue_position.asc(), JobApplication.id.asc()).first()
                finally:
                    db.close()

                if not app_obj:
                    # Queue exhausted
                    db = SessionLocal()
                    try:
                        log_activity(db, "INFO", "QUEUE_EXHAUSTED", "No more applications in queue to process")
                    finally:
                        db.close()
                    break

                # 3. Update telemetry
                self.current_job_id = app_obj.job_id
                self.current_job_title = app_obj.job.title if app_obj.job else f"Job #{app_obj.job_id}"
                self.current_action = f"Processing {self.current_job_title}"

                # 4. Process application through safe workflow
                res = await process_application_workflow(
                    app_id=app_obj.id,
                    session_id=self.session_id,
                    pause_event=self._pause_event,
                    check_stop=lambda: self._stop_requested
                )

                self.processed_count += 1
                outcome = res.get("outcome")
                if outcome == "SUBMITTED":
                    self.submitted_count += 1
                elif outcome == "MANUAL_ACTION_REQUIRED":
                    self.manual_count += 1
                elif outcome == "FAILED":
                    self.failed_count += 1

                # 5. Configured delay (1-5s) between eligible attempts
                if self.is_active and not self._stop_requested and self.submitted_count < self.target_count:
                    self.current_action = f"Waiting {self.delay_seconds}s before next attempt"
                    delay_slices = int(self.delay_seconds * 10)
                    for _ in range(delay_slices):
                        if self._stop_requested:
                            break
                        await self._pause_event.wait()
                        await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info("Session worker task was cancelled")
        except Exception as e:
            logger.exception(f"Unhandled error in session worker: {e}")
            db = SessionLocal()
            try:
                log_activity(db, "ERROR", "WORKER_ERROR", f"Fatal session error: {str(e)}")
            finally:
                db.close()
        finally:
            self.is_active = False
            self.is_paused = False
            self.status = "IDLE"
            self.current_action = "Session completed"
            self.ended_at = datetime.utcnow()
            
            db = SessionLocal()
            try:
                log_activity(
                    db, "SUCCESS" if self.submitted_count > 0 else "INFO", "SESSION_END",
                    f"Session {self.session_id} finished. Processed: {self.processed_count}, Submitted: {self.submitted_count}, Manual: {self.manual_count}, Failed: {self.failed_count}",
                    details={
                        "processed": self.processed_count,
                        "submitted": self.submitted_count,
                        "manual": self.manual_count,
                        "failed": self.failed_count
                    }
                )
            finally:
                db.close()


task_manager = TaskManager()
