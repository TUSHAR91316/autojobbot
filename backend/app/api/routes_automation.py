from typing import Optional, Dict, Any, List
from datetime import datetime
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.models.application import JobApplication, ApplicationStatus
from backend.app.models.job import JobListing
from backend.app.models.profile import CandidateProfile
from backend.app.models.resume import ResumeVersion
from backend.app.models.settings import AutomationSettings
from backend.app.services.task_manager import task_manager
from backend.app.services.cover_letter import generate_truthful_cover_letter
from backend.app.core.logging import log_activity
from backend.app.automation.browser import browser_manager
from backend.app.automation.simulator import (
    execute_live_browser_apply,
    execute_multi_tab_career_apply,
    execute_linkedin_auto_search_and_apply,
    execute_indeed_auto_search_and_apply,
    execute_naukri_auto_search_and_apply,
    execute_universal_job_search_and_apply,
)

router = APIRouter(prefix="/automation", tags=["Automation Controls"])


class DirectUrlApplyRequest(BaseModel):
    url: str
    title: Optional[str] = "Job Position"
    company: Optional[str] = "Company"


class MultiTabApplyRequest(BaseModel):
    urls: List[str]
    delay_seconds: float = 3.0
    auto_submit: bool = True


class LinkedInAutoApplyRequest(BaseModel):
    keywords: str = "Python Developer"
    location: str = "Bengaluru, Karnataka, India"
    max_jobs: int = 5
    delay_seconds: float = 4.0
    auto_submit: bool = True


class UniversalAutoApplyRequest(BaseModel):
    platform: str = "linkedin"  # linkedin, indeed, naukri, multi_portal
    keywords: str = "Python Developer"
    location: str = "Bengaluru, Karnataka, India"
    max_jobs: int = 5
    delay_seconds: float = 4.0
    auto_submit: bool = True
    non_stop: bool = False


@router.get("/status")
def get_automation_status(db: Session = Depends(get_db)):
    base_status = task_manager.get_status()
    settings_obj = db.query(AutomationSettings).first()
    b_status = browser_manager.get_status()
    base_status["simulation_mode"] = settings_obj.simulation_mode if settings_obj else False
    base_status["browser_launched"] = b_status.get("is_launched", False)
    return base_status


@router.post("/start")
async def start_automation(
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


@router.post("/toggle-simulation")
def toggle_simulation_mode(db: Session = Depends(get_db)):
    """Toggle between Live Browser Automation and Dry Run Simulation"""
    settings_obj = db.query(AutomationSettings).first()
    if not settings_obj:
        settings_obj = AutomationSettings(simulation_mode=False)
        db.add(settings_obj)
    else:
        settings_obj.simulation_mode = not settings_obj.simulation_mode

    db.commit()
    mode_str = "Simulation (Dry Run)" if settings_obj.simulation_mode else "Live Browser Automation (Real Chrome)"
    log_activity(db, "ACTION", "MODE_TOGGLE", f"Switched mode to: {mode_str}")
    return {"success": True, "simulation_mode": settings_obj.simulation_mode, "mode_label": mode_str}


@router.get("/browser/status")
def get_browser_status():
    """Check if the visible desktop browser window is currently open"""
    return browser_manager.get_status()


@router.get("/browser/sessions")
async def get_browser_sessions_status():
    """Check active login sessions (LinkedIn, Indeed, Naukri, Google) in browser profile"""
    return await browser_manager.get_saved_sessions_status()


@router.post("/browser/login")
async def open_portal_login(site: str = "linkedin"):
    """
    Launch desktop browser specifically to sign into a job portal.
    Credentials and cookies are permanently saved in ApplyPilot's local profile.
    """
    try:
        return await browser_manager.open_login_session(site=site)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open login page: {str(e)}")


@router.post("/browser/connect-cdp")
async def connect_to_running_chrome(cdp_url: str = "http://127.0.0.1:9222"):
    """
    Connect Playwright directly to an existing Google Chrome instance started with:
    chrome.exe --remote-debugging-port=9222
    """
    try:
        page = await browser_manager.connect_to_chrome_cdp(cdp_url=cdp_url)
        return {
            "success": True,
            "message": f"Successfully connected to your running Chrome instance at {cdp_url}!",
            "current_title": await page.title()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Chrome at {cdp_url}. Ensure Chrome was started with --remote-debugging-port=9222: {str(e)}")


@router.post("/browser/launch")
async def launch_desktop_browser():
    """Explicitly launch the desktop browser window for user viewing"""
    try:
        page = await browser_manager.get_or_launch_page(headless=False)
        await page.goto("http://127.0.0.1:5173", wait_until="domcontentloaded", timeout=15000)
        return {"success": True, "message": "Visible desktop browser launched successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to launch browser: {str(e)}")


@router.post("/browser/close")
async def close_desktop_browser():
    """Close the desktop browser window cleanly"""
    await browser_manager.close()
    return {"success": True, "message": "Browser closed"}


@router.post("/browser/apply-job/{job_id}")
async def apply_single_job_in_browser(job_id: int, db: Session = Depends(get_db)):
    """
    Launch visible desktop browser and apply directly to this specific job!
    Autofills candidate profile, attaches resume, and submits or prepares for review.
    """
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(CandidateProfile).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is missing. Please save profile first.")

    primary_resume = db.query(ResumeVersion).filter(ResumeVersion.is_primary == True).first()
    if not primary_resume:
        primary_resume = db.query(ResumeVersion).first()

    # Find or create application record
    app = db.query(JobApplication).filter(JobApplication.job_id == job_id).first()
    if not app:
        app = JobApplication(
            job_id=job.id,
            status=ApplicationStatus.PREPARING.value,
            last_action="User triggered direct Live Browser Apply"
        )
        db.add(app)
        db.commit()
        db.refresh(app)

    cover_letter = generate_truthful_cover_letter(profile, job)
    resume_path = primary_resume.file_path if primary_resume else None

    app.status = ApplicationStatus.PREPARING.value
    app.cover_letter = cover_letter
    app.resume_version_id = primary_resume.id if primary_resume else None
    app.last_action = f"Opening visible browser to apply at {job.original_url}"
    db.commit()

    log_activity(
        db, "ACTION", "BROWSER_APPLY_START",
        f"Launching browser to apply for '{job.title}' at {job.company}",
        job_id=job.id, application_id=app.id
    )

    result = await execute_live_browser_apply(
        url=job.original_url,
        profile=profile,
        job=job,
        resume_path=resume_path,
        cover_letter=cover_letter,
        auto_submit=True
    )

    outcome = result.get("outcome")
    steps = result.get("steps_completed", [])
    shot = result.get("screenshot", "")

    if outcome == "SUBMITTED":
        app.status = ApplicationStatus.SUBMITTED.value
        app.applied_at = datetime.utcnow()
        app.last_action = f"Submitted via Live Browser ({len(steps)} steps completed)"
        app.screenshot_path = shot
        job.status = "APPLIED"
        db.commit()
        log_activity(
            db, "SUCCESS", "BROWSER_APPLY_SUBMIT",
            f"Submitted application for '{job.title}' via Live Browser. Steps: {steps}",
            job_id=job.id, application_id=app.id
        )
    else:
        app.status = ApplicationStatus.MANUAL_ACTION_REQUIRED.value
        app.last_action = result.get("message", "Browser filled form; manual review needed")
        app.screenshot_path = shot
        app.external_portal_url = job.original_url
        db.commit()
        log_activity(
            db, "INFO", "BROWSER_APPLY_PARTIAL",
            f"Browser navigated and filled {len(steps)} fields for '{job.title}'. Session kept open.",
            job_id=job.id, application_id=app.id
        )

    return {
        "success": True,
        "application_id": app.id,
        "outcome": outcome,
        "message": result.get("message"),
        "steps_completed": steps,
        "screenshot": shot,
    }


@router.post("/browser/apply-url")
async def apply_custom_url_in_browser(
    data: DirectUrlApplyRequest,
    db: Session = Depends(get_db)
):
    """
    Launch visible desktop browser and navigate directly to ANY user-provided job URL.
    Autofills credentials, uploads active resume, and applies on behalf of the user.
    """
    url_str = data.url.strip()
    if not url_str.startswith("http"):
        url_str = "https://" + url_str

    profile = db.query(CandidateProfile).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is missing. Please save profile first.")

    primary_resume = db.query(ResumeVersion).filter(ResumeVersion.is_primary == True).first()
    if not primary_resume:
        primary_resume = db.query(ResumeVersion).first()

    # Create temporary or saved JobListing
    existing_job = db.query(JobListing).filter(JobListing.original_url == url_str).first()
    if not existing_job:
        existing_job = JobListing(
            title=data.title or "Direct URL Position",
            company=data.company or "Direct Employer",
            original_url=url_str,
            normalized_url=url_str,
            source_platform="direct_url",
            status="QUEUED",
            match_score=85.0
        )
        db.add(existing_job)
        db.commit()
        db.refresh(existing_job)

    # Create application record
    app = db.query(JobApplication).filter(JobApplication.job_id == existing_job.id).first()
    if not app:
        app = JobApplication(
            job_id=existing_job.id,
            status=ApplicationStatus.PREPARING.value,
            last_action="User triggered Direct URL Browser Apply"
        )
        db.add(app)
        db.commit()
        db.refresh(app)

    cover_letter = generate_truthful_cover_letter(profile, existing_job)
    resume_path = primary_resume.file_path if primary_resume else None

    app.status = ApplicationStatus.PREPARING.value
    app.cover_letter = cover_letter
    app.resume_version_id = primary_resume.id if primary_resume else None
    app.last_action = f"Opening visible browser to apply at {url_str}"
    db.commit()

    log_activity(
        db, "ACTION", "BROWSER_DIRECT_URL_START",
        f"Launching browser to apply to URL: {url_str}",
        job_id=existing_job.id, application_id=app.id
    )

    result = await execute_live_browser_apply(
        url=url_str,
        profile=profile,
        job=existing_job,
        resume_path=resume_path,
        cover_letter=cover_letter,
        auto_submit=True
    )

    outcome = result.get("outcome")
    steps = result.get("steps_completed", [])
    shot = result.get("screenshot", "")

    if outcome == "SUBMITTED":
        app.status = ApplicationStatus.SUBMITTED.value
        app.applied_at = datetime.utcnow()
        app.last_action = f"Submitted via Live Browser ({len(steps)} steps)"
        app.screenshot_path = shot
        existing_job.status = "APPLIED"
        db.commit()
    else:
        app.status = ApplicationStatus.MANUAL_ACTION_REQUIRED.value
        app.last_action = result.get("message", "Browser filled form; manual review needed")
        app.screenshot_path = shot
        app.external_portal_url = url_str
        db.commit()

    return {
        "success": True,
        "application_id": app.id,
        "job_id": existing_job.id,
        "outcome": outcome,
        "message": result.get("message"),
        "steps_completed": steps,
        "screenshot": shot,
    }


@router.post("/browser/apply-multi-tab")
async def apply_multi_tab_career_portals(
    data: MultiTabApplyRequest,
    db: Session = Depends(get_db)
):
    """
    Launch visible desktop browser and open multiple tabs to apply across career websites.
    Fills candidate profile details, attaches primary resume, handles screening questions,
    and observes user-configured delay between tab executions.
    """
    valid_urls = [u.strip() for u in data.urls if u and u.strip()]
    if not valid_urls:
        raise HTTPException(status_code=400, detail="No valid URLs provided")

    if len(valid_urls) > 15:
        raise HTTPException(status_code=400, detail="Maximum 15 tabs allowed per multi-tab run")

    delay = max(0.5, min(data.delay_seconds, 30.0))

    profile = db.query(CandidateProfile).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is missing. Please save profile first.")

    primary_resume = db.query(ResumeVersion).filter(ResumeVersion.is_primary == True).first()
    if not primary_resume:
        primary_resume = db.query(ResumeVersion).first()

    resume_path = primary_resume.file_path if primary_resume else None

    log_activity(
        db, "ACTION", "BROWSER_MULTI_TAB_START",
        f"Launching multi-tab browser apply across {len(valid_urls)} career URLs with {delay}s delay (Auto-Submit={data.auto_submit})"
    )

    cover_letter = (
        f"Dear Hiring Team,\n\n"
        f"I am excited to apply for this engineering opportunity. With over {int(profile.years_of_experience or 5)} years "
        f"of experience building high-performance systems and full-stack applications, I am eager to contribute.\n\n"
        f"Sincerely,\n{profile.full_name}"
    )

    result = await execute_multi_tab_career_apply(
        urls=valid_urls,
        profile=profile,
        resume_path=resume_path,
        cover_letter=cover_letter,
        delay_seconds=delay,
        auto_submit=data.auto_submit,
    )

    # Persist / record each application in DB
    for tab in result.get("tab_results", []):
        url = tab.get("url")
        outcome = tab.get("outcome")
        steps = tab.get("steps_completed", [])
        shot = tab.get("screenshot", "")

        job = db.query(JobListing).filter(JobListing.original_url == url).first()
        if not job:
            netloc = urlparse(url).netloc or "Career Portal"
            comp_name = netloc.replace("www.", "").split(".")[0].capitalize()
            job = JobListing(
                title="Engineering Role",
                company=comp_name,
                original_url=url,
                normalized_url=url,
                source_platform="career_portal",
                status="APPLIED" if outcome == "SUBMITTED" else "DISCOVERED",
                match_score=92.0,
            )
            db.add(job)
            db.commit()
            db.refresh(job)

        app = db.query(JobApplication).filter(JobApplication.job_id == job.id).first()
        if not app:
            app = JobApplication(
                job_id=job.id,
                status=ApplicationStatus.SUBMITTED.value if outcome == "SUBMITTED" else ApplicationStatus.MANUAL_ACTION_REQUIRED.value,
                last_action=f"Multi-Tab Apply: {tab.get('message', '')} ({len(steps)} steps)",
                screenshot_path=shot,
                applied_at=datetime.utcnow() if outcome == "SUBMITTED" else None,
                external_portal_url=url,
            )
            db.add(app)
        else:
            app.status = ApplicationStatus.SUBMITTED.value if outcome == "SUBMITTED" else ApplicationStatus.MANUAL_ACTION_REQUIRED.value
            app.last_action = f"Multi-Tab Apply: {tab.get('message', '')} ({len(steps)} steps)"
            app.screenshot_path = shot
            if outcome == "SUBMITTED":
                app.applied_at = datetime.utcnow()
                job.status = "APPLIED"
        db.commit()

    log_activity(
        db, "SUCCESS" if result.get("completed") else "INFO", "BROWSER_MULTI_TAB_COMPLETE",
        f"Completed multi-tab browser apply: {result.get('completed')}/{result.get('total_tabs')} tabs processed"
    )

    return {
        "success": True,
        "total_tabs": result.get("total_tabs"),
        "completed": result.get("completed"),
        "delay_seconds": delay,
        "auto_submit": data.auto_submit,
        "tab_results": result.get("tab_results", []),
    }


@router.post("/linkedin/auto-apply")
async def start_linkedin_auto_apply(
    data: LinkedInAutoApplyRequest,
    db: Session = Depends(get_db)
):
    """
    Launch visible desktop Playwright browser session, navigate to LinkedIn Jobs search,
    automatically move cursor to the 'Easy Apply' filter and click it,
    then automatically iterate through matching job cards, clicking Easy Apply,
    autofilling all questions (phone, resume, notice period, CTC, work authorization),
    and applying with user-specified delay.
    """
    profile = db.query(CandidateProfile).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is missing. Please save candidate profile first.")

    primary_resume = db.query(ResumeVersion).filter(ResumeVersion.is_primary == True).first()
    if not primary_resume:
        primary_resume = db.query(ResumeVersion).first()

    resume_path = primary_resume.file_path if primary_resume else None

    log_activity(
        db, "ACTION", "LINKEDIN_AUTOPILOT_START",
        f"Launching LinkedIn Easy Apply Auto-Pilot: '{data.keywords}' in '{data.location}' (Max {data.max_jobs} jobs, {data.delay_seconds}s delay, Auto-Submit={data.auto_submit})"
    )

    cover_letter = (
        f"Dear Hiring Team,\n\n"
        f"I am writing to express my strong interest in this position. With over {int(profile.years_of_experience or 5)} years "
        f"of experience building robust, scalable applications, I am confident in my ability to make an immediate positive impact.\n\n"
        f"Sincerely,\n{profile.full_name}"
    )

    result = await execute_linkedin_auto_search_and_apply(
        keywords=data.keywords,
        location=data.location,
        profile=profile,
        resume_path=resume_path,
        cover_letter=cover_letter,
        max_jobs=max(1, min(data.max_jobs, 25)),
        delay_seconds=max(1.0, min(data.delay_seconds, 30.0)),
        auto_submit=data.auto_submit,
    )

    return {
        "success": True,
        "result": result,
    }


@router.post("/universal/auto-apply")
async def start_universal_auto_apply(
    data: UniversalAutoApplyRequest,
    db: Session = Depends(get_db)
):
    """
    Launch visible desktop Playwright browser session across ANY job portal (LinkedIn, Indeed, Naukri, or Multi-Portal).
    Leverages persistent browser session (already logged in) to search, filter by 1-click/Easy Apply,
    and apply non-stop with user-configured anti-ban delays and cooldown breathers.
    """
    profile = db.query(CandidateProfile).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Candidate profile is missing. Please save candidate profile first.")

    primary_resume = db.query(ResumeVersion).filter(ResumeVersion.is_primary == True).first()
    if not primary_resume:
        primary_resume = db.query(ResumeVersion).first()

    resume_path = primary_resume.file_path if primary_resume else None

    log_activity(
        db, "ACTION", "UNIVERSAL_AUTOPILOT_START",
        f"Launching Universal Auto-Pilot on '{data.platform.upper()}': '{data.keywords}' in '{data.location}' (Max {data.max_jobs} jobs, {data.delay_seconds}s delay, Non-Stop={data.non_stop})"
    )

    cover_letter = (
        f"Dear Hiring Team,\n\n"
        f"I am writing to express my strong interest in this position. With over {int(profile.years_of_experience or 5)} years "
        f"of experience building robust, scalable applications, I am eager to contribute.\n\n"
        f"Sincerely,\n{profile.full_name}"
    )

    result = await execute_universal_job_search_and_apply(
        platform=data.platform,
        keywords=data.keywords,
        location=data.location,
        profile=profile,
        resume_path=resume_path,
        cover_letter=cover_letter,
        max_jobs=max(1, min(data.max_jobs, 50 if data.non_stop else 25)),
        delay_seconds=max(1.0, min(data.delay_seconds, 30.0)),
        auto_submit=data.auto_submit,
        non_stop=data.non_stop,
    )

    return {
        "success": True,
        "platform": data.platform,
        "result": result,
    }


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
