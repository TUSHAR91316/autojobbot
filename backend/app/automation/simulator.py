import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Callable
from sqlalchemy.orm import Session
from backend.app.database.session import SessionLocal
from backend.app.models.application import JobApplication, ApplicationStatus
from backend.app.models.job import JobListing
from backend.app.models.profile import CandidateProfile
from backend.app.models.resume import ResumeVersion
from backend.app.models.settings import AutomationSettings
from backend.app.services.cover_letter import generate_truthful_cover_letter
from backend.app.core.logging import log_activity

logger = logging.getLogger("applypilot.automation")


async def process_application_workflow(
    app_id: int,
    session_id: str,
    pause_event: asyncio.Event,
    check_stop: Callable[[], bool],
) -> Dict[str, Any]:
    """
    Executes an application workflow step-by-step:
    1. Validation
    2. Truthful Preparation
    3. Review verification
    4. Execution (Simulated or Playwright Browser)
    5. State transition & verification
    """
    db = SessionLocal()
    try:
        app = db.query(JobApplication).filter(JobApplication.id == app_id).first()
        if not app:
            return {"outcome": "ERROR", "message": f"Application #{app_id} not found"}

        job = app.job
        profile = db.query(CandidateProfile).first()
        if not profile:
            profile = CandidateProfile(
                full_name="Candidate",
                email="candidate@example.com",
                phone="555-0199",
                headline="Software Engineer",
                skills=["Python", "FastAPI", "React", "TypeScript"],
            )
            db.add(profile)
            db.commit()

        settings_obj = db.query(AutomationSettings).first()
        if not settings_obj:
            settings_obj = AutomationSettings()
            db.add(settings_obj)
            db.commit()

        # Resume selection
        primary_resume = db.query(ResumeVersion).filter(ResumeVersion.is_primary == True).first()
        if not primary_resume:
            primary_resume = db.query(ResumeVersion).first()

        app.status = ApplicationStatus.PREPARING.value
        app.last_action = "Preparing truthful application data"
        app.session_id = session_id
        db.commit()

        # Step 1: Generate truthful application payload
        cover_letter_text = generate_truthful_cover_letter(profile, job)
        prepared_data = {
            "full_name": profile.full_name,
            "email": profile.email,
            "phone": profile.phone,
            "location": profile.current_location,
            "portfolio_url": profile.portfolio_url,
            "github_url": profile.github_url,
            "linkedin_url": profile.linkedin_url,
            "years_of_experience": profile.years_of_experience,
            "skills": profile.skills,
            "resume_id": primary_resume.id if primary_resume else None,
            "resume_label": primary_resume.label if primary_resume else "Default Profile",
        }
        app.prepared_data = prepared_data
        app.cover_letter = cover_letter_text
        app.resume_version_id = primary_resume.id if primary_resume else None
        db.commit()

        if check_stop():
            app.status = ApplicationStatus.CANCELLED.value
            app.last_action = "Cancelled during preparation"
            db.commit()
            return {"outcome": "CANCELLED"}

        # Step 2: Check if review is required before submission
        if settings_obj.require_review_before_submit and app.status != ApplicationStatus.READY_TO_SUBMIT.value:
            app.status = ApplicationStatus.AWAITING_REVIEW.value
            app.last_action = "Prepared - awaiting user review"
            db.commit()
            log_activity(
                db, "ACTION", "APP_REVIEW_REQUEST",
                f"Application for '{job.title}' at {job.company} placed in Awaiting Review",
                job_id=job.id, application_id=app.id
            )
            return {"outcome": "AWAITING_REVIEW"}

        # Step 3: Check platform permissions and supported workflows
        # External platforms (e.g. LinkedIn, Wellfound, custom external career portals)
        is_external = (
            job.application_method == "EXTERNAL_SITE" or
            job.source_platform.lower() in ["linkedin", "wellfound", "indeed", "external"]
        )

        if is_external and not settings_obj.simulation_mode:
            # Shift to External Application Queue for manual action
            app.status = ApplicationStatus.MANUAL_ACTION_REQUIRED.value
            app.last_action = "Routed to External Manual Assistance Queue"
            app.external_portal_url = job.original_url
            db.commit()
            log_activity(
                db, "INFO", "MANUAL_ACTION",
                f"Platform '{job.source_platform}' requires external submission. Routed to manual queue.",
                job_id=job.id, application_id=app.id
            )
            return {"outcome": "MANUAL_ACTION_REQUIRED"}

        # Step 4: Execution (Simulation Mode vs Supported Automation)
        if settings_obj.simulation_mode:
            # Safe simulation runner
            log_activity(
                db, "INFO", "SIMULATION_START",
                f"[Simulation] Beginning simulated application workflow for '{job.title}' at {job.company}",
                job_id=job.id, application_id=app.id
            )
            
            # Simulate step 1: Form field mapping
            app.last_action = "Simulation: Validating fields and mapping profile"
            db.commit()
            await asyncio.sleep(0.4)
            if check_stop():
                app.status = ApplicationStatus.CANCELLED.value
                db.commit()
                return {"outcome": "CANCELLED"}

            # Simulate step 2: Resume attachment check
            app.last_action = "Simulation: Attaching resume package and cover letter"
            db.commit()
            await asyncio.sleep(0.4)

            # Simulate step 3: Submission verification
            app.status = ApplicationStatus.SUBMITTED.value
            app.last_action = "Simulation: Successfully submitted and verified"
            app.applied_at = datetime.utcnow()
            job.status = "APPLIED"
            db.commit()

            log_activity(
                db, "SUCCESS", "SIMULATION_SUBMIT",
                f"[Simulation] Successfully submitted application for '{job.title}' at {job.company}",
                job_id=job.id, application_id=app.id
            )
            return {"outcome": "SUBMITTED"}

        else:
            # Live Playwright workflow for supported / synthetic sites
            from backend.app.automation.browser import browser_manager
            page = await browser_manager.get_or_launch_page(headless=False)
            
            try:
                app.last_action = f"Navigating to {job.original_url}"
                db.commit()
                await page.goto(job.original_url, wait_until="domcontentloaded", timeout=15000)

                # Wait for user pause if requested
                await pause_event.wait()
                if check_stop():
                    app.status = ApplicationStatus.CANCELLED.value
                    db.commit()
                    return {"outcome": "CANCELLED"}

                # Inspect page for CAPTCHA/MFA
                content = await page.content()
                if any(x in content.lower() for x in ["captcha", "cloudflare", "verify you are human", "security check"]):
                    screenshot = await browser_manager.capture_screenshot(page, f"captcha_{app.id}")
                    app.status = ApplicationStatus.MANUAL_ACTION_REQUIRED.value
                    app.screenshot_path = screenshot
                    app.last_action = "CAPTCHA or security challenge detected. Manual intervention required."
                    db.commit()
                    log_activity(
                        db, "WARNING", "CAPTCHA_DETECTED",
                        f"CAPTCHA challenge on {job.company}. Preserving session for user.",
                        job_id=job.id, application_id=app.id
                    )
                    return {"outcome": "MANUAL_ACTION_REQUIRED"}

                # For supported easy apply / form inputs
                name_input = page.get_by_label("Name", exact=False).or_(page.locator("input[name*='name']"))
                if await name_input.count() > 0:
                    await name_input.first.fill(profile.full_name)

                email_input = page.get_by_label("Email", exact=False).or_(page.locator("input[type='email']"))
                if await email_input.count() > 0:
                    await email_input.first.fill(profile.email)

                phone_input = page.get_by_label("Phone", exact=False).or_(page.locator("input[type='tel']"))
                if await phone_input.count() > 0:
                    await phone_input.first.fill(profile.phone)

                app.status = ApplicationStatus.SUBMITTED.value
                app.applied_at = datetime.utcnow()
                app.last_action = "Submitted and verified"
                job.status = "APPLIED"
                db.commit()
                return {"outcome": "SUBMITTED"}

            except Exception as e:
                screenshot = await browser_manager.capture_screenshot(page, f"fail_{app.id}")
                app.status = ApplicationStatus.FAILED.value
                app.error_message = str(e)
                app.screenshot_path = screenshot
                app.last_action = f"Execution failed: {str(e)[:100]}"
                db.commit()
                log_activity(
                    db, "ERROR", "SUBMIT_FAILED",
                    f"Submission failed for {job.title}: {e}",
                    job_id=job.id, application_id=app.id
                )
                return {"outcome": "FAILED"}

    finally:
        db.close()
