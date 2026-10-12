import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from backend.app.database.session import Base, get_db
from backend.app.main import app
from backend.app.models.profile import CandidateProfile
from backend.app.models.settings import JobPreferences, AutomationSettings

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Initialize basic seed data
    profile = CandidateProfile(
        full_name="Test Engineer",
        email="test@example.com",
        headline="Senior Python Developer",
        skills=["Python", "FastAPI", "React", "TypeScript", "SQLAlchemy"],
        years_of_experience=4.0,
        experience_level="senior",
        preferred_job_titles=["Software Engineer", "Backend Developer"],
        preferred_locations=["Remote"],
        remote_preference="remote_only",
        employment_types=["full_time"]
    )
    prefs = JobPreferences(
        title_keywords=["Software Engineer", "Backend Developer"],
        negative_keywords=["Sales", "Marketing"],
        preferred_locations=["Remote"],
        remote_only=True,
        required_skills=["Python", "FastAPI"]
    )
    settings = AutomationSettings(
        target_applications_per_session=5,
        delay_between_attempts_sec=1.0,
        min_match_score=60,
        simulation_mode=True
    )
    session.add(profile)
    session.add(prefs)
    session.add(settings)
    session.commit()
    
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
