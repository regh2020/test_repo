"""FastAPI application entry point."""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI

from academic_events.api.conferences import router as conferences_router
from academic_events.api.discovery import router as discovery_router
from academic_events.api.health import router as health_router
from academic_events.api.ingestion import router as ingestion_router
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

app.include_router(health_router)
app.include_router(conferences_router)
app.include_router(ingestion_router)
app.include_router(discovery_router)
app.include_router(refresh_router)
