from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from backend.app.database.session import get_db
from backend.app.models.job import JobListing
from backend.app.models.profile import CandidateProfile
from backend.app.models.settings import JobPreferences, AutomationSettings
from backend.app.models.application import JobApplication, ApplicationStatus
from backend.app.schemas.job import JobListingResponse, JobListingCreate
from backend.app.services.matcher import evaluate_job_match
from backend.app.services.duplicate import check_for_duplicate_job, normalize_job_url
from backend.app.providers.remoteok import RemoteOKProvider
from backend.app.providers.jobicy import JobicyProvider
from backend.app.providers.mock_provider import MockJobProvider
from backend.app.providers.csv_provider import parse_csv_jobs, export_jobs_to_csv
from backend.app.core.logging import log_activity

router = APIRouter(prefix="/jobs", tags=["Job Discovery & Listings"])


@router.get("", response_model=List[JobListingResponse])
def get_jobs(
    search: Optional[str] = None,
    company: Optional[str] = None,
    work_mode: Optional[str] = None,
    min_score: Optional[float] = None,
    source_platform: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(JobListing).filter(JobListing.is_archived == False)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(JobListing.title.ilike(term), JobListing.company.ilike(term), JobListing.description.ilike(term)))
    if company:
        query = query.filter(JobListing.company.ilike(f"%{company.strip()}%"))
    if work_mode and work_mode != "all":
        query = query.filter(JobListing.work_mode == work_mode)
    if min_score is not None:
        query = query.filter(JobListing.match_score >= min_score)
    if source_platform and source_platform != "all":
        query = query.filter(JobListing.source_platform == source_platform)
    if status and status != "all":
        query = query.filter(JobListing.status == status)

    return query.order_by(desc(JobListing.match_score), desc(JobListing.discovered_at)).offset(skip).limit(limit).all()


@router.get("/export/csv")
def export_jobs(db: Session = Depends(get_db)):
    jobs = db.query(JobListing).filter(JobListing.is_archived == False).all()
    job_dicts = []
    for j in jobs:
        job_dicts.append({
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "location": j.location,
            "work_mode": j.work_mode,
            "employment_type": j.employment_type,
            "salary_min": j.salary_min or "",
            "salary_max": j.salary_max or "",
            "match_score": j.match_score,
            "status": j.status,
            "source_platform": j.source_platform,
            "original_url": j.original_url
        })
    csv_data = export_jobs_to_csv(job_dicts)
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=applypilot_jobs.csv"}
    )


@router.get("/{job_id}", response_model=JobListingResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/discover")
async def discover_jobs(
    source: str = Query("all", description="Source provider: all, remoteok, jobicy, synthetic_demo"),
    db: Session = Depends(get_db)
):
    profile = db.query(CandidateProfile).first() or CandidateProfile()
    prefs = db.query(JobPreferences).first() or JobPreferences()
    settings_obj = db.query(AutomationSettings).first() or AutomationSettings()

    providers = []
    if source in ["all", "remoteok"]:
        providers.append(RemoteOKProvider())
    if source in ["all", "jobicy"]:
        providers.append(JobicyProvider())
    if source in ["all", "synthetic_demo"] or (source == "all" and settings_obj.simulation_mode):
        providers.append(MockJobProvider())

    discovered_count = 0
    duplicates_skipped = 0
    new_jobs = []

    for prov in providers:
        try:
            raw_jobs = await prov.fetch_jobs(limit=settings_obj.max_jobs_to_inspect)
            for jdata in raw_jobs:
                is_dup, existing, _ = check_for_duplicate_job(
                    db,
                    raw_url=jdata.get("original_url", ""),
                    title=jdata.get("title", ""),
                    company=jdata.get("company", ""),
                    source_job_id=jdata.get("source_job_id")
                )
                if is_dup and settings_obj.skip_duplicates:
                    duplicates_skipped += 1
                    continue

                # Score & check eligibility
                score, breakdown, eligibility = evaluate_job_match(jdata, profile, prefs)
                norm_url = normalize_job_url(jdata.get("original_url", ""))

                job_record = JobListing(
                    title=jdata.get("title", "Software Engineer"),
                    company=jdata.get("company", "Company"),
                    location=jdata.get("location", ""),
                    work_mode=jdata.get("work_mode", "remote"),
                    employment_type=jdata.get("employment_type", "full_time"),
                    salary_min=jdata.get("salary_min"),
                    salary_max=jdata.get("salary_max"),
                    salary_currency=jdata.get("salary_currency", "USD"),
                    experience_min_years=jdata.get("experience_min_years", 0.0),
                    experience_level=jdata.get("experience_level", "mid"),
                    required_skills=jdata.get("required_skills", []),
                    description=jdata.get("description", ""),
                    source_platform=prov.provider_name,
                    original_url=jdata.get("original_url", ""),
                    normalized_url=norm_url,
                    source_job_id=jdata.get("source_job_id"),
                    application_method=jdata.get("application_method", "EXTERNAL_SITE"),
                    match_score=score,
                    match_breakdown=breakdown,
                    eligibility_assessment=eligibility,
                    status="MATCHED" if score >= settings_obj.min_match_score and eligibility.get("is_eligible") else "DISCOVERED"
                )
                db.add(job_record)
                new_jobs.append(job_record)
                discovered_count += 1
        except Exception as e:
            log_activity(db, "ERROR", "DISCOVERY_ERROR", f"Provider {prov.provider_name} failed: {e}")

    db.commit()
    log_activity(
        db, "SUCCESS", "JOB_DISCOVERY",
        f"Discovery run completed: {discovered_count} discovered, {duplicates_skipped} duplicates skipped",
        details={"discovered": discovered_count, "duplicates_skipped": duplicates_skipped}
    )
    return {
        "success": True,
        "discovered_count": discovered_count,
        "duplicates_skipped": duplicates_skipped
    }


@router.post("/import/url")
def import_job_from_url(data: JobListingCreate, db: Session = Depends(get_db)):
    profile = db.query(CandidateProfile).first() or CandidateProfile()
    prefs = db.query(JobPreferences).first() or JobPreferences()

    is_dup, existing, reason = check_for_duplicate_job(
        db, raw_url=data.original_url, title=data.title, company=data.company
    )
    if is_dup:
        raise HTTPException(status_code=400, detail=f"Duplicate job detected: {reason}")

    score, breakdown, eligibility = evaluate_job_match(data.model_dump(), profile, prefs)
    norm_url = normalize_job_url(data.original_url)

    job_record = JobListing(
        title=data.title,
        company=data.company,
        location=data.location,
        work_mode=data.work_mode,
        employment_type=data.employment_type,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        salary_currency=data.salary_currency,
        experience_min_years=data.experience_min_years,
        experience_level=data.experience_level,
        required_skills=data.required_skills,
        description=data.description,
        source_platform=data.source_platform or "manual",
        original_url=data.original_url,
        normalized_url=norm_url,
        source_job_id=data.source_job_id,
        application_method=data.application_method,
        match_score=score,
        match_breakdown=breakdown,
        eligibility_assessment=eligibility,
        status="MATCHED" if score >= 60.0 else "DISCOVERED"
    )
    db.add(job_record)
    db.commit()
    db.refresh(job_record)
    log_activity(db, "INFO", "MANUAL_IMPORT", f"Manually imported job '{data.title}' at {data.company}")
    return job_record


@router.post("/import/csv")
async def import_csv_jobs(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    parsed_jobs = parse_csv_jobs(text)
    
    if not parsed_jobs:
        raise HTTPException(status_code=400, detail="No valid jobs parsed from CSV file")

    profile = db.query(CandidateProfile).first() or CandidateProfile()
    prefs = db.query(JobPreferences).first() or JobPreferences()
    settings_obj = db.query(AutomationSettings).first() or AutomationSettings()

    imported = 0
    duplicates = 0
    for j in parsed_jobs:
        is_dup, _, _ = check_for_duplicate_job(db, j.get("original_url", ""), j["title"], j["company"])
        if is_dup and settings_obj.skip_duplicates:
            duplicates += 1
            continue

        score, breakdown, eligibility = evaluate_job_match(j, profile, prefs)
        norm_url = normalize_job_url(j.get("original_url", ""))

        record = JobListing(
            title=j["title"],
            company=j["company"],
            location=j.get("location", ""),
            work_mode=j.get("work_mode", "remote"),
            employment_type=j.get("employment_type", "full_time"),
            salary_min=j.get("salary_min"),
            salary_max=j.get("salary_max"),
            salary_currency=j.get("salary_currency", "USD"),
            experience_min_years=j.get("experience_min_years", 0.0),
            experience_level=j.get("experience_level", "mid"),
            required_skills=j.get("required_skills", []),
            description=j.get("description", ""),
            source_platform="csv_import",
            original_url=j.get("original_url", ""),
            normalized_url=norm_url,
            application_method=j.get("application_method", "EXTERNAL_SITE"),
            match_score=score,
            match_breakdown=breakdown,
            eligibility_assessment=eligibility,
            status="MATCHED" if score >= settings_obj.min_match_score else "DISCOVERED"
        )
        db.add(record)
        imported += 1

    db.commit()
    log_activity(db, "SUCCESS", "CSV_IMPORT", f"Imported {imported} jobs from CSV ({duplicates} duplicates skipped)")
    return {"success": True, "imported_count": imported, "duplicates_skipped": duplicates}


@router.post("/{job_id}/queue")
def add_job_to_queue(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobListing).filter(JobListing.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing_app = db.query(JobApplication).filter(JobApplication.job_id == job_id).first()
    if existing_app:
        return {"success": True, "message": "Job already in queue", "application_id": existing_app.id}

    max_pos = db.query(JobApplication.queue_position).order_by(desc(JobApplication.queue_position)).first()
    next_pos = (max_pos[0] + 1) if max_pos and max_pos[0] is not None else 1

    app_record = JobApplication(
        job_id=job.id,
        status=ApplicationStatus.QUEUED.value,
        queue_position=next_pos,
        last_action="Added to application queue"
    )
    job.status = "QUEUED"
    db.add(app_record)
    db.commit()
    db.refresh(app_record)

    log_activity(db, "INFO", "QUEUE_ADD", f"Added '{job.title}' at {job.company} to application queue")
    return {"success": True, "application_id": app_record.id, "queue_position": next_pos}
