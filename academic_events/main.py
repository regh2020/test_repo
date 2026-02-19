"""FastAPI application entry point."""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from academic_events.api.conferences import router as conferences_router
from academic_events.api.discovery import router as discovery_router
from academic_events.api.health import router as health_router
from academic_events.api.important_dates import router as important_dates_router
from academic_events.api.ingestion import router as ingestion_router
from academic_events.api.pending_discoveries import router as pending_discoveries_router
from academic_events.api.refresh import router as refresh_router

# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)

app = FastAPI(
    title="Academic Events Registry",
    description="Backend API for managing academic conferences and events",
    version="0.1.0",
)

# Allow the Vite dev server (and any localhost port) to call the API without
# CORS errors. Restrict origins in production by setting CORS_ORIGINS in the
# environment to a comma-separated list of allowed URLs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(conferences_router)
app.include_router(important_dates_router)
app.include_router(ingestion_router)
app.include_router(discovery_router)
app.include_router(pending_discoveries_router)
app.include_router(refresh_router)
