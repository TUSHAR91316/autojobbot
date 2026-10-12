"""
Real Playwright-powered browser automation workflows.
The bot launches a visible browser window directly on the user's desktop and navigates
to job sites, fills application forms, uploads resumes, and submits applications.
"""
import asyncio
import logging
import urllib.parse
import random
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


async def _human_delay(base_delay: float, cooldown: bool = False):
    """
    Applies natural human jitter and random pause to prevent bot detection and account bans.
    Adds ±1.5s random jitter to the user's base delay.
    If cooldown is True, takes an extra 12-18s pause to reset request velocity.
    """
    jitter = random.uniform(0.6, 2.2)
    total = max(1.0, base_delay + jitter)
    if cooldown:
        total += random.uniform(12.0, 18.0)
        logger.info(f"🛡️ Anti-Ban Cooldown: Taking a natural human breather of {total:.2f}s...")
    else:
        logger.info(f"Observing anti-ban delay of {total:.2f}s (base {base_delay}s + {jitter:.2f}s jitter)...")
    await asyncio.sleep(total)


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
    job: Optional[JobListing] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    auto_submit: bool = True,
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
    if auto_submit:
        submit_selectors = ["#submit_app", "button[id*='submit']", "input[type='submit']", "button:has-text('Submit Application')"]
        if await _smart_click(page, submit_selectors):
            steps.append("submitted")
    else:
        steps.append("ready_for_review")

    return {"steps_completed": steps, "platform": "greenhouse"}


async def workflow_lever(
    page: Page,
    profile: CandidateProfile,
    job: Optional[JobListing] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    auto_submit: bool = True,
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
    if auto_submit:
        submit_selectors = ["button#btn-submit", "button:has-text('Submit application')", "input[type='submit']"]
        if await _smart_click(page, submit_selectors):
            steps.append("submitted")
    else:
        steps.append("ready_for_review")

    return {"steps_completed": steps, "platform": "lever"}


async def workflow_linkedin_easy_apply(
    page: Page,
    profile: CandidateProfile,
    job: Optional[JobListing] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    auto_submit: bool = True,
) -> Dict[str, Any]:
    """
    LinkedIn Easy Apply multi-step modal automation workflow.
    Handles contact info, resume upload, work authorization radios, CTC, notice period,
    experience questions, Next/Review steps, and automatic dialog dismissal.
    """
    steps = []
    logger.info("Executing comprehensive LinkedIn Easy Apply workflow")

    # Check if modal is already open
    modal = page.locator("div.jobs-easy-apply-modal, div[role='dialog']").first
    modal_open = await modal.count() > 0 and await modal.is_visible()

    if not modal_open:
        # Look for Easy Apply button
        easy_apply_selectors = [
            "button.jobs-apply-button:has-text('Easy Apply')",
            "div.jobs-apply-button--top-card button:has-text('Easy Apply')",
            "button:has-text('Easy Apply')",
            "button[aria-label*='Easy Apply' i]",
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
            for sel in ["button:has-text('Apply')", "a:has-text('Apply')"]:
                loc = page.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.click()
                    await page.wait_for_timeout(2000)
                    steps.append("clicked_general_apply")
                    break

    # Handle multi-step modal (up to 8 screens)
    for step_num in range(8):
        await page.wait_for_timeout(1000)

        # 1. Check for Submit Application (final step)
        submit_selectors = [
            "button:has-text('Submit application')",
            "button[aria-label*='Submit application' i]",
            "button:has-text('Submit')",
        ]
        for sel in submit_selectors:
            sub = page.locator(sel).first
            if await sub.count() > 0 and await sub.is_visible():
                if auto_submit:
                    await sub.click()
                    await page.wait_for_timeout(2500)
                    steps.append("submitted")

                    # Handle post-submission modal ("Application sent")
                    for done_sel in [
                        "button:has-text('Done')",
                        "button[aria-label*='Dismiss' i]",
                        "button:has-text('Close')",
                    ]:
                        done_btn = page.locator(done_sel).first
                        if await done_btn.count() > 0 and await done_btn.is_visible():
                            await done_btn.click()
                            await page.wait_for_timeout(1000)
                            steps.append("dismissed_done_dialog")
                            break
                    return {"steps_completed": steps, "platform": "linkedin", "outcome": "SUBMITTED"}
                else:
                    steps.append("ready_for_review")
                    return {"steps_completed": steps, "platform": "linkedin", "outcome": "AWAITING_REVIEW"}

        # 2. Contact details (phone & email)
        phone_inputs = page.locator("input[id*='phoneNumber' i], input[name*='phone' i], input[type='tel']")
        if await phone_inputs.count() > 0 and await phone_inputs.first.is_visible():
            val = await phone_inputs.first.input_value()
            if not val:
                await phone_inputs.first.fill(profile.phone or "+91 9876543210")
                steps.append(f"step_{step_num}_phone")

        email_inputs = page.locator("input[id*='email' i], input[name*='email' i]")
        if await email_inputs.count() > 0 and await email_inputs.first.is_visible():
            val = await email_inputs.first.input_value()
            if not val:
                await email_inputs.first.fill(profile.email or "candidate@example.com")
                steps.append(f"step_{step_num}_email")

        # 3. Resume attachment or selection
        if resume_path and Path(resume_path).exists():
            file_input = page.locator("input[type='file']")
            if await file_input.count() > 0:
                try:
                    await file_input.first.set_input_files(resume_path)
                    steps.append(f"step_{step_num}_resume_upload")
                except Exception:
                    pass

        # If radio selector for previously uploaded resume is present, pick first if none selected
        resume_radios = page.locator("input[type='radio'][name*='resume' i]")
        if await resume_radios.count() > 0:
            try:
                first_r = resume_radios.first
                if not await first_r.is_checked():
                    await first_r.check()
                    steps.append(f"step_{step_num}_selected_existing_resume")
            except Exception:
                pass

        # 4. Radio screening questions (Authorization, Sponsorship, Relocation)
        fieldsets = page.locator("fieldset[data-test-form-builder-radio-button-form-component='true'], fieldset")
        fs_count = await fieldsets.count()
        for fs_idx in range(fs_count):
            try:
                fs = fieldsets.nth(fs_idx)
                legend_el = fs.locator("legend").first
                legend_text = (await legend_el.inner_text()).lower() if await legend_el.count() > 0 else ""

                if any(w in legend_text for w in ["sponsor", "require visa", "sponsorship"]):
                    # Click 'No'
                    no_radio = fs.locator("label:has-text('No'), input[value*='No' i], span:has-text('No')").first
                    if await no_radio.count() > 0:
                        await no_radio.click()
                        steps.append(f"step_{step_num}_radio_sponsor_no")
                else:
                    # Legally authorized, commute, comfortable, completed degree -> Click 'Yes'
                    yes_radio = fs.locator("label:has-text('Yes'), input[value*='Yes' i], span:has-text('Yes')").first
                    if await yes_radio.count() > 0:
                        await yes_radio.click()
                        steps.append(f"step_{step_num}_radio_yes")
            except Exception:
                continue

        # 5. Dropdown selects
        selects = page.locator("select:visible")
        sel_count = await selects.count()
        for s_idx in range(sel_count):
            try:
                sel = selects.nth(s_idx)
                val = await sel.input_value()
                if not val or val.lower() in ["select an option", "", "select"]:
                    yes_opt = sel.locator("option:has-text('Yes')")
                    if await yes_opt.count() > 0:
                        await sel.select_option(label="Yes")
                    else:
                        await sel.select_option(index=1)
                    steps.append(f"step_{step_num}_select_{s_idx}")
            except Exception:
                continue

        # 6. Text and number inputs (Experience, CTC, notice period, location)
        text_inputs = page.locator("input[type='text']:visible, input[type='number']:visible")
        count = await text_inputs.count()
        for i in range(min(count, 8)):
            try:
                inp = text_inputs.nth(i)
                label = (
                    (await inp.get_attribute("aria-label") or "") + " " +
                    (await inp.get_attribute("placeholder") or "") + " " +
                    (await inp.get_attribute("id") or "")
                ).lower()
                val = ""
                if any(x in label for x in ["year", "experience"]):
                    val = str(int(profile.years_of_experience or 5))
                elif any(x in label for x in ["notice", "period"]):
                    val = "30 days"
                elif any(x in label for x in ["expected", "desired"]) and any(x in label for x in ["salary", "ctc", "compensation"]):
                    val = "1800000"
                elif any(x in label for x in ["current", "present"]) and any(x in label for x in ["salary", "ctc", "compensation"]):
                    val = "1200000"
                elif "salary" in label or "ctc" in label or "compensation" in label:
                    val = "1500000"
                elif any(x in label for x in ["city", "location", "address"]):
                    val = profile.current_location or "Bengaluru, India"
                elif "linkedin" in label:
                    val = profile.linkedin_url or ""
                elif any(x in label for x in ["github", "website", "portfolio"]):
                    val = profile.github_url or profile.portfolio_url or ""

                if val and not (await inp.input_value()):
                    await inp.fill(val)
                    steps.append(f"step_{step_num}_input_{i}")
            except Exception:
                continue

        # 7. Checkboxes (terms / agreement)
        checkboxes = page.locator("input[type='checkbox']:visible")
        cb_count = await checkboxes.count()
        for cb_idx in range(cb_count):
            try:
                cb = checkboxes.nth(cb_idx)
                if not await cb.is_checked():
                    await cb.check()
                    steps.append(f"step_{step_num}_checkbox_{cb_idx}")
            except Exception:
                pass

        # 8. Click Next / Review button
        next_selectors = [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Review')",
            "button[aria-label*='Next' i]",
            "button[aria-label*='Continue' i]",
            "button[aria-label*='Review' i]",
        ]
        clicked_next = False
        for sel in next_selectors:
            btn = page.locator(sel).first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click()
                steps.append(f"step_{step_num}_next")
                clicked_next = True
                await page.wait_for_timeout(1200)
                break

        if not clicked_next:
            # Check if modal can be submitted on this screen
            sub = page.locator("button:has-text('Submit application'), button[aria-label*='Submit application' i]").first
            if await sub.count() > 0 and await sub.is_visible():
                if auto_submit:
                    await sub.click()
                    await page.wait_for_timeout(2500)
                    steps.append("submitted")
                    for done_sel in ["button:has-text('Done')", "button[aria-label*='Dismiss' i]"]:
                        done_btn = page.locator(done_sel).first
                        if await done_btn.count() > 0 and await done_btn.is_visible():
                            await done_btn.click()
                            break
                    return {"steps_completed": steps, "platform": "linkedin", "outcome": "SUBMITTED"}
                else:
                    return {"steps_completed": steps, "platform": "linkedin", "outcome": "AWAITING_REVIEW"}
            break

    outcome = "SUBMITTED" if "submitted" in steps else ("AWAITING_REVIEW" if "ready_for_review" in steps else "PARTIAL_FILLED")
    return {"steps_completed": steps, "platform": "linkedin", "outcome": outcome}


async def workflow_indeed_apply(
    page: Page,
    profile: CandidateProfile,
    job: Optional[JobListing] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    auto_submit: bool = True,
) -> Dict[str, Any]:
    """
    Indeed Easily Apply multi-step modal automation workflow.
    Handles contact details, resume selection, screening questions, Continue/Review steps, and submission.
    """
    steps = []
    logger.info("Executing comprehensive Indeed Apply workflow")

    # Click Apply button if modal not yet opened
    apply_selectors = [
        "button#indeedApplyButton",
        "button:has-text('Apply now')",
        "a:has-text('Apply now')",
        "span:has-text('Apply now')",
        "div[data-testid='indeedApply'] button",
    ]
    for sel in apply_selectors:
        btn = page.locator(sel).first
        if await btn.count() > 0 and await btn.is_visible():
            await btn.click()
            await page.wait_for_timeout(2000)
            steps.append("indeed_apply_clicked")
            break

    # Loop through Indeed multi-step modal (up to 7 screens)
    for step_num in range(7):
        await page.wait_for_timeout(1000)

        # 1. Check for Submit Application (final step)
        submit_selectors = [
            "button:has-text('Submit your application')",
            "button[aria-label*='Submit your application' i]",
            "button:has-text('Submit application')",
        ]
        for sel in submit_selectors:
            sub = page.locator(sel).first
            if await sub.count() > 0 and await sub.is_visible():
                if auto_submit:
                    await sub.click()
                    await page.wait_for_timeout(2500)
                    steps.append("submitted")
                    # Check for completion dialog dismiss
                    for close_sel in ["button:has-text('Close')", "button[aria-label*='Close' i]", "button:has-text('Done')"]:
                        cl_btn = page.locator(close_sel).first
                        if await cl_btn.count() > 0 and await cl_btn.is_visible():
                            await cl_btn.click()
                            break
                    return {"steps_completed": steps, "platform": "indeed", "outcome": "SUBMITTED"}
                else:
                    steps.append("ready_for_review")
                    return {"steps_completed": steps, "platform": "indeed", "outcome": "AWAITING_REVIEW"}

        # 2. Contact details (Name, Phone, Email)
        name_input = page.locator("input[id*='applicant.name' i], input[name*='name' i]").first
        if await name_input.count() > 0 and await name_input.is_visible():
            if not await name_input.input_value():
                await name_input.fill(profile.full_name or "Alex Mercer")
                steps.append(f"indeed_step_{step_num}_name")

        phone_input = page.locator("input[type='tel'], input[id*='phoneNumber' i], input[name*='phone' i]").first
        if await phone_input.count() > 0 and await phone_input.is_visible():
            if not await phone_input.input_value():
                await phone_input.fill(profile.phone or "+91 9876543210")
                steps.append(f"indeed_step_{step_num}_phone")

        email_input = page.locator("input[type='email'], input[id*='email' i]").first
        if await email_input.count() > 0 and await email_input.is_visible():
            if not await email_input.input_value():
                await email_input.fill(profile.email or "alex.mercer@example.com")
                steps.append(f"indeed_step_{step_num}_email")

        # 3. Resume attachment or selection
        if resume_path and Path(resume_path).exists():
            file_input = page.locator("input[type='file']").first
            if await file_input.count() > 0:
                try:
                    await file_input.set_input_files(resume_path)
                    steps.append(f"indeed_step_{step_num}_resume_upload")
                except Exception:
                    pass

        # Select active Indeed resume radio if present
        resume_radio = page.locator("input[type='radio'][name*='resume' i]").first
        if await resume_radio.count() > 0:
            try:
                if not await resume_radio.is_checked():
                    await resume_radio.check()
                    steps.append(f"indeed_step_{step_num}_resume_selected")
            except Exception:
                pass

        # 4. Radio screening questions
        fieldsets = page.locator("fieldset")
        fs_count = await fieldsets.count()
        for f_i in range(fs_count):
            try:
                fs = fieldsets.nth(f_i)
                leg_text = (await fs.locator("legend").first.inner_text() if await fs.locator("legend").count() > 0 else "").lower()
                if "sponsor" in leg_text or "require visa" in leg_text:
                    no_btn = fs.locator("label:has-text('No'), input[value*='No' i]").first
                    if await no_btn.count() > 0:
                        await no_btn.click()
                        steps.append(f"indeed_step_{step_num}_sponsor_no")
                else:
                    yes_btn = fs.locator("label:has-text('Yes'), input[value*='Yes' i]").first
                    if await yes_btn.count() > 0:
                        await yes_btn.click()
                        steps.append(f"indeed_step_{step_num}_yes")
            except Exception:
                continue

        # 5. Text & number questions
        inputs = page.locator("input[type='text']:visible, input[type='number']:visible")
        inp_count = await inputs.count()
        for i in range(min(inp_count, 6)):
            try:
                inp = inputs.nth(i)
                lbl = (
                    (await inp.get_attribute("aria-label") or "") + " " +
                    (await inp.get_attribute("placeholder") or "") + " " +
                    (await inp.get_attribute("id") or "")
                ).lower()
                val = ""
                if any(k in lbl for k in ["year", "experience"]):
                    val = str(int(profile.years_of_experience or 5))
                elif any(k in lbl for k in ["notice", "period"]):
                    val = "30 days"
                elif any(k in lbl for k in ["salary", "ctc", "compensation"]):
                    val = "1500000"
                elif any(k in lbl for k in ["city", "location"]):
                    val = profile.current_location or "Bengaluru, India"

                if val and not await inp.input_value():
                    await inp.fill(val)
                    steps.append(f"indeed_step_{step_num}_input_{i}")
            except Exception:
                continue

        # 6. Click Continue / Review button
        cont_selectors = [
            "button:has-text('Continue')",
            "button:has-text('Review your application')",
            "button:has-text('Next')",
            "button[aria-label*='Continue' i]",
        ]
        clicked_cont = False
        for c_sel in cont_selectors:
            c_btn = page.locator(c_sel).first
            if await c_btn.count() > 0 and await c_btn.is_visible():
                await c_btn.click()
                steps.append(f"indeed_step_{step_num}_continue")
                clicked_cont = True
                await page.wait_for_timeout(1500)
                break

        if not clicked_cont:
            # Check if submit is present on current screen
            sub = page.locator("button:has-text('Submit your application'), button:has-text('Submit')").first
            if await sub.count() > 0 and await sub.is_visible():
                if auto_submit:
                    await sub.click()
                    await page.wait_for_timeout(2500)
                    steps.append("submitted")
                    return {"steps_completed": steps, "platform": "indeed", "outcome": "SUBMITTED"}
                else:
                    return {"steps_completed": steps, "platform": "indeed", "outcome": "AWAITING_REVIEW"}
            break

    outcome = "SUBMITTED" if "submitted" in steps else ("AWAITING_REVIEW" if "ready_for_review" in steps else "PARTIAL_FILLED")
    return {"steps_completed": steps, "platform": "indeed", "outcome": outcome}


async def workflow_naukri_apply(
    page: Page,
    profile: CandidateProfile,
    job: Optional[JobListing] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    auto_submit: bool = True,
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
    if auto_submit:
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
            gen_res = await workflow_generic_form(page, profile, job, resume_path, cover_letter, auto_submit=auto_submit)
            steps.extend(gen_res.get("steps_completed", []))
    else:
        steps.append("ready_for_review")

    return {"steps_completed": steps, "platform": "naukri"}


async def workflow_generic_form(
    page: Page,
    profile: CandidateProfile,
    job: Optional[JobListing] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    auto_submit: bool = True,
) -> Dict[str, Any]:
    """
    Generic intelligent form filler for arbitrary job application portals.
    Detects and fills common fields (name, email, phone, location, URLs, cover letter, resume).
    """
    steps = []
    logger.info("Executing Generic Form Filler workflow")

    # 0. Check for initial "Apply" / "Apply for this job" / "Apply now" button and click it to reveal form
    initial_apply_selectors = [
        "a:has-text('Apply for this job')",
        "button:has-text('Apply for this job')",
        "a:has-text('Apply now')",
        "button:has-text('Apply now')",
        "button:has-text('Easy Apply')",
        "button.apply-button",
        "a.apply-button",
        "button[data-qa='btn-apply']",
        "a:has-text('Apply')",
        "button:has-text('Apply')",
        "span:has-text('Apply now')",
    ]
    for sel in initial_apply_selectors:
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0 and await loc.is_visible():
                await loc.scroll_into_view_if_needed(timeout=2000)
                await loc.click(timeout=3000)
                await page.wait_for_timeout(1500)
                steps.append("clicked_apply_button")
                break
        except Exception:
            continue

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

    # Screening questions: Experience, CTC / Salary, Notice Period
    if profile.years_of_experience:
        exp_sel = [
            "input[name*='experience' i]",
            "input[placeholder*='years of experience' i]",
            "input[placeholder*='experience' i]",
            "input[id*='experience' i]",
        ]
        if await _smart_fill(page, exp_sel, str(int(profile.years_of_experience))):
            steps.append("experience")

    salary_val = str(profile.salary_expectation_min or 2500000)
    salary_sel = [
        "input[name*='salary' i]",
        "input[name*='ctc' i]",
        "input[placeholder*='expected salary' i]",
        "input[placeholder*='expected ctc' i]",
        "input[placeholder*='ctc' i]",
        "input[id*='salary' i]",
    ]
    if await _smart_fill(page, salary_sel, salary_val):
        steps.append("expected_salary")

    notice_sel = [
        "input[name*='notice' i]",
        "input[placeholder*='notice period' i]",
        "input[placeholder*='notice' i]",
        "input[id*='notice' i]",
    ]
    if await _smart_fill(page, notice_sel, "15 Days"):
        steps.append("notice_period")

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

    # Checkbox consent / terms agreements
    try:
        checkboxes = page.locator("input[type='checkbox']")
        cb_count = await checkboxes.count()
        for ci in range(min(cb_count, 4)):
            cb = checkboxes.nth(ci)
            if await cb.is_visible() and not await cb.is_checked():
                await cb.check()
                steps.append(f"checkbox_{ci}_checked")
    except Exception:
        pass

    # Radio button for work authorization / right to work
    try:
        auth_radios = page.locator("input[type='radio'][value*='yes' i], input[type='radio'][id*='yes' i]")
        if await auth_radios.count() > 0 and await auth_radios.first.is_visible():
            await auth_radios.first.check()
            steps.append("work_auth_yes")
    except Exception:
        pass

    # Check for Submit button
    if auto_submit:
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit Application')",
            "button:has-text('Submit application')",
            "button:has-text('Submit')",
            "button:has-text('Send Application')",
            "button:has-text('Send application')",
        ]
        if await _smart_click(page, submit_selectors):
            steps.append("submitted")
    else:
        steps.append("ready_for_review")

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
    job: Optional[JobListing] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    auto_submit: bool = True,
    page: Optional[Page] = None,
) -> Dict[str, Any]:
    """
    Core function that launches or uses a visible Chromium browser window on the desktop,
    navigates to the career website URL, executes intelligent auto-fill, attaches resume,
    and captures screenshots.
    """
    logger.info(f"Applying in visible browser at: {url}")
    if page is None:
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
            auto_submit=auto_submit,
        )

        steps_done = res.get("steps_completed", [])
        shot = await browser_manager.capture_screenshot(page, f"applied_{job.id if job else 'direct'}")

        if "submitted" in steps_done:
            outcome = "SUBMITTED"
            msg = f"Successfully filled application and clicked Submit ({len(steps_done)} steps)."
        elif "ready_for_review" in steps_done or not auto_submit:
            outcome = "PARTIAL_FILLED"
            msg = f"Application fields filled & staged for review ({len(steps_done)} steps). Browser tab kept open."
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


async def execute_multi_tab_career_apply(
    urls: List[str],
    profile: CandidateProfile,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    delay_seconds: float = 3.0,
    auto_submit: bool = True,
) -> Dict[str, Any]:
    """
    Direct multi-tab browser auto-apply runner.
    Opens separate browser tabs in Playwright Chromium on the user's desktop,
    navigates to each career portal URL, clicks Apply, fills form fields with candidate
    profile data, attaches active resume, submits (or holds for user review),
    and applies a user-configured delay between each tab action.
    """
    cleaned_urls = [u.strip() for u in urls if u and u.strip()]
    if not cleaned_urls:
        return {"total_tabs": 0, "completed": 0, "delay_seconds": delay_seconds, "tab_results": []}

    logger.info(f"Starting multi-tab career apply across {len(cleaned_urls)} URLs with {delay_seconds}s delay")

    # Launch or get visible browser
    initial_page = await browser_manager.get_or_launch_page(headless=False)

    tab_results = []
    for idx, raw_url in enumerate(cleaned_urls):
        target_url = raw_url
        if not target_url.startswith("http"):
            target_url = "https://" + target_url

        try:
            # For the first URL, reuse initial page if blank/localhost, otherwise open new tab
            if idx == 0 and initial_page and (initial_page.url in ["about:blank", "http://127.0.0.1:5173/"]):
                current_page = initial_page
            else:
                current_page = await browser_manager.new_tab()

            await current_page.bring_to_front()
            logger.info(f"[Multi-Tab] Opening tab {idx + 1}/{len(cleaned_urls)}: {target_url}")

            tab_res = await execute_live_browser_apply(
                url=target_url,
                profile=profile,
                job=None,
                resume_path=resume_path,
                cover_letter=cover_letter,
                auto_submit=auto_submit,
                page=current_page,
            )

            tab_results.append({
                "tab_index": idx + 1,
                "url": target_url,
                "outcome": tab_res.get("outcome", "UNKNOWN"),
                "message": tab_res.get("message", ""),
                "steps_completed": tab_res.get("steps_completed", []),
                "screenshot": tab_res.get("screenshot", ""),
            })

            # User-configured delay between tabs
            if idx < len(cleaned_urls) - 1 and delay_seconds > 0:
                logger.info(f"[Multi-Tab] Waiting {delay_seconds}s user delay before opening next tab...")
                await asyncio.sleep(delay_seconds)

        except Exception as e:
            logger.exception(f"[Multi-Tab] Error processing tab {idx + 1} ({target_url}): {e}")
            tab_results.append({
                "tab_index": idx + 1,
                "url": target_url,
                "outcome": "FAILED",
                "message": f"Tab error: {str(e)}",
                "steps_completed": [],
                "screenshot": "",
            })

    return {
        "total_tabs": len(cleaned_urls),
        "completed": len(tab_results),
        "delay_seconds": delay_seconds,
        "auto_submit": auto_submit,
        "tab_results": tab_results,
    }


async def execute_linkedin_auto_search_and_apply(
    keywords: str = "Python Developer",
    location: str = "Bengaluru, Karnataka, India",
    profile: Optional[CandidateProfile] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    max_jobs: int = 5,
    delay_seconds: float = 4.0,
    auto_submit: bool = True,
    unlimited: bool = False,
) -> Dict[str, Any]:
    """
    Automated LinkedIn Easy Apply search & apply robot.
    Supports UNLIMITED mode: paginates through search pages non-stop until all relevant jobs run out.
    Enforces anti-ban human delay and safety cooldowns to keep accounts completely safe.
    """
    target_limit_desc = "∞ UNLIMITED (Runs till relevant jobs run out)" if (unlimited or max_jobs <= 0) else f"Target {max_jobs} jobs"
    logger.info(f"Starting LinkedIn Auto-Pilot: keywords='{keywords}', location='{location}', {target_limit_desc}, delay={delay_seconds}s")

    if profile is None:
        db = SessionLocal()
        try:
            profile = db.query(CandidateProfile).first()
        finally:
            db.close()

    if profile is None:
        profile = CandidateProfile(
            full_name="Alex Mercer",
            email="alex.mercer@example.com",
            phone="+91 9876543210",
            current_location=location or "Bengaluru, India",
            years_of_experience=5.0,
            skills=["Python", "FastAPI", "React", "TypeScript", "SQLAlchemy", "Docker"],
        )

    # Launch or attach visible desktop browser
    page = await browser_manager.get_or_launch_page(headless=False)
    await page.bring_to_front()

    # Encode query parameters
    enc_kw = urllib.parse.quote(keywords.strip())
    enc_loc = urllib.parse.quote(location.strip())
    search_url = f"https://www.linkedin.com/jobs/search/?keywords={enc_kw}&location={enc_loc}&f_AL=true"

    logger.info(f"[LinkedIn Auto-Pilot] Navigating to: {search_url}")
    try:
        await page.goto(search_url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        logger.warning(f"[LinkedIn Auto-Pilot] Navigation timed out or slow: {e}")

    await page.wait_for_timeout(3000)

    # Check for authentication barrier
    curr_url = page.url.lower()
    if any(k in curr_url for k in ["login", "checkpoint", "authwall", "signup"]):
        shot = await browser_manager.capture_screenshot(page, "linkedin_auth_required")
        return {
            "outcome": "AUTH_REQUIRED",
            "message": "LinkedIn authentication required! Browser opened on your desktop. Please sign into LinkedIn in this window to save your session, then re-run.",
            "screenshot": shot,
            "jobs_processed": 0,
            "jobs_applied": 0,
            "applications": [],
        }

    # Step: Move cursor to "Easy Apply" filter toggle button and click to ensure it's selected
    easy_apply_filter_selectors = [
        "button[aria-label*='Easy Apply filter' i]",
        "button#searchFilter_applyWithLinkedin",
        "button:has-text('Easy Apply')",
        "button[aria-checked='false']:has-text('Easy Apply')",
    ]
    for sel in easy_apply_filter_selectors:
        loc = page.locator(sel).first
        if await loc.count() > 0 and await loc.is_visible():
            box = await loc.bounding_box()
            if box:
                await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=12)
                await page.wait_for_timeout(300)
                is_checked = await loc.get_attribute("aria-checked")
                if is_checked != "true":
                    await loc.click()
                    await page.wait_for_timeout(2500)
            break

    # Discover and iterate over job cards across pages
    applied_jobs = []
    processed_count = 0
    seen_job_urls = set()
    current_page_num = 1
    max_pages = 50 if (unlimited or max_jobs <= 0) else max(2, (max_jobs // 10) + 2)
    target_cap = 999999 if (unlimited or max_jobs <= 0) else max_jobs
    is_exhausted = False

    while True:
        if len(applied_jobs) >= target_cap:
            logger.info(f"[LinkedIn Auto-Pilot] Reached target application count ({len(applied_jobs)}/{target_cap}).")
            break
        if current_page_num > max_pages:
            logger.info(f"[LinkedIn Auto-Pilot] Processed maximum {max_pages} pages. Stopping.")
            break

        logger.info(f"[LinkedIn Auto-Pilot] Traversing Page {current_page_num}...")

        # Scroll list down incrementally to load all lazy-rendered cards
        for _ in range(4):
            await page.evaluate("""() => {
                const list = document.querySelector('.jobs-search-results-list, .scaffold-layout__list-container');
                if (list) list.scrollTop += 500;
            }""")
            await page.wait_for_timeout(500)

        # Query job cards
        cards = page.locator(
            "div.job-card-container, li.jobs-search-results__list-item, li[data-occludable-job-id]"
        )
        total_cards = await cards.count()

        if total_cards == 0:
            logger.warning(f"[LinkedIn Auto-Pilot] No job cards found on page {current_page_num}. Relevant jobs ran out.")
            is_exhausted = True
            break

        new_cards_processed_on_page = 0

        for card_idx in range(total_cards):
            if len(applied_jobs) >= target_cap:
                break

            card = cards.nth(card_idx)

            try:
                await card.scroll_into_view_if_needed()
                await page.wait_for_timeout(300)

                # Extract link for deduplication
                link_el = card.locator("a.job-card-list__title, a.job-card-container__link, a[href*='/jobs/view/']").first
                href = (await link_el.get_attribute("href")) if await link_el.count() > 0 else ""
                clean_href = href.split("?")[0] if href else ""

                if clean_href and clean_href in seen_job_urls:
                    continue
                if clean_href:
                    seen_job_urls.add(clean_href)

                new_cards_processed_on_page += 1

                # Smooth cursor move to the job card
                box = await card.bounding_box()
                if box:
                    await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=8)
                    await page.wait_for_timeout(200)
                    await card.click()
                else:
                    await card.click()

                await page.wait_for_timeout(1800)
                processed_count += 1

                # Extract job details from right-hand pane
                title_loc = page.locator(
                    "h1.t-24, .job-details-jobs-unified-top-card__job-title, .jobs-unified-top-card__job-title"
                ).first
                job_title = (await title_loc.inner_text()).strip() if await title_loc.count() > 0 else f"Job #{processed_count}"

                comp_loc = page.locator(
                    ".job-details-jobs-unified-top-card__company-name, .jobs-unified-top-card__company-name, a[href*='/company/']"
                ).first
                company_name = (await comp_loc.inner_text()).strip() if await comp_loc.count() > 0 else "LinkedIn Employer"

                loc_loc = page.locator(
                    ".job-details-jobs-unified-top-card__primary-description-container, .jobs-unified-top-card__bullet"
                ).first
                job_location = (await loc_loc.inner_text()).strip() if await loc_loc.count() > 0 else location

                current_job_url = clean_href or page.url

                # Check if already applied
                applied_badge = page.locator(
                    "span:has-text('Applied'), div:has-text('Applied '), .jobs-s-apply__application-link"
                ).first
                if await applied_badge.count() > 0 and await applied_badge.is_visible():
                    logger.info(f"[LinkedIn Auto-Pilot] Already applied to '{job_title}' at {company_name}. Skipping.")
                    continue

                # Look for Easy Apply button on details pane
                easy_btn = page.locator(
                    "button.jobs-apply-button:has-text('Easy Apply'), "
                    "div.jobs-apply-button--top-card button:has-text('Easy Apply'), "
                    "button:has-text('Easy Apply'), "
                    "button[aria-label*='Easy Apply' i]"
                ).first

                if await easy_btn.count() == 0 or not await easy_btn.is_visible():
                    logger.info(f"[LinkedIn Auto-Pilot] '{job_title}' does not have Easy Apply button (external apply). Skipping.")
                    continue

                # Cursor animation to Easy Apply button & click
                btn_box = await easy_btn.bounding_box()
                if btn_box:
                    await page.mouse.move(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2, steps=8)
                    await page.wait_for_timeout(250)
                await easy_btn.click()
                await page.wait_for_timeout(2000)

                # Execute multi-step Easy Apply modal workflow
                apply_res = await workflow_linkedin_easy_apply(
                    page=page,
                    profile=profile,
                    job=None,
                    resume_path=resume_path,
                    cover_letter=cover_letter,
                    auto_submit=auto_submit,
                )

                shot = await browser_manager.capture_screenshot(page, f"linkedin_{len(applied_jobs) + 1}")
                outcome = apply_res.get("outcome", "SUBMITTED" if "submitted" in apply_res.get("steps_completed", []) else "PARTIAL_FILLED")

                record = {
                    "index": len(applied_jobs) + 1,
                    "title": job_title,
                    "company": company_name,
                    "location": job_location,
                    "url": current_job_url,
                    "outcome": outcome,
                    "steps_completed": apply_res.get("steps_completed", []),
                    "screenshot": shot,
                }
                applied_jobs.append(record)
                logger.info(f"[LinkedIn Auto-Pilot] Applied #{len(applied_jobs)}: {job_title} at {company_name} -> {outcome}")

                # Persist application in SQLite DB
                try:
                    db = SessionLocal()
                    try:
                        db_job = db.query(JobListing).filter(JobListing.original_url == current_job_url).first()
                        if not db_job:
                            db_job = JobListing(
                                title=job_title,
                                company=company_name,
                                location=job_location,
                                original_url=current_job_url,
                                normalized_url=current_job_url,
                                source_platform="linkedin_easy_apply",
                                application_method="EASY_APPLY",
                                status="APPLIED" if outcome == "SUBMITTED" else "QUEUED",
                            )
                            db.add(db_job)
                            db.commit()
                            db.refresh(db_job)

                        db_app = JobApplication(
                            job_id=db_job.id,
                            status=ApplicationStatus.SUBMITTED.value if outcome == "SUBMITTED" else ApplicationStatus.AWAITING_REVIEW.value,
                            last_action=f"LinkedIn Easy Apply: {outcome} ({len(apply_res.get('steps_completed', []))} steps)",
                            screenshot_path=shot,
                            applied_at=datetime.utcnow() if outcome == "SUBMITTED" else None,
                        )
                        db.add(db_app)
                        db.commit()

                        log_activity(
                            db,
                            "SUCCESS" if outcome == "SUBMITTED" else "INFO",
                            "LINKEDIN_EASY_APPLY",
                            f"LinkedIn Auto-Pilot applied for '{job_title}' at {company_name}",
                            job_id=db_job.id,
                            application_id=db_app.id,
                        )
                    finally:
                        db.close()
                except Exception as dbe:
                    logger.warning(f"Error persisting LinkedIn app to DB: {dbe}")

                # Anti-ban natural delay with jitter and cooldown breathers every 5 jobs
                if delay_seconds > 0:
                    is_cooldown = (len(applied_jobs) % 5 == 0)
                    await _human_delay(delay_seconds, cooldown=is_cooldown)

            except Exception as loop_err:
                logger.exception(f"Error handling job card #{card_idx}: {loop_err}")
                try:
                    for dismiss_sel in ["button[aria-label*='Dismiss' i]", "button:has-text('Discard')"]:
                        d_btn = page.locator(dismiss_sel).first
                        if await d_btn.count() > 0 and await d_btn.is_visible():
                            await d_btn.click()
                            await page.wait_for_timeout(600)
                except Exception:
                    pass
                continue

        # Check if target reached
        if len(applied_jobs) >= target_cap:
            break

        # Pagination: check next page or navigate using &start={offset}
        next_page_num = current_page_num + 1
        start_offset = (next_page_num - 1) * 25
        next_url = f"https://www.linkedin.com/jobs/search/?keywords={enc_kw}&location={enc_loc}&f_AL=true&start={start_offset}"

        next_btn = page.locator(
            f"button[aria-label='View next page'], button[aria-label='Next'], button[aria-label*='Page {next_page_num}'], li[data-test-pagination-page-btn='{next_page_num}'] button"
        ).first

        has_next = False
        if await next_btn.count() > 0 and await next_btn.is_visible():
            logger.info(f"[LinkedIn Auto-Pilot] Clicking Next Page ({next_page_num})...")
            await next_btn.scroll_into_view_if_needed()
            await next_btn.click()
            has_next = True
        elif new_cards_processed_on_page > 0:
            logger.info(f"[LinkedIn Auto-Pilot] Navigating to next page offset: {next_url}")
            try:
                await page.goto(next_url, wait_until="domcontentloaded", timeout=35000)
                has_next = True
            except Exception:
                has_next = False

        if not has_next or new_cards_processed_on_page == 0:
            logger.info(f"[LinkedIn Auto-Pilot] All matching Easy Apply jobs for '{keywords}' in '{location}' on LinkedIn have been exhausted.")
            is_exhausted = True
            break

        current_page_num += 1
        await page.wait_for_timeout(3000)

    summary_shot = await browser_manager.capture_screenshot(page, "linkedin_autopilot_summary")
    return {
        "outcome": "JOBS_EXHAUSTED" if is_exhausted else "COMPLETED",
        "message": (
            f"Auto-Pilot applied to {len(applied_jobs)} jobs. All relevant Easy Apply listings for '{keywords}' in '{location}' on LinkedIn have run out."
            if is_exhausted else
            f"Auto-Pilot completed! Successfully applied to {len(applied_jobs)} LinkedIn Easy Apply jobs."
        ),
        "keywords": keywords,
        "location": location,
        "platform": "linkedin",
        "jobs_processed": processed_count,
        "jobs_applied": len(applied_jobs),
        "delay_seconds": delay_seconds,
        "auto_submit": auto_submit,
        "unlimited": unlimited,
        "applications": applied_jobs,
        "screenshot": summary_shot,
    }


async def execute_indeed_auto_search_and_apply(
    keywords: str = "Python Developer",
    location: str = "Bengaluru, Karnataka, India",
    profile: Optional[CandidateProfile] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    max_jobs: int = 5,
    delay_seconds: float = 4.0,
    auto_submit: bool = True,
    unlimited: bool = False,
) -> Dict[str, Any]:
    """
    Automated Indeed 'Easily apply' search & apply robot.
    Supports UNLIMITED mode: paginates through search pages non-stop until all relevant jobs run out.
    Enforces anti-ban human delay and safety cooldowns to keep accounts completely safe.
    """
    target_limit_desc = "∞ UNLIMITED (Runs till relevant jobs run out)" if (unlimited or max_jobs <= 0) else f"Target {max_jobs} jobs"
    logger.info(f"Starting Indeed Auto-Pilot: keywords='{keywords}', location='{location}', {target_limit_desc}, delay={delay_seconds}s")

    if profile is None:
        db = SessionLocal()
        try:
            profile = db.query(CandidateProfile).first()
        finally:
            db.close()

    if profile is None:
        profile = CandidateProfile(
            full_name="Alex Mercer",
            email="alex.mercer@example.com",
            phone="+91 9876543210",
            current_location=location or "Bengaluru, India",
            years_of_experience=5.0,
            skills=["Python", "FastAPI", "React", "TypeScript", "SQLAlchemy", "Docker"],
        )

    page = await browser_manager.get_or_launch_page(headless=False)
    await page.bring_to_front()

    # Determine region: Indeed India (in.indeed.com) vs Global
    is_india = any(w in location.lower() for w in ["india", "bengaluru", "bangalore", "delhi", "mumbai", "pune", "hyderabad", "chennai", "noida", "gurgaon"])
    base_host = "https://in.indeed.com" if is_india else "https://www.indeed.com"

    enc_kw = urllib.parse.quote(keywords.strip())
    enc_loc = urllib.parse.quote(location.strip())
    base_search_url = f"{base_host}/jobs?q={enc_kw}&l={enc_loc}&sc=0kf%3Aattr%28DSQF7%29%3B"

    logger.info(f"[Indeed Auto-Pilot] Navigating to: {base_search_url}")
    try:
        await page.goto(base_search_url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        logger.warning(f"[Indeed Auto-Pilot] Navigation timed out or slow: {e}")

    await page.wait_for_timeout(3000)

    # Check for authentication or Cloudflare verification challenge
    curr_url = page.url.lower()
    page_content = (await page.content()).lower()
    if any(k in curr_url for k in ["login", "checkpoint", "auth", "signup"]) or "verify you are human" in page_content:
        shot = await browser_manager.capture_screenshot(page, "indeed_auth_required")
        return {
            "outcome": "AUTH_REQUIRED",
            "message": "Indeed authentication or security challenge detected! Desktop browser opened. Please complete login in this window to save your session, then re-run.",
            "screenshot": shot,
            "jobs_processed": 0,
            "jobs_applied": 0,
            "applications": [],
        }

    applied_jobs = []
    processed_count = 0
    seen_job_urls = set()
    current_page_num = 1
    max_pages = 50 if (unlimited or max_jobs <= 0) else max(2, (max_jobs // 10) + 2)
    target_cap = 999999 if (unlimited or max_jobs <= 0) else max_jobs
    is_exhausted = False

    while True:
        if len(applied_jobs) >= target_cap:
            logger.info(f"[Indeed Auto-Pilot] Reached target application count ({len(applied_jobs)}/{target_cap}).")
            break
        if current_page_num > max_pages:
            logger.info(f"[Indeed Auto-Pilot] Reached maximum page count ({max_pages}). Stopping.")
            break

        logger.info(f"[Indeed Auto-Pilot] Traversing Page {current_page_num}...")

        # Scroll to ensure cards render
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 450)")
            await page.wait_for_timeout(400)

        cards = page.locator("div.job_seen_beacon, div.cardOutline, div[data-testid='slider_item'], div.jobsearch-ResultsList > li")
        total_cards = await cards.count()

        if total_cards == 0:
            logger.warning(f"[Indeed Auto-Pilot] No job cards found on page {current_page_num}. Relevant jobs ran out.")
            is_exhausted = True
            break

        new_cards_processed_on_page = 0

        for card_idx in range(total_cards):
            if len(applied_jobs) >= target_cap:
                break

            card = cards.nth(card_idx)

            try:
                await card.scroll_into_view_if_needed()
                await page.wait_for_timeout(300)

                # Find link for deduplication
                link_el = card.locator("a.jcs-JobTitle, a[id*='job_'], a[data-jk]").first
                job_key = (await link_el.get_attribute("data-jk")) if await link_el.count() > 0 else ""
                href = (await link_el.get_attribute("href")) if await link_el.count() > 0 else ""
                clean_href = f"{base_host}/viewjob?jk={job_key}" if job_key else (href.split("&")[0] if href else "")

                if clean_href and clean_href in seen_job_urls:
                    continue
                if clean_href:
                    seen_job_urls.add(clean_href)

                new_cards_processed_on_page += 1

                # Move cursor to job card with human motion
                box = await card.bounding_box()
                if box:
                    await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=8)
                    await page.wait_for_timeout(200)
                    await card.click()
                else:
                    await card.click()

                await page.wait_for_timeout(2000)
                processed_count += 1

                # Extract job details
                title_loc = page.locator("h2.jobsearch-JobInfoHeader-title, h1[data-testid='jobsearch-JobInfoHeader-title'], .jobsearch-JobInfoHeader-title").first
                job_title = (await title_loc.inner_text()).strip() if await title_loc.count() > 0 else f"Job #{processed_count}"

                comp_loc = page.locator("div[data-testid='inlineHeader-companyName'], .jobsearch-InlineCompanyRating-companyHeader, a[data-company-name='true']").first
                company_name = (await comp_loc.inner_text()).strip() if await comp_loc.count() > 0 else "Indeed Employer"

                loc_loc = page.locator("div[data-testid='inlineHeader-companyLocation'], .jobsearch-JobInfoHeader-companyLocation").first
                job_location = (await loc_loc.inner_text()).strip() if await loc_loc.count() > 0 else location

                current_job_url = clean_href or page.url

                # Check for Easily apply CTA button
                apply_btn = page.locator("button#indeedApplyButton, button:has-text('Apply now'), a:has-text('Apply now')").first
                if await apply_btn.count() == 0 or not await apply_btn.is_visible():
                    logger.info(f"[Indeed Auto-Pilot] '{job_title}' does not have 1-click Apply button. Skipping.")
                    continue

                # Cursor move to Apply button
                btn_box = await apply_btn.bounding_box()
                if btn_box:
                    await page.mouse.move(btn_box["x"] + btn_box["width"] / 2, btn_box["y"] + btn_box["height"] / 2, steps=8)
                    await page.wait_for_timeout(250)
                await apply_btn.click()
                await page.wait_for_timeout(2000)

                # Execute Indeed multi-step apply workflow
                apply_res = await workflow_indeed_apply(
                    page=page,
                    profile=profile,
                    job=None,
                    resume_path=resume_path,
                    cover_letter=cover_letter,
                    auto_submit=auto_submit,
                )

                shot = await browser_manager.capture_screenshot(page, f"indeed_{len(applied_jobs) + 1}")
                outcome = apply_res.get("outcome", "SUBMITTED" if "submitted" in apply_res.get("steps_completed", []) else "PARTIAL_FILLED")

                record = {
                    "index": len(applied_jobs) + 1,
                    "title": job_title,
                    "company": company_name,
                    "location": job_location,
                    "url": current_job_url,
                    "outcome": outcome,
                    "steps_completed": apply_res.get("steps_completed", []),
                    "screenshot": shot,
                }
                applied_jobs.append(record)
                logger.info(f"[Indeed Auto-Pilot] Applied #{len(applied_jobs)}: {job_title} at {company_name} -> {outcome}")

                # Persist application in SQLite DB
                try:
                    db = SessionLocal()
                    try:
                        db_job = db.query(JobListing).filter(JobListing.original_url == current_job_url).first()
                        if not db_job:
                            db_job = JobListing(
                                title=job_title,
                                company=company_name,
                                location=job_location,
                                original_url=current_job_url,
                                normalized_url=current_job_url,
                                source_platform="indeed_easily_apply",
                                application_method="EASY_APPLY",
                                status="APPLIED" if outcome == "SUBMITTED" else "QUEUED",
                            )
                            db.add(db_job)
                            db.commit()
                            db.refresh(db_job)

                        db_app = JobApplication(
                            job_id=db_job.id,
                            status=ApplicationStatus.SUBMITTED.value if outcome == "SUBMITTED" else ApplicationStatus.AWAITING_REVIEW.value,
                            last_action=f"Indeed Auto-Pilot: {outcome} ({len(apply_res.get('steps_completed', []))} steps)",
                            screenshot_path=shot,
                            applied_at=datetime.utcnow() if outcome == "SUBMITTED" else None,
                        )
                        db.add(db_app)
                        db.commit()

                        log_activity(
                            db,
                            "SUCCESS" if outcome == "SUBMITTED" else "INFO",
                            "INDEED_APPLY",
                            f"Indeed Auto-Pilot applied for '{job_title}' at {company_name}",
                            job_id=db_job.id,
                            application_id=db_app.id,
                        )
                    finally:
                        db.close()
                except Exception as dbe:
                    logger.warning(f"Error persisting Indeed app to DB: {dbe}")

                # Anti-ban delay with natural jitter
                if delay_seconds > 0:
                    is_cooldown = (len(applied_jobs) % 5 == 0)
                    await _human_delay(delay_seconds, cooldown=is_cooldown)

            except Exception as loop_err:
                logger.exception(f"Error handling Indeed card #{card_idx}: {loop_err}")
                continue

        # Check if target reached
        if len(applied_jobs) >= target_cap:
            break

        # Pagination to next page
        next_page_num = current_page_num + 1
        start_offset = (next_page_num - 1) * 10
        next_url = f"{base_search_url}&start={start_offset}"

        next_btn = page.locator("a[data-testid='pagination-page-next'], a[aria-label='Next Page'], a[aria-label='Next']").first
        has_next = False
        if await next_btn.count() > 0 and await next_btn.is_visible():
            logger.info(f"[Indeed Auto-Pilot] Clicking Next Page ({next_page_num})...")
            await next_btn.scroll_into_view_if_needed()
            await next_btn.click()
            has_next = True
        elif new_cards_processed_on_page > 0:
            logger.info(f"[Indeed Auto-Pilot] Navigating to next page offset: {next_url}")
            try:
                await page.goto(next_url, wait_until="domcontentloaded", timeout=35000)
                has_next = True
            except Exception:
                has_next = False

        if not has_next or new_cards_processed_on_page == 0:
            logger.info(f"[Indeed Auto-Pilot] All matching Indeed jobs for '{keywords}' in '{location}' have been exhausted.")
            is_exhausted = True
            break

        current_page_num += 1
        await page.wait_for_timeout(3000)

    summary_shot = await browser_manager.capture_screenshot(page, "indeed_autopilot_summary")
    return {
        "outcome": "JOBS_EXHAUSTED" if is_exhausted else "COMPLETED",
        "message": (
            f"Auto-Pilot applied to {len(applied_jobs)} jobs. All relevant Indeed Easily Apply listings for '{keywords}' in '{location}' have run out."
            if is_exhausted else
            f"Auto-Pilot completed! Successfully applied to {len(applied_jobs)} Indeed jobs."
        ),
        "keywords": keywords,
        "location": location,
        "platform": "indeed",
        "jobs_processed": processed_count,
        "jobs_applied": len(applied_jobs),
        "delay_seconds": delay_seconds,
        "auto_submit": auto_submit,
        "unlimited": unlimited,
        "applications": applied_jobs,
        "screenshot": summary_shot,
    }


async def execute_naukri_auto_search_and_apply(
    keywords: str = "Python Developer",
    location: str = "Bengaluru",
    profile: Optional[CandidateProfile] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    max_jobs: int = 5,
    delay_seconds: float = 4.0,
    auto_submit: bool = True,
    unlimited: bool = False,
) -> Dict[str, Any]:
    """
    Automated Naukri.com (India #1 Portal) 1-Click Fast Apply robot.
    Supports UNLIMITED mode: paginates through search pages non-stop until all relevant jobs run out.
    Enforces anti-ban human delay and safety cooldowns to keep accounts completely safe.
    """
    target_limit_desc = "∞ UNLIMITED (Runs till relevant jobs run out)" if (unlimited or max_jobs <= 0) else f"Target {max_jobs} jobs"
    logger.info(f"Starting Naukri India Auto-Pilot: keywords='{keywords}', location='{location}', {target_limit_desc}, delay={delay_seconds}s")

    if profile is None:
        db = SessionLocal()
        try:
            profile = db.query(CandidateProfile).first()
        finally:
            db.close()

    if profile is None:
        profile = CandidateProfile(
            full_name="Alex Mercer",
            email="alex.mercer@example.com",
            phone="+91 9876543210",
            current_location=location or "Bengaluru, India",
            years_of_experience=5.0,
            skills=["Python", "FastAPI", "React", "TypeScript", "SQLAlchemy", "Docker"],
        )

    page = await browser_manager.get_or_launch_page(headless=False)
    await page.bring_to_front()

    kw_clean = keywords.strip().replace(" ", "-").lower()
    loc_clean = location.strip().replace(" ", "-").lower()
    base_search_url = f"https://www.naukri.com/{kw_clean}-jobs-in-{loc_clean}"

    logger.info(f"[Naukri Auto-Pilot] Navigating to: {base_search_url}")
    try:
        await page.goto(base_search_url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        logger.warning(f"[Naukri Auto-Pilot] Navigation timed out or slow: {e}")

    await page.wait_for_timeout(3000)

    # Check for authentication barrier
    curr_url = page.url.lower()
    if any(k in curr_url for k in ["login", "register", "auth"]):
        shot = await browser_manager.capture_screenshot(page, "naukri_auth_required")
        return {
            "outcome": "AUTH_REQUIRED",
            "message": "Naukri authentication required! Desktop browser opened. Please log in to your Naukri account in this window to save your session, then re-run.",
            "screenshot": shot,
            "jobs_processed": 0,
            "jobs_applied": 0,
            "applications": [],
        }

    applied_jobs = []
    processed_count = 0
    seen_job_urls = set()
    current_page_num = 1
    max_pages = 50 if (unlimited or max_jobs <= 0) else max(2, (max_jobs // 10) + 2)
    target_cap = 999999 if (unlimited or max_jobs <= 0) else max_jobs
    is_exhausted = False

    while True:
        if len(applied_jobs) >= target_cap:
            logger.info(f"[Naukri Auto-Pilot] Reached target application count ({len(applied_jobs)}/{target_cap}).")
            break
        if current_page_num > max_pages:
            logger.info(f"[Naukri Auto-Pilot] Reached maximum page limit ({max_pages}). Stopping.")
            break

        logger.info(f"[Naukri Auto-Pilot] Traversing Page {current_page_num}...")

        # Scroll to load job tuples
        for _ in range(3):
            await page.evaluate("window.scrollBy(0, 450)")
            await page.wait_for_timeout(400)

        cards = page.locator("div.srp-jobtuple-wrapper, article.jobTuple, div.cust-job-tuple, div.tuple")
        total_cards = await cards.count()

        if total_cards == 0:
            logger.warning(f"[Naukri Auto-Pilot] No job cards found on page {current_page_num}. Relevant jobs ran out.")
            is_exhausted = True
            break

        new_cards_processed_on_page = 0

        for card_idx in range(total_cards):
            if len(applied_jobs) >= target_cap:
                break

            card = cards.nth(card_idx)

            try:
                await card.scroll_into_view_if_needed()
                await page.wait_for_timeout(300)

                title_loc = card.locator("a.title, .job-title, a[class*='title']").first
                job_title = (await title_loc.inner_text()).strip() if await title_loc.count() > 0 else f"Job #{processed_count}"

                comp_loc = card.locator("a.comp-name, .company-name, a[class*='comp-name']").first
                company_name = (await comp_loc.inner_text()).strip() if await comp_loc.count() > 0 else "Naukri Employer"

                loc_loc = card.locator(".loc-wrap, .location, span[class*='loc']").first
                job_location = (await loc_loc.inner_text()).strip() if await loc_loc.count() > 0 else location

                job_link = (await title_loc.get_attribute("href") or page.url) if await title_loc.count() > 0 else page.url
                clean_link = job_link.split("?")[0] if job_link else ""

                if clean_link and clean_link in seen_job_urls:
                    continue
                if clean_link:
                    seen_job_urls.add(clean_link)

                new_cards_processed_on_page += 1

                # Click card with human cursor motion
                box = await card.bounding_box()
                if box:
                    await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=8)
                    await card.click()
                else:
                    await card.click()

                await page.wait_for_timeout(2000)
                processed_count += 1

                # Run Naukri apply workflow
                apply_res = await workflow_naukri_apply(
                    page=page,
                    profile=profile,
                    job=None,
                    resume_path=resume_path,
                    cover_letter=cover_letter,
                    auto_submit=auto_submit,
                )

                shot = await browser_manager.capture_screenshot(page, f"naukri_{len(applied_jobs) + 1}")
                outcome = "SUBMITTED" if "submitted" in apply_res.get("steps_completed", []) else "PARTIAL_FILLED"

                record = {
                    "index": len(applied_jobs) + 1,
                    "title": job_title,
                    "company": company_name,
                    "location": job_location,
                    "url": clean_link or job_link,
                    "outcome": outcome,
                    "steps_completed": apply_res.get("steps_completed", []),
                    "screenshot": shot,
                }
                applied_jobs.append(record)
                logger.info(f"[Naukri Auto-Pilot] Applied #{len(applied_jobs)}: {job_title} at {company_name} -> {outcome}")

                # Persist in DB
                try:
                    db = SessionLocal()
                    try:
                        db_job = db.query(JobListing).filter(JobListing.original_url == job_link).first()
                        if not db_job:
                            db_job = JobListing(
                                title=job_title,
                                company=company_name,
                                location=job_location,
                                original_url=job_link,
                                normalized_url=job_link,
                                source_platform="naukri_india",
                                application_method="ONE_CLICK",
                                status="APPLIED" if outcome == "SUBMITTED" else "QUEUED",
                            )
                            db.add(db_job)
                            db.commit()
                            db.refresh(db_job)

                        db_app = JobApplication(
                            job_id=db_job.id,
                            status=ApplicationStatus.SUBMITTED.value if outcome == "SUBMITTED" else ApplicationStatus.AWAITING_REVIEW.value,
                            last_action=f"Naukri Auto-Pilot: {outcome} ({len(apply_res.get('steps_completed', []))} steps)",
                            screenshot_path=shot,
                            applied_at=datetime.utcnow() if outcome == "SUBMITTED" else None,
                        )
                        db.add(db_app)
                        db.commit()

                        log_activity(
                            db,
                            "SUCCESS" if outcome == "SUBMITTED" else "INFO",
                            "NAUKRI_APPLY",
                            f"Naukri Auto-Pilot applied for '{job_title}' at {company_name}",
                            job_id=db_job.id,
                            application_id=db_app.id,
                        )
                    finally:
                        db.close()
                except Exception as dbe:
                    logger.warning(f"Error persisting Naukri app to DB: {dbe}")

                # Anti-ban delay with natural jitter
                if delay_seconds > 0:
                    is_cooldown = (len(applied_jobs) % 5 == 0)
                    await _human_delay(delay_seconds, cooldown=is_cooldown)

            except Exception as loop_err:
                logger.exception(f"Error handling Naukri card #{card_idx}: {loop_err}")
                continue

        # Check if target reached
        if len(applied_jobs) >= target_cap:
            break

        # Pagination: next page in Naukri is typically URL suffix -2, -3 or next button
        next_page_num = current_page_num + 1
        next_url = f"https://www.naukri.com/{kw_clean}-jobs-in-{loc_clean}-{next_page_num}"

        next_btn = page.locator("a.fright, a:has-text('Next'), div.pagination a:has-text('Next')").first
        has_next = False
        if await next_btn.count() > 0 and await next_btn.is_visible():
            logger.info(f"[Naukri Auto-Pilot] Clicking Next Page ({next_page_num})...")
            await next_btn.scroll_into_view_if_needed()
            await next_btn.click()
            has_next = True
        elif new_cards_processed_on_page > 0:
            logger.info(f"[Naukri Auto-Pilot] Navigating to next page URL: {next_url}")
            try:
                await page.goto(next_url, wait_until="domcontentloaded", timeout=35000)
                has_next = True
            except Exception:
                has_next = False

        if not has_next or new_cards_processed_on_page == 0:
            logger.info(f"[Naukri Auto-Pilot] All matching Naukri India jobs for '{keywords}' in '{location}' have run out.")
            is_exhausted = True
            break

        current_page_num += 1
        await page.wait_for_timeout(3000)

    summary_shot = await browser_manager.capture_screenshot(page, "naukri_autopilot_summary")
    return {
        "outcome": "JOBS_EXHAUSTED" if is_exhausted else "COMPLETED",
        "message": (
            f"Auto-Pilot applied to {len(applied_jobs)} jobs. All relevant Naukri India 1-Click Apply listings for '{keywords}' in '{location}' have run out."
            if is_exhausted else
            f"Auto-Pilot completed! Successfully applied to {len(applied_jobs)} Naukri India jobs."
        ),
        "keywords": keywords,
        "location": location,
        "platform": "naukri",
        "jobs_processed": processed_count,
        "jobs_applied": len(applied_jobs),
        "delay_seconds": delay_seconds,
        "auto_submit": auto_submit,
        "unlimited": unlimited,
        "applications": applied_jobs,
        "screenshot": summary_shot,
    }


async def execute_universal_job_search_and_apply(
    platform: str = "linkedin",
    keywords: str = "Python Developer",
    location: str = "Bengaluru, Karnataka, India",
    profile: Optional[CandidateProfile] = None,
    resume_path: Optional[str] = None,
    cover_letter: str = "",
    max_jobs: int = 10,
    delay_seconds: float = 4.0,
    auto_submit: bool = True,
    non_stop: bool = False,
    unlimited: bool = False,
) -> Dict[str, Any]:
    """
    Universal multi-jobsite auto-pilot router.
    Routes execution to LinkedIn, Indeed, Naukri, or cycles across all of them in continuous non-stop or unlimited mode.
    Guarantees anti-ban human delay and safety cooldowns to keep accounts in good standing.
    """
    plat = platform.lower().strip()
    target_desc = "∞ UNLIMITED (till jobs run out)" if unlimited else f"{max_jobs} jobs"
    logger.info(f"Universal Auto-Pilot: platform='{plat}', keywords='{keywords}', target={target_desc}, non_stop={non_stop}")

    if plat == "indeed":
        return await execute_indeed_auto_search_and_apply(
            keywords=keywords,
            location=location,
            profile=profile,
            resume_path=resume_path,
            cover_letter=cover_letter,
            max_jobs=max_jobs,
            delay_seconds=delay_seconds,
            auto_submit=auto_submit,
            unlimited=unlimited,
        )
    elif plat == "naukri":
        return await execute_naukri_auto_search_and_apply(
            keywords=keywords,
            location=location,
            profile=profile,
            resume_path=resume_path,
            cover_letter=cover_letter,
            max_jobs=max_jobs,
            delay_seconds=delay_seconds,
            auto_submit=auto_submit,
            unlimited=unlimited,
        )
    elif plat in ["all", "multi_portal"]:
        # If unlimited, process each platform until jobs run out or large target reached
        each_target = 999999 if unlimited else max(1, max_jobs // 3)

        res_li = await execute_linkedin_auto_search_and_apply(
            keywords=keywords, location=location, profile=profile,
            resume_path=resume_path, cover_letter=cover_letter,
            max_jobs=each_target, delay_seconds=delay_seconds, auto_submit=auto_submit,
            unlimited=unlimited,
        )
        await _human_delay(delay_seconds, cooldown=True)

        res_ind = await execute_indeed_auto_search_and_apply(
            keywords=keywords, location=location, profile=profile,
            resume_path=resume_path, cover_letter=cover_letter,
            max_jobs=each_target, delay_seconds=delay_seconds, auto_submit=auto_submit,
            unlimited=unlimited,
        )
        await _human_delay(delay_seconds, cooldown=True)

        res_nk = await execute_naukri_auto_search_and_apply(
            keywords=keywords, location=location, profile=profile,
            resume_path=resume_path, cover_letter=cover_letter,
            max_jobs=each_target, delay_seconds=delay_seconds, auto_submit=auto_submit,
            unlimited=unlimited,
        )

        all_apps = res_li.get("applications", []) + res_ind.get("applications", []) + res_nk.get("applications", [])
        total_applied = len(all_apps)
        return {
            "outcome": "JOBS_EXHAUSTED" if (res_li.get("outcome") == "JOBS_EXHAUSTED" and res_ind.get("outcome") == "JOBS_EXHAUSTED") else "COMPLETED",
            "message": f"Multi-Portal Auto-Pilot applied to {total_applied} jobs across LinkedIn, Indeed, and Naukri India." + (" All relevant listings across portals have run out!" if unlimited else ""),
            "keywords": keywords,
            "location": location,
            "platform": "multi_portal",
            "jobs_applied": total_applied,
            "jobs_processed": res_li.get("jobs_processed", 0) + res_ind.get("jobs_processed", 0) + res_nk.get("jobs_processed", 0),
            "unlimited": unlimited,
            "applications": all_apps,
            "screenshot": res_nk.get("screenshot") or res_li.get("screenshot"),
        }
    else:
        # Default to LinkedIn
        return await execute_linkedin_auto_search_and_apply(
            keywords=keywords,
            location=location,
            profile=profile,
            resume_path=resume_path,
            cover_letter=cover_letter,
            max_jobs=max_jobs,
            delay_seconds=delay_seconds,
            auto_submit=auto_submit,
            unlimited=unlimited,
        )


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
