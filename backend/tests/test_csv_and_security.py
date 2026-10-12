import pytest
from backend.app.providers.csv_provider import parse_csv_jobs, export_jobs_to_csv


def test_csv_import_parsing():
    csv_data = """title,company,location,work_mode,employment_type,salary_min,salary_max,skills,url
Python Backend Engineer,Acme Corp,Remote,remote,full_time,120000,160000,"Python, FastAPI, SQL",https://acme.com/jobs/1
Staff Frontend Engineer,Globex,New York,hybrid,full_time,150000,190000,"React, TypeScript",https://globex.com/jobs/2
"""
    jobs = parse_csv_jobs(csv_data)
    assert len(jobs) == 2
    assert jobs[0]["title"] == "Python Backend Engineer"
    assert jobs[0]["company"] == "Acme Corp"
    assert jobs[0]["salary_min"] == 120000
    assert "FastAPI" in jobs[0]["required_skills"]
    assert jobs[1]["company"] == "Globex"


def test_csv_export():
    sample_jobs = [
        {
            "id": 1,
            "title": "Full Stack Dev",
            "company": "Initech",
            "location": "Remote",
            "work_mode": "remote",
            "employment_type": "full_time",
            "salary_min": 100000,
            "salary_max": 130000,
            "match_score": 85.5,
            "status": "QUEUED",
            "source_platform": "remoteok",
            "original_url": "https://initech.com/jobs/1"
        }
    ]
    csv_str = export_jobs_to_csv(sample_jobs)
    assert "Full Stack Dev" in csv_str
    assert "Initech" in csv_str
    assert "85.5" in csv_str


def test_api_health_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    assert res.json()["loopback_only"] is True


def test_api_profile_endpoint(client):
    res = client.get("/api/v1/profile")
    assert res.status_code == 200
    assert "full_name" in res.json()
