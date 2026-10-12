import pytest
from backend.app.services.duplicate import (
    normalize_job_url,
    normalize_string,
    check_for_duplicate_job,
)
from backend.app.models.job import JobListing


def test_url_normalization():
    url1 = "https://example.com/jobs/123/?utm_source=linkedin&utm_campaign=tracker#details"
    url2 = "https://example.com/jobs/123"
    assert normalize_job_url(url1) == "https://example.com/jobs/123"
    assert normalize_job_url(url2) == "https://example.com/jobs/123"


def test_duplicate_detection(db_session):
    job = JobListing(
        title="Senior Python Engineer",
        company="Tech Innovations Inc.",
        normalized_url="https://techinnovations.com/careers/101",
        source_job_id="ti-101",
        source_platform="remoteok"
    )
    db_session.add(job)
    db_session.commit()

    # 1. Duplicate by URL
    is_dup1, existing1, reason1 = check_for_duplicate_job(
        db_session,
        raw_url="https://techinnovations.com/careers/101?ref=jobboard",
        title="Different Title",
        company="Other Co"
    )
    assert is_dup1 is True
    assert existing1.id == job.id

    # 2. Duplicate by Source ID
    is_dup2, existing2, reason2 = check_for_duplicate_job(
        db_session,
        raw_url="https://other.com/job",
        title="Any Title",
        company="Any Co",
        source_job_id="ti-101"
    )
    assert is_dup2 is True

    # 3. Duplicate by Company and Title similarity
    is_dup3, existing3, reason3 = check_for_duplicate_job(
        db_session,
        raw_url="https://newlink.com/post",
        title="senior python engineer!",
        company="tech innovations inc."
    )
    assert is_dup3 is True

    # 4. Non-duplicate
    is_dup4, existing4, _ = check_for_duplicate_job(
        db_session,
        raw_url="https://different.com/job",
        title="Frontend React Developer",
        company="Tech Innovations Inc."
    )
    assert is_dup4 is False
