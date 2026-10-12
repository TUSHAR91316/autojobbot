from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{api_v1}/health"
    }
