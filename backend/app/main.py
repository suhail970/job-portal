from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.core.database import init_db
from app.workers.cron_scheduler import cron_scheduler
from app.api.v1 import (
    auth,
    colleges,
    drives,
    students,
    resume,
    prep_hub,
    interview,
    simulation,
    cron
)

logger = logging.getLogger("skillbridge.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables exist and demo seed data is present
    init_db()
    # Start background Hermes-style 3x daily cron scheduler
    cron_scheduler.start()
    yield
    # Shutdown
    cron_scheduler.stop()

app = FastAPI(
    title=settings.APP_NAME,
    description="SkillBridge AI: AI-Powered Career Guidance and Placement Preparation Ecosystem",
    version="1.0.0",
    lifespan=lifespan
)

# Global Unhandled Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception during {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "error_type": exc.__class__.__name__ if settings.DEBUG else "InternalServerError"
        }
    )


# CORS Middleware (Strict origins with regex fallback for local dev ports)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:[0-9]+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# Register API Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(colleges.router, prefix="/api/v1")
app.include_router(drives.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(resume.router, prefix="/api/v1")
app.include_router(prep_hub.router, prefix="/api/v1")
app.include_router(interview.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")
app.include_router(cron.router, prefix="/api/v1")

@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "default_ai_provider": settings.DEFAULT_AI_PROVIDER
    }

@app.post("/api/v1/ai/test-connection", tags=["AI Router"])
async def test_ai_connection(payload: dict):
    provider = payload.get("provider", "gemini")
    custom_config = payload.get("custom_config")
    from app.ai.router import ai_router
    messages = [{"role": "user", "content": "Respond with 'PONG' only."}]
    res = await ai_router.generate_completion(
        messages=messages,
        preferred_provider=provider,
        custom_config=custom_config
    )
    return {
        "status": "connected",
        "provider": "custom" if custom_config else provider,
        "model": custom_config.get("model") if custom_config else provider,
        "sample_output": res.strip()[:100]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

