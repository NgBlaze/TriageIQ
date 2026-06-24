"""
Vercel serverless entrypoint.

Vercel's @vercel/python runtime serves the ASGI callable named `app` found in
this module. We simply re-export the FastAPI app; all routing/config lives in
app/main.py so local (`uvicorn app.main:app`) and deployed environments run the
exact same application object.
"""
from app.main import app  # noqa: F401
