"""
TriageIQ — FastAPI application entrypoint.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import tickets
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="AI-powered customer support ticket triage and routing system.",
    version="0.1.0",
)

# Allow the separate Next.js frontend (different origin) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)


@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "app": settings.app_name}
