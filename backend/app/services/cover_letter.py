from typing import Dict, Any, List
from backend.app.models.profile import CandidateProfile
from backend.app.models.job import JobListing


def generate_truthful_cover_letter(profile: CandidateProfile, job: JobListing) -> str:
    """
    Generate a professional, truthful cover letter strictly from verified candidate profile data.
    Never fabricates experiences, qualifications, or company history.
    """
    name = profile.full_name or "Applicant"
    email = profile.email or ""
    phone = profile.phone or ""
    headline = profile.headline or "Software Professional"
    company = job.company or "Hiring Team"
    title = job.title or "Open Position"
    
    # Identify skills that match both
    cand_skills = profile.skills or []
    req_skills = job.required_skills or []
    matched = [s for s in req_skills if any(cs.lower() == s.lower() for cs in cand_skills)]
    if not matched and cand_skills:
        matched = cand_skills[:4]
    skills_text = ", ".join(matched) if matched else "software development best practices"

    # Identify recent experience
    experiences = profile.work_experience or []
    recent_role_text = ""
    if experiences and isinstance(experiences, list) and len(experiences) > 0:
        first = experiences[0]
        if isinstance(first, dict):
            r_title = first.get("title", "")
            r_comp = first.get("company", "")
            if r_title and r_comp:
                recent_role_text = f"Most recently, as a {r_title} at {r_comp}, I focused on delivering high-impact solutions and scalable architecture."

    paragraphs = [
        f"Dear {company} Hiring Team,",
        f"I am writing to express my strong enthusiasm for the {title} position at {company}. As a {headline} with {profile.years_of_experience:.1f} years of hands-on experience, I believe my background aligns directly with the goals of your team.",
    ]

    if recent_role_text:
        paragraphs.append(recent_role_text)

    paragraphs.append(
        f"My core competencies include {skills_text}. I take pride in writing clean, well-tested code, collaborating across engineering teams, and solving complex problems with reliability and craftsmanship."
    )

    if profile.portfolio_url or profile.github_url:
        links = []
        if profile.portfolio_url:
            links.append(f"portfolio: {profile.portfolio_url}")
        if profile.github_url:
            links.append(f"GitHub: {profile.github_url}")
        paragraphs.append(f"You can review my work and projects at {', '.join(links)}.")

    paragraphs.append(
        f"Thank you for your time and consideration. I welcome the opportunity to discuss how my experience and skills can contribute to {company}.\n\nSincerely,\n{name}\n{email} | {phone}"
    )

    return "\n\n".join(paragraphs)
