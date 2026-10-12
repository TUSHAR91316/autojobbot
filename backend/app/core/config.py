import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
RESUMES_DIR = BASE_DIR / "resumes"
LOGS_DIR = BASE_DIR / "logs"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
BROWSER_PROFILE_DIR = DATA_DIR / "browser_profile"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESUMES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
BROWSER_PROFILE_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "ApplyPilot"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Network and Security - Loopback only
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'applypilot.db'}"
    
    # Automation defaults
    DEFAULT_APPLICATIONS_TARGET: int = 15
    DEFAULT_DELAY_SECONDS: float = 2.0
    DEFAULT_MIN_MATCH_SCORE: int = 60
    DEFAULT_MAX_FAILURES_BEFORE_STOP: int = 3
    
    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = DATA_DIR
    RESUMES_DIR: Path = RESUMES_DIR
    LOGS_DIR: Path = LOGS_DIR
    SCREENSHOTS_DIR: Path = SCREENSHOTS_DIR
    BROWSER_PROFILE_DIR: Path = BROWSER_PROFILE_DIR

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
