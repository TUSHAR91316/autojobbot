from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from backend.app.core.config import settings
from backend.app.database.session import engine, Base
import backend.app.models  # Ensure all models are registered
from backend.app.api import (
    routes_health,
    routes_profile,
    routes_jobs,
    routes_queue,
    routes_automation,
    routes_history,
    routes_logs,
    routes_settings,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown browser if open
    from backend.app.automation.browser import browser_manager
    await browser_manager.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Local AI-Powered Job Application Assistant API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Strict loopback CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def loopback_security_middleware(request: Request, call_next):
    """
    Localhost-only enforcement:
    Ensure requests originate from local loopback interfaces.
    """
    client_host = request.client.host if request.client else ""
    if client_host not in ["127.0.0.1", "localhost", "::1", "testclient"]:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Access forbidden: ApplyPilot only accepts connections from local loopback (127.0.0.1)."}
        )
    return await call_next(request)


# Register API Routers
api_v1 = settings.API_V1_STR
app.include_router(routes_health.router, prefix=api_v1)
app.include_router(routes_profile.router, prefix=api_v1)
app.include_router(routes_jobs.router, prefix=api_v1)
app.include_router(routes_queue.router, prefix=api_v1)
app.include_router(routes_automation.router, prefix=api_v1)
app.include_router(routes_history.router, prefix=api_v1)
app.include_router(routes_logs.router, prefix=api_v1)
app.include_router(routes_settings.router, prefix=api_v1)

from fastapi.staticfiles import StaticFiles
from backend.app.core.config import SCREENSHOTS_DIR
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")

@app.get("/demo-career-portal", response_class=HTMLResponse)
def demo_career_portal(request: Request, job: str = "demo-position"):
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Careers Portal — ApplyPilot Automation Demo</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: #0f172a;
      color: #f8fafc;
      margin: 0;
      padding: 40px 20px;
      display: flex;
      justify-content: center;
    }}
    .container {{
      max-width: 640px;
      width: 100%;
      background: #1e293b;
      padding: 32px;
      border-radius: 16px;
      border: 1px solid #334155;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }}
    h1 {{ font-size: 20px; margin-top: 0; color: #38bdf8; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; background: rgba(56, 189, 248, 0.15); color: #38bdf8; font-size: 11px; font-weight: 600; margin-bottom: 20px; }}
    label {{ display: block; font-size: 12px; font-weight: 600; margin-top: 14px; margin-bottom: 6px; color: #cbd5e1; }}
    input, textarea {{
      width: 100%;
      box-sizing: border-box;
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid #475569;
      background: #0f172a;
      color: #f8fafc;
      font-size: 13px;
      outline: none;
      transition: border-color 0.2s;
    }}
    input:focus, textarea:focus {{ border-color: #38bdf8; }}
    input[type="file"] {{ padding: 8px; font-size: 11px; }}
    button {{
      margin-top: 24px;
      width: 100%;
      padding: 12px;
      border-radius: 8px;
      border: none;
      background: #38bdf8;
      color: #0f172a;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.2s;
    }}
    button:hover {{ background: #7dd3fc; }}
    #status-msg {{
      display: none;
      margin-top: 20px;
      padding: 16px;
      border-radius: 8px;
      background: rgba(34, 197, 94, 0.15);
      border: 1px solid rgba(34, 197, 94, 0.4);
      color: #4ade80;
      font-size: 13px;
      font-weight: 600;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="container">
    <span class="badge">ApplyPilot Live Browser Target • Position: {job}</span>
    <h1>Job Application: Senior Software Engineer</h1>
    <p style="font-size: 12px; color: #94a3b8; line-height: 1.5; margin-bottom: 24px;">
      This is a local testing portal. The ApplyPilot browser bot will autofill your personal credentials, attach your resume, fill the cover letter, and submit this application directly in front of you.
    </p>

    <form id="app-form" onsubmit="event.preventDefault(); document.getElementById('status-msg').style.display='block'; document.getElementById('submit-btn').innerText='Application Submitted!'; document.getElementById('submit-btn').disabled=true;">
      <label for="full_name">Full Name *</label>
      <input type="text" id="full_name" name="full_name" placeholder="Your Full Name" required>

      <label for="email">Email Address *</label>
      <input type="email" id="email" name="email" placeholder="you@domain.com" required>

      <label for="phone">Phone Number</label>
      <input type="tel" id="phone" name="phone" placeholder="+1 (555) 000-0000">

      <label for="location">Current Location</label>
      <input type="text" id="location" name="location" placeholder="City, Country">

      <label for="linkedin">LinkedIn Profile URL</label>
      <input type="url" id="linkedin" name="linkedin" placeholder="https://linkedin.com/in/username">

      <label for="resume">Attach Resume (PDF, Word, LaTeX, Text)</label>
      <input type="file" id="resume" name="resume">

      <label for="cover_letter">Cover Letter / Motivation</label>
      <textarea id="cover_letter" name="cover_letter" rows="4" placeholder="Why are you a fit for this role?"></textarea>

      <button type="submit" id="submit-btn">Submit Application</button>

      <div id="status-msg">
        🎉 Application Submitted Successfully! Recorded in local automation session.
      </div>
    </form>
  </div>
</body>
</html>
"""
    return HTMLResponse(content=html_content)


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{api_v1}/health",
        "demo_portal": "/demo-career-portal"
    }
