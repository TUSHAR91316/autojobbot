#!/usr/bin/env python3
"""
Universal Multi-Jobsite Autonomous Playwright Robot (LinkedIn, Indeed, Naukri, All)
Usage:
    python run_jobbot.py --platform linkedin --keywords "Python Developer" --location "Bengaluru" --max-jobs 5 --delay 4
    python run_jobbot.py --platform indeed --keywords "Full Stack Engineer" --location "India" --max-jobs 5
    python run_jobbot.py --platform naukri --keywords "Python Developer" --location "Bengaluru" --max-jobs 5
    python run_jobbot.py --platform all --keywords "Backend Engineer" --location "Bengaluru" --non-stop
"""
import sys
import os
import asyncio
import argparse
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.database.session import SessionLocal
from backend.app.models.profile import CandidateProfile
from backend.app.models.resume import ResumeVersion
from backend.app.automation.simulator import execute_universal_job_search_and_apply


async def main():
    parser = argparse.ArgumentParser(description="ApplyPilot Universal Multi-Jobsite Playwright Robot")
    parser.add_argument("--platform", type=str, default="linkedin", choices=["linkedin", "indeed", "naukri", "all", "multi_portal"],
                        help="Target jobsite: linkedin, indeed, naukri, or all (default: linkedin)")
    parser.add_argument("--keywords", type=str, default="Python Developer", help="Search job title or keywords")
    parser.add_argument("--location", type=str, default="Bengaluru, Karnataka, India", help="Search location (e.g. Bengaluru, India, Remote)")
    parser.add_argument("--max-jobs", type=int, default=5, help="Maximum jobs to apply for (default: 5)")
    parser.add_argument("--delay", type=float, default=4.0, help="Base delay in seconds between job applications (default: 4.0s)")
    parser.add_argument("--non-stop", action="store_true", help="Run in continuous non-stop mode with anti-ban cooldown breathers")
    parser.add_argument("--review", action="store_true", help="Stage applications for review instead of auto-submitting")
    args = parser.parse_args()

    print("\n" + "="*70)
    print("🚀 ApplyPilot: Universal Multi-Jobsite Autonomous Robot")
    print("="*70)
    print(f"🌐 Platform: {args.platform.upper()}")
    print(f"🎯 Keywords: {args.keywords}")
    print(f"📍 Location: {args.location}")
    print(f"🔢 Target Jobs: {args.max_jobs} {'(Continuous Non-Stop Mode)' if args.non_stop else ''}")
    print(f"⏱️ Base Delay: {args.delay}s (+ natural anti-ban human jitter)")
    print(f"⚙️ Execution Mode: {'Staged Review' if args.review else 'Auto-Submit'}")
    print("="*70)

    db = SessionLocal()
    try:
        profile = db.query(CandidateProfile).first()
        if not profile:
            print("⚠️ No profile found in database. Using default Alex Mercer profile.")
            profile = CandidateProfile(
                full_name="Alex Mercer",
                email="alex.mercer@example.com",
                phone="+91 9876543210",
                current_location=args.location,
                years_of_experience=5.0,
                skills=["Python", "FastAPI", "React", "TypeScript", "SQLAlchemy", "Docker"],
            )

        primary_resume = db.query(ResumeVersion).filter(ResumeVersion.is_primary == True).first()
        if not primary_resume:
            primary_resume = db.query(ResumeVersion).first()

        resume_path = primary_resume.file_path if primary_resume else None
        print(f"👤 Candidate: {profile.full_name} ({profile.email})")
        print(f"📄 Active Resume: {primary_resume.label if primary_resume else 'None'}")
        print("🖥️ Launching visible desktop Chromium browser window...")

        cover_letter = (
            f"Dear Hiring Team,\n\n"
            f"I am writing to express my strong interest in this position. With over {int(profile.years_of_experience or 5)} years "
            f"of experience building high-performance systems and full-stack applications, I am eager to contribute.\n\n"
            f"Sincerely,\n{profile.full_name}"
        )

        res = await execute_universal_job_search_and_apply(
            platform=args.platform,
            keywords=args.keywords,
            location=args.location,
            profile=profile,
            resume_path=resume_path,
            cover_letter=cover_letter,
            max_jobs=args.max_jobs,
            delay_seconds=args.delay,
            auto_submit=not args.review,
            non_stop=args.non_stop,
        )

        print("\n" + "="*70)
        print("📊 Execution Summary:")
        print(f"Outcome: {res.get('outcome')}")
        print(f"Message: {res.get('message', 'Completed successfully')}")
        print(f"Total Applied: {res.get('jobs_applied', 0)} / {args.max_jobs}")
        print("="*70)

        for app in res.get("applications", []):
            print(f"  [{app.get('index')}] {app.get('title')} at {app.get('company')} -> {app.get('outcome')}")
            print(f"      Steps: {len(app.get('steps_completed', []))} completed")
            if app.get("screenshot"):
                print(f"      Screenshot: {app.get('screenshot')}")

        print("\n✨ Done! All applications saved to database with evidence screenshots.")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
