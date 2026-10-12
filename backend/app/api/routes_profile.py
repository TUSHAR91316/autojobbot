import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.core.config import RESUMES_DIR
from backend.app.models.profile import CandidateProfile
from backend.app.models.resume import ResumeVersion
from backend.app.schemas.profile import CandidateProfileResponse, CandidateProfileUpdate
from backend.app.schemas.resume import ResumeVersionResponse
from backend.app.services.resume_parser import parse_resume_content
from backend.app.core.logging import log_activity

router = APIRouter(prefix="/profile", tags=["Profile & Resume"])


def get_or_create_profile(db: Session) -> CandidateProfile:
    profile = db.query(CandidateProfile).first()
    if not profile:
        profile = CandidateProfile(
            full_name="Alex Mercer",
            email="alex.mercer@example.com",
            phone="+1 (555) 234-5678",
            current_location="San Francisco, CA",
            headline="Senior Full Stack & Python Engineer",
            summary="Full stack engineer with 5+ years of experience architecting resilient distributed systems, modern web frontends, and automated workflows.",
            skills=["Python", "FastAPI", "React", "TypeScript", "SQLAlchemy", "Docker", "Tailwind CSS"],
            preferred_job_titles=["Senior Software Engineer", "Full Stack Developer", "Backend Engineer"],
            preferred_locations=["Remote", "San Francisco, CA", "Worldwide"],
            remote_preference="remote_only",
            years_of_experience=5.0,
            experience_level="senior",
            employment_types=["full_time"],
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.get("", response_model=CandidateProfileResponse)
def get_profile(db: Session = Depends(get_db)):
    return get_or_create_profile(db)


@router.put("", response_model=CandidateProfileResponse)
def update_profile(data: CandidateProfileUpdate, db: Session = Depends(get_db)):
    profile = get_or_create_profile(db)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    log_activity(db, "INFO", "PROFILE_UPDATE", "Updated candidate profile details")
    return profile


@router.get("/resumes", response_model=List[ResumeVersionResponse])
def list_resumes(db: Session = Depends(get_db)):
    return db.query(ResumeVersion).order_by(ResumeVersion.is_primary.desc(), ResumeVersion.created_at.desc()).all()


@router.post("/resumes/upload", response_model=ResumeVersionResponse)
async def upload_resume(
    label: str = Form(...),
    target_categories: str = Form(""),  # comma separated
    is_primary: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Validate extension
    file_ext = Path(file.filename or "").suffix.lower().lstrip(".")
    if file_ext not in ["pdf", "docx"]:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are permitted")

    # Limit file size to 10MB
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")

    # Safe destination filename
    clean_filename = f"{Path(file.filename or 'resume').stem}_{file_ext}"
    dest_path = RESUMES_DIR / f"{Path(file.filename or 'resume').stem}_{file_ext}"
    counter = 1
    while dest_path.exists():
        dest_path = RESUMES_DIR / f"{Path(file.filename or 'resume').stem}_{counter}.{file_ext}"
        counter += 1

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text locally
    try:
        parsed = parse_resume_content(dest_path, file_ext)
        extracted_text = parsed["text"]
    except Exception as e:
        extracted_text = f"[Text extraction notice: {str(e)}]"

    # If is_primary, unset any previous primary
    if is_primary:
        db.query(ResumeVersion).update({ResumeVersion.is_primary: False})

    cats = [c.strip() for c in target_categories.split(",") if c.strip()]
    resume_record = ResumeVersion(
        label=label.strip(),
        target_categories=cats,
        file_name=file.filename or "resume",
        file_path=str(dest_path),
        file_size=file_size,
        file_type=file_ext,
        extracted_text=extracted_text,
        is_primary=is_primary,
    )
    db.add(resume_record)
    db.commit()
    db.refresh(resume_record)

    log_activity(db, "SUCCESS", "RESUME_UPLOAD", f"Uploaded resume '{resume_record.label}' ({file_ext.upper()})")
    return resume_record


@router.put("/resumes/{resume_id}/primary")
def set_primary_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(ResumeVersion).filter(ResumeVersion.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume version not found")

    db.query(ResumeVersion).update({ResumeVersion.is_primary: False})
    resume.is_primary = True
    db.commit()
    return {"success": True, "primary_id": resume_id}


@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(ResumeVersion).filter(ResumeVersion.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume version not found")

    # Delete local file safely
    try:
        local_file = Path(resume.file_path)
        if local_file.exists():
            local_file.unlink()
    except Exception:
        pass

    db.delete(resume)
    db.commit()
    log_activity(db, "INFO", "RESUME_DELETE", f"Deleted resume version #{resume_id}")
    return {"success": True, "deleted_id": resume_id}
