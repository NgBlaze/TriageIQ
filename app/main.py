"""
TriageIQ — FastAPI application entrypoint.
"""
from fastapi import FastAPI

from app.api import tickets
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    description="AI-powered customer support ticket triage and routing system.",
    version="0.1.0",
)

app.include_router(tickets.router)


@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "app": settings.app_name}
