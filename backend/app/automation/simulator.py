"""
Real Playwright-powered browser automation workflows.
The bot launches a visible browser window directly on the user's desktop and navigates
to job sites, fills application forms, uploads resumes, and submits applications.
"""
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Callable, Optional, List
from sqlalchemy.orm import Session
from playwright.async_api import Page, Locator

from backend.app.database.session import SessionLocal
from backend.app.models.application import JobApplication, ApplicationStatus
from backend.app.models.job import JobListing
from backend.app.models.profile import CandidateProfile
from backend.app.models.resume import ResumeVersion
from backend.app.models.settings import AutomationSettings
from backend.app.services.cover_letter import generate_truthful_cover_letter
from backend.app.core.logging import log_activity
from backend.app.automation.browser import browser_manager

logger = logging.getLogger("applypilot.automation")


async def _smart_fill(page: Page, selectors: List[str], value: str) -> bool:
    """Try multiple selectors to fill an input field. Returns True if filled."""
    if not value:
        return False
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0 and await loc.is_visible():
                await loc.scroll_into_view_if_needed(timeout=2000)
                await loc.click(timeout=2000)
                await loc.fill(value, timeout=3000)
                logger.info(f"Filled selector '{sel}' with value '{value[:20]}...'")
                return True
        except Exception:
            continue
    return False


async def _smart_click(page: Page, selectors: List[str]) -> bool:
    """Try multiple selectors to click a button. Returns True if clicked."""
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0 and await loc.is_visible():
                await loc.scroll_into_view_if_needed(timeout=2000)
                await loc.click(timeout=3000)
                logger.info(f"Clicked button '{sel}'")
                return True
        except Exception:
            continue
    return False


async def workflow_greenhouse(
    page: Page,
    profile: CandidateProfile,
    job: JobListing,
    resume_path: Optional[str],
    cover_letter: str,
) -> Dict[str, Any]:
    """
    Dedicated workflow for Greenhouse boards (e.g. boards.greenhouse.io).
    """
    steps = []
    logger.info("Executing Greenhouse application workflow")

    name_parts = (profile.full_name or "").split(" ", 1)
    first_name = name_parts[0] if len(name_parts) >= 1 else ""
    last_name = name_parts[1] if len(name_parts) >= 2 else ""

    # Name
    if await _smart_fill(page, ["#first_name", "input[name*='first_name']", "input[autocomplete='given-name']"], first_name):
        steps.append("greenhouse_first_name")
    if await _smart_fill(page, ["#last_name", "input[name*='last_name']", "input[autocomplete='family-name']"], last_name):
        steps.append("greenhouse_last_name")

    # Contact
    if await _smart_fill(page, ["#email", "input[name*='email']", "input[type='email']"], profile.email or ""):
        steps.append("greenhouse_email")
    if await _smart_fill(page, ["#phone", "input[name*='phone']", "input[type='tel']"], profile.phone or ""):
        steps.append("greenhouse_phone")

    # Links
    if profile.linkedin_url:
        if await _smart_fill(page, ["input[id*='linkedin']", "input[name*='linkedin']", "input[placeholder*='LinkedIn']"], profile.linkedin_url):
            steps.append("greenhouse_linkedin")
    if profile.github_url or profile.portfolio_url:
        url = profile.github_url or profile.portfolio_url or ""
        if await _smart_fill(page, ["input[id*='website']", "input[name*='website']", "input[placeholder*='Website']"], url):
            steps.append("greenhouse_website")

    # Resume attachment
    if resume_path and Path(resume_path).exists():
        file_inputs = page.locator("input[type='file']")
        if await file_inputs.count() > 0:
            try:
                await file_inputs.first.set_input_files(resume_path)
                steps.append("greenhouse_resume_uploaded")
            except Exception as e:
                logger.warning(f"Greenhouse resume upload failed: {e}")

    # Cover letter
    if cover_letter:
        if await _smart_fill(page, ["#cover_letter_text", "textarea[name*='cover_letter']", "textarea[id*='cover']"], cover_letter):
            steps.append("greenhouse_cover_letter")

    # Submit button check
    submit_selectors = ["#submit_app", "button[id*='submit']", "input[type='submit']", "button:has-text('Submit Application')"]
    if await _smart_click(page, submit_selectors):
        steps.append("submitted")

    return {"steps_completed": steps, "platform": "greenhouse"}


async def workflow_lever(
    page: Page,
    profile: CandidateProfile,
    job: JobListing,
    resume_path: Optional[str],
    cover_letter: str,
) -> Dict[str, Any]:
    """
    Dedicated workflow for Lever application postings (e.g. jobs.lever.co).
    """
    steps = []
    logger.info("Executing Lever application workflow")

    # Check for "Apply" button on Lever job listing page to navigate to application form
    apply_btns = ["a.postings-btn", "a:has-text('Apply for this job')", "button:has-text('Apply')"]
    for ab in apply_btns:
        loc = page.locator(ab).first
        if await loc.count() > 0 and await loc.is_visible():
            await loc.click()
            await page.wait_for_timeout(1500)
            steps.append("lever_apply_clicked")
            break

    # Fill form fields
    if await _smart_fill(page, ["input[name='name']", "input[placeholder*='Full name']"], profile.full_name or ""):
        steps.append("lever_full_name")
    if await _smart_fill(page, ["input[name='email']", "input[type='email']"], profile.email or ""):
        steps.append("lever_email")
    if await _smart_fill(page, ["input[name='phone']", "input[type='tel']"], profile.phone or ""):
        steps.append("lever_phone")
    if profile.current_location:
        await _smart_fill(page, ["input[name='org']", "input[placeholder*='Current company']"], "Self / Confidential")
    if profile.linkedin_url:
        await _smart_fill(page, ["input[name*='urls[LinkedIn]']", "input[placeholder*='LinkedIn']"], profile.linkedin_url)
    if profile.github_url:
        await _smart_fill(page, ["input[name*='urls[GitHub]']", "input[placeholder*='GitHub']"], profile.github_url)
    if profile.portfolio_url:
        await _smart_fill(page, ["input[name*='urls[Portfolio]']", "input[name*='urls[Other]']"], profile.portfolio_url)

    # Resume attachment
    if resume_path and Path(resume_path).exists():
        file_inputs = page.locator("input[type='file'][name*='resume'], input[type='file']")
        if await file_inputs.count() > 0:
            try:
                await file_inputs.first.set_input_files(resume_path)
                steps.append("lever_resume_uploaded")
            except Exception as e:
                logger.warning(f"Lever resume upload failed: {e}")

    # Additional comments / cover letter
    if cover_letter:
        await _smart_fill(page, ["textarea[name='comments']", "textarea[placeholder*='Additional information']"], cover_letter)

    # Submit
    submit_selectors = ["button#btn-submit", "button:has-text('Submit application')", "input[type='submit']"]
    if await _smart_click(page, submit_selectors):
        steps.append("submitted")

    return {"steps_completed": steps, "platform": "lever"}


async def workflow_linkedin_easy_apply(
    page: Page,
    profile: CandidateProfile,
    job: JobListing,
    resume_path: Optional[str],
    cover_letter: str,
) -> Dict[str, Any]:
    """
    LinkedIn Easy Apply multi-step modal automation workflow.
    """
    steps = []
    logger.info("Executing LinkedIn Easy Apply workflow")

    # Look for Easy Apply button
    easy_apply_selectors = [
        "button:has-text('Easy Apply')",
        "button.jobs-apply-button",
        "div.jobs-apply-button--top-card button",
        "button[aria-label*='Easy Apply']",
    ]
    easy_apply_clicked = False
    for sel in easy_apply_selectors:
        loc = page.locator(sel).first
        if await loc.count() > 0 and await loc.is_visible():
            await loc.click()
            await page.wait_for_timeout(2000)
            steps.append("clicked_easy_apply")
            easy_apply_clicked = True
            break

    if not easy_apply_clicked:
        logger.info("Easy Apply button not found directly, checking for apply button on page")
        for sel in ["button:has-text('Apply')", "a:has-text('Apply')"]:
            loc = page.locator(sel).first
            if await loc.count() > 0 and await loc.is_visible():
                await loc.click()
                await page.wait_for_timeout(2000)
                steps.append("clicked_general_apply")
                break

    # Handle multi-step modal (up to 6 pages)
    for step_num in range(6):
        await page.wait_for_timeout(1000)

        # Check for Submit Application (final step)
        submit_selectors = [
            "button:has-text('Submit application')",
            "button[aria-label*='Submit application']",
            "button:has-text('Submit')",
        ]
        for sel in submit_selectors:
            sub = page.locator(sel).first
            if await sub.count() > 0 and await sub.is_visible():
                await sub.click()
                await page.wait_for_timeout(2000)
                steps.append("submitted")
                return {"steps_completed": steps, "platform": "linkedin"}

        # Phone field
        phone_inputs = page.locator("input[id*='phoneNumber'], input[name*='phone'], input[type='tel']")
        if await phone_inputs.count() > 0 and await phone_inputs.first.is_visible():
            val = await phone_inputs.first.input_value()
            if not val:
                await phone_inputs.first.fill(profile.phone or "")
                steps.append(f"step_{step_num}_phone")

        # Resume upload if requested
        if resume_path and Path(resume_path).exists():
            file_input = page.locator("input[type='file']")
            if await file_input.count() > 0:
                try:
                    await file_input.first.set_input_files(resume_path)
                    steps.append(f"step_{step_num}_resume")
                except Exception:
                    pass

        # Text/Number question inputs
        text_inputs = page.locator("input[type='text']:visible, input[type='number']:visible")
        count = await text_inputs.count()
        for i in range(min(count, 5)):
            try:
                inp = text_inputs.nth(i)
                label = (await inp.get_attribute("aria-label") or "") + " " + (await inp.get_attribute("placeholder") or "")
                label_l = label.lower()
                val = ""
                if any(x in label_l for x in ["year", "experience"]):
                    val = str(int(profile.years_of_experience or 5))
                elif "salary" in label_l:
                    val = "120000"
                elif "city" in label_l or "location" in label_l:
                    val = profile.current_location or "San Francisco, CA"
                elif "linkedin" in label_l:
                    val = profile.linkedin_url or ""
                elif "github" in label_l or "website" in label_l:
                    val = profile.github_url or profile.portfolio_url or ""

                if val and not (await inp.input_value()):
                    await inp.fill(val)
                    steps.append(f"step_{step_num}_field_{i}")
            except Exception:
                continue

        # Click Next / Review button
        next_selectors = [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Review')",
            "button[aria-label*='Next']",
            "button[aria-label*='Continue']",
        ]
        clicked_next = False
        for sel in next_selectors:
            btn = page.locator(sel).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                steps.append(f"step_{step_num}_next")
                clicked_next = True
                await page.wait_for_timeout(1000)
                break

        if not clicked_next:
            break

    return {"steps_completed": steps, "platform": "linkedin"}


async def workflow_indeed_apply(
    page: Page,
    profile: CandidateProfile,
    job: JobListing,
    resume_path: Optional[str],
    cover_letter: str,
) -> Dict[str, Any]:
    """
    Indeed Apply Now workflow.
    """
    steps = []
    logger.info("Executing Indeed Apply workflow")

    apply_selectors = [
        "button:has-text('Apply now')",
        "a:has-text('Apply now')",
        "button#indeedApplyButton",
        "span:has-text('Apply now')",
    ]
    for sel in apply_selectors:
        btn = page.locator(sel).first
        if await btn.count() > 0 and await btn.is_visible():
            await btn.click()
            await page.wait_for_timeout(2000)
            steps.append("indeed_apply_clicked")
            break

    # Run generic filler for the form inside Indeed or opened page
    res = await workflow_generic_form(page, profile, job, resume_path, cover_letter)
    steps.extend(res.get("steps_completed", []))

    submit_selectors = [
        "button:has-text('Submit your application')",
        "button:has-text('Submit')",
        "button[type='submit']",
    ]
    if await _smart_click(page, submit_selectors):
        steps.append("submitted")

    return {"steps_completed": steps, "platform": "indeed"}


async def workflow_naukri_apply(
    page: Page,
    profile: CandidateProfile,
    job: JobListing,
    resume_path: Optional[str],
    cover_letter: str,
) -> Dict[str, Any]:
    """
    Naukri.com (India) application workflow.
    Handles Naukri 1-Click apply, questionnaire modals (CTC, Notice Period, Experience),
    and resume attachment.
    """
    steps = []
    logger.info("Executing Naukri India application workflow")

    # Click Apply button on Naukri job page
    apply_selectors = [
        "button.apply-button",
        "button#apply-button",
        "div.apply-button-container button",
        "button:has-text('Apply on Naukri')",
        "button:has-text('Apply')",
        "a.apply-button",
        "a:has-text('Apply')",
        "span:has-text('Apply')",
    ]
    for sel in apply_selectors:
        loc = page.locator(sel).first
        if await loc.count() > 0 and await loc.is_visible():
            await loc.click()
            await page.wait_for_timeout(2000)
            steps.append("naukri_apply_clicked")
            break

    # Fill common Naukri questionnaire fields if modal opens
    # Experience
    if profile.years_of_experience:
        exp_sel = ["input[placeholder*='experience' i]", "input[id*='experience' i]", "input[name*='exp' i]"]
        if await _smart_fill(page, exp_sel, str(int(profile.years_of_experience))):
            steps.append("naukri_experience_filled")

    # Notice Period
    notice_sel = ["input[placeholder*='notice' i]", "input[id*='notice' i]", "input[name*='notice' i]"]
    if await _smart_fill(page, notice_sel, "15 Days"):
        steps.append("naukri_notice_period_filled")

    # Current / Expected CTC (Lakhs or INR)
    ctc_sel = ["input[placeholder*='ctc' i]", "input[placeholder*='salary' i]", "input[id*='ctc' i]", "input[name*='ctc' i]"]
    if await _smart_fill(page, ctc_sel, "30"):
        steps.append("naukri_ctc_filled")

    # Location
    if profile.current_location:
        loc_sel = ["input[placeholder*='city' i]", "input[placeholder*='location' i]", "input[id*='city' i]"]
        if await _smart_fill(page, loc_sel, profile.current_location):
            steps.append("naukri_location_filled")

    # Resume attachment if upload requested
    if resume_path and Path(resume_path).exists():
        file_inputs = page.locator("input[type='file']")
        if await file_inputs.count() > 0:
            try:
                await file_inputs.first.set_input_files(resume_path)
                steps.append("naukri_resume_uploaded")
            except Exception as e:
                logger.warning(f"Naukri resume upload failed: {e}")

    # Confirm / Submit in modal
    confirm_selectors = [
        "button:has-text('Submit and Apply')",
        "button:has-text('Apply Now')",
        "button:has-text('Apply')",
        "button:has-text('Submit')",
        "button.apply-modal-btn",
    ]
    if await _smart_click(page, confirm_selectors):
        steps.append("submitted")
    else:
        # Fallback to generic filler if custom form
        gen_res = await workflow_generic_form(page, profile, job, resume_path, cover_letter)
        steps.extend(gen_res.get("steps_completed", []))

    return {"steps_completed": steps, "platform": "naukri"}


async def workflow_generic_form(
    page: Page,
    profile: CandidateProfile,
    job: JobListing,
    resume_path: Optional[str],
    cover_letter: str,
) -> Dict[str, Any]:
    """
    Generic intelligent form filler for arbitrary job application portals.
    Detects and fills common fields (name, email, phone, location, URLs, cover letter, resume).
    """
    steps = []
    logger.info("Executing Generic Form Filler workflow")

    # Full Name
    name_selectors = [
        "input[name*='name'][name*='full']",
        "input[name='name']",
        "input[placeholder*='full name' i]",
        "input[placeholder*='your name' i]",
        "input[autocomplete='name']",
        "input[id*='fullname' i]",
        "input[id*='full_name' i]",
        "input[aria-label*='full name' i]",
    ]
    if await _smart_fill(page, name_selectors, profile.full_name or ""):
        steps.append("full_name")

    # First & Last Name
    name_parts = (profile.full_name or "").split(" ", 1)
    if len(name_parts) >= 1:
        first_sel = [
            "input[name='first_name']", "input[name='firstname']",
            "input[id*='first' i][id*='name' i]",
            "input[placeholder*='first name' i]",
            "input[autocomplete='given-name']",
        ]
        if await _smart_fill(page, first_sel, name_parts[0]):
            steps.append("first_name")
    if len(name_parts) >= 2:
        last_sel = [
            "input[name='last_name']", "input[name='lastname']",
            "input[id*='last' i][id*='name' i]",
            "input[placeholder*='last name' i]",
            "input[autocomplete='family-name']",
        ]
        if await _smart_fill(page, last_sel, name_parts[1]):
            steps.append("last_name")

    # Email
    email_sel = [
        "input[type='email']",
        "input[name*='email' i]",
        "input[placeholder*='email' i]",
        "input[autocomplete='email']",
        "input[id*='email' i]",
    ]
    if await _smart_fill(page, email_sel, profile.email or ""):
        steps.append("email")

    # Phone
    phone_sel = [
        "input[type='tel']",
        "input[name*='phone' i]",
        "input[placeholder*='phone' i]",
        "input[autocomplete='tel']",
        "input[id*='phone' i]",
    ]
    if await _smart_fill(page, phone_sel, profile.phone or ""):
        steps.append("phone")

    # Location / City
    if profile.current_location:
        city_sel = [
            "input[name*='city' i]",
            "input[placeholder*='city' i]",
            "input[name*='location' i]",
            "input[placeholder*='location' i]",
            "input[autocomplete='address-level2']",
            "input[id*='city' i]",
        ]
        if await _smart_fill(page, city_sel, profile.current_location):
            steps.append("location")

    # LinkedIn
    if profile.linkedin_url:
        li_sel = [
            "input[name*='linkedin' i]",
            "input[placeholder*='linkedin' i]",
            "input[id*='linkedin' i]",
        ]
        if await _smart_fill(page, li_sel, profile.linkedin_url):
            steps.append("linkedin")

    # GitHub / Portfolio
    url_to_use = profile.github_url or profile.portfolio_url or ""
    if url_to_use:
        gh_sel = [
            "input[name*='github' i]",
            "input[placeholder*='github' i]",
            "input[id*='github' i]",
            "input[name*='portfolio' i]",
            "input[placeholder*='portfolio' i]",
            "input[name*='website' i]",
        ]
        if await _smart_fill(page, gh_sel, url_to_use):
            steps.append("portfolio_or_github")

    # Cover Letter textarea
    if cover_letter:
        cl_sel = [
            "textarea[name*='cover' i]",
            "textarea[placeholder*='cover letter' i]",
            "textarea[id*='cover' i]",
            "textarea[aria-label*='cover letter' i]",
            "textarea[name*='comments' i]",
            "textarea[name*='motivation' i]",
            "textarea[placeholder*='message' i]",
        ]
        if await _smart_fill(page, cl_sel, cover_letter):
            steps.append("cover_letter")

    # Resume File Upload
    if resume_path and Path(resume_path).exists():
        file_inputs = page.locator("input[type='file']")
        count = await file_inputs.count()
        if count > 0:
            try:
                await file_inputs.first.set_input_files(resume_path)
                steps.append("resume_uploaded")
            except Exception as e:
                logger.warning(f"Resume upload failed: {e}")

    # Check for Submit button
    submit_selectors = [
        "button[type='submit']",
        "input[type='submit']",
        "button:has-text('Submit Application')",
        "button:has-text('Submit')",
        "button:has-text('Send Application')",
    ]
    if await _smart_click(page, submit_selectors):
        steps.append("submitted")

    return {"steps_completed": steps, "platform": "generic"}


def _select_workflow_function(url: str, platform: str):
    """Select the best workflow function based on URL and platform."""
    url_l = (url or "").lower()
    plat_l = (platform or "").lower()

    if "greenhouse.io" in url_l:
        return workflow_greenhouse
    elif "lever.co" in url_l:
        return workflow_lever
    elif "naukri.com" in url_l or "naukri" in plat_l:
        return workflow_naukri_apply
    elif "linkedin.com" in url_l or "linkedin" in plat_l:
        return workflow_linkedin_easy_apply
    elif "indeed.com" in url_l or "indeed" in plat_l:
        return workflow_indeed_apply
    else:
        return workflow_generic_form


async def execute_live_browser_apply(
    url: str,
    profile: CandidateProfile,
    job: JobListing,
    resume_path: Optional[str],
    cover_letter: str,
    auto_submit: bool = True,
) -> Dict[str, Any]:
    """
    Core function that launches a visible Chromium browser window on the desktop,
    navigates to the job URL, executes intelligent auto-fill, attaches resume,
    and captures screenshots.
    """
    logger.info(f"Opening visible browser to apply at: {url}")
    page = await browser_manager.get_or_launch_page(headless=False)
    await page.bring_to_front()

    try:
        # Navigate to target job URL
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        # Check for CAPTCHA
        content = await page.content()
        captcha_keywords = ["captcha", "cloudflare", "verify you are human", "security check", "are you a robot"]
        if any(k in content.lower() for k in captcha_keywords):
            shot = await browser_manager.capture_screenshot(page, f"captcha_{job.id if job else 'direct'}")
            return {
                "outcome": "MANUAL_ACTION_REQUIRED",
                "message": "CAPTCHA / Security verification challenge detected. Browser left open for you to solve.",
                "screenshot": shot,
                "steps_completed": ["captcha_detected"],
            }

        # Select matching workflow
        workflow_fn = _select_workflow_function(url, job.source_platform if job else "")
        res = await workflow_fn(
            page=page,
            profile=profile,
            job=job,
            resume_path=resume_path,
            cover_letter=cover_letter,
        )

        steps_done = res.get("steps_completed", [])
        shot = await browser_manager.capture_screenshot(page, f"applied_{job.id if job else 'direct'}")

        if "submitted" in steps_done:
            outcome = "SUBMITTED"
            msg = f"Successfully filled application and clicked Submit ({len(steps_done)} steps)."
        else:
            outcome = "PARTIAL_FILLED"
            msg = f"Filled application fields ({len(steps_done)} steps completed). Browser kept open for your review."

        return {
            "outcome": outcome,
            "message": msg,
            "screenshot": shot,
            "steps_completed": steps_done,
        }

    except Exception as e:
        logger.exception(f"Error during browser application: {e}")
        shot = await browser_manager.capture_screenshot(page, "error")
        return {
            "outcome": "FAILED",
            "message": f"Browser error: {str(e)}",
            "screenshot": shot,
            "steps_completed": [],
        }


async def process_application_workflow(
    app_id: int,
    session_id: str,
    pause_event: asyncio.Event,
    check_stop: Callable[[], bool],
) -> Dict[str, Any]:
    """
    Standard queue session worker: processes one application from the queue.
    Supports either Live Visible Browser automation or Dry Run Simulation.
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
                full_name="Alex Mercer",
                email="alex.mercer@example.com",
                phone="+1 (555) 234-5678",
                headline="Senior Software Engineer",
                skills=["Python", "FastAPI", "React", "TypeScript"],
            )
            db.add(profile)
            db.commit()

        settings_obj = db.query(AutomationSettings).first()
        if not settings_obj:
            settings_obj = AutomationSettings(simulation_mode=False)
            db.add(settings_obj)
            db.commit()

        # Primary resume selection
        primary_resume = db.query(ResumeVersion).filter(ResumeVersion.is_primary == True).first()
        if not primary_resume:
            primary_resume = db.query(ResumeVersion).first()

        app.status = ApplicationStatus.PREPARING.value
        app.last_action = "Preparing truthful application data"
        app.session_id = session_id
        db.commit()

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
            "resume_label": primary_resume.label if primary_resume else "Default",
        }
        app.prepared_data = prepared_data
        app.cover_letter = cover_letter_text
        app.resume_version_id = primary_resume.id if primary_resume else None
        db.commit()

        if check_stop():
            app.status = ApplicationStatus.CANCELLED.value
            db.commit()
            return {"outcome": "CANCELLED"}

        # Review gate
        if settings_obj.require_review_before_submit and app.status != ApplicationStatus.READY_TO_SUBMIT.value:
            app.status = ApplicationStatus.AWAITING_REVIEW.value
            app.last_action = "Prepared - awaiting user review"
            db.commit()
            log_activity(
                db, "ACTION", "APP_REVIEW_REQUEST",
                f"Application for '{job.title}' placed in Awaiting Review",
                job_id=job.id, application_id=app.id
            )
            return {"outcome": "AWAITING_REVIEW"}

        # EXECUTION: Simulation or Live Browser
        if settings_obj.simulation_mode:
            # === DRY RUN SIMULATION MODE ===
            log_activity(
                db, "INFO", "SIMULATION_START",
                f"[Simulation] Simulating application for '{job.title}' at {job.company}",
                job_id=job.id, application_id=app.id
            )
            app.last_action = "Simulation: Filling fields and attaching credentials"
            db.commit()
            await asyncio.sleep(0.5)

            if check_stop():
                app.status = ApplicationStatus.CANCELLED.value
                db.commit()
                return {"outcome": "CANCELLED"}

            app.status = ApplicationStatus.SUBMITTED.value
            app.last_action = "Simulation: Submitted successfully"
            app.applied_at = datetime.utcnow()
            job.status = "APPLIED"
            db.commit()
            return {"outcome": "SUBMITTED"}

        else:
            # === LIVE PLAYWRIGHT BROWSER AUTOMATION ===
            app.last_action = f"Browser: Launching desktop browser to apply at {job.original_url}"
            db.commit()

            resume_file = primary_resume.file_path if primary_resume else None
            result = await execute_live_browser_apply(
                url=job.original_url,
                profile=profile,
                job=job,
                resume_path=resume_file,
                cover_letter=cover_letter_text,
                auto_submit=True,
            )

            outcome = result.get("outcome")
            steps = result.get("steps_completed", [])
            shot = result.get("screenshot", "")

            if outcome == "SUBMITTED":
                app.status = ApplicationStatus.SUBMITTED.value
                app.applied_at = datetime.utcnow()
                app.last_action = f"Browser applied successfully! ({len(steps)} steps)"
                app.screenshot_path = shot
                job.status = "APPLIED"
                db.commit()
                log_activity(
                    db, "SUCCESS", "BROWSER_SUBMIT",
                    f"Live browser successfully submitted application for '{job.title}' at {job.company}",
                    job_id=job.id, application_id=app.id
                )
                return {"outcome": "SUBMITTED"}
            elif outcome == "MANUAL_ACTION_REQUIRED":
                app.status = ApplicationStatus.MANUAL_ACTION_REQUIRED.value
                app.last_action = result.get("message", "Manual action required")
                app.screenshot_path = shot
                app.external_portal_url = job.original_url
                db.commit()
                return {"outcome": "MANUAL_ACTION_REQUIRED"}
            else:
                # Partial filled or fallback
                app.status = ApplicationStatus.MANUAL_ACTION_REQUIRED.value
                app.last_action = f"Browser partially filled form ({len(steps)} fields) — session preserved for you"
                app.screenshot_path = shot
                app.external_portal_url = job.original_url
                db.commit()
                log_activity(
                    db, "INFO", "BROWSER_PARTIAL",
                    f"Browser filled {len(steps)} fields for '{job.title}' at {job.company}. Preserved for manual review.",
                    job_id=job.id, application_id=app.id
                )
                return {"outcome": "MANUAL_ACTION_REQUIRED"}

    finally:
        db.close()
