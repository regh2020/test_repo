"""FastAPI dependency injection wiring."""

from __future__ import annotations

from functools import lru_cache

from academic_events.config import DATABASE_PATH
from academic_events.repositories.sqlite import (
    SQLiteConferenceRepository,
    SQLiteDatabase,
    SQLiteDiscoveryRepository,
    SQLiteExtractionRepository,
    SQLiteImportantDateRepository,
    SQLiteSourceRepository,
)
from academic_events.services.conference_service import ConferenceService
from academic_events.services.discovery.discovery_service import DiscoveryService
from academic_events.services.ingestion.pipeline import IngestionPipeline
from academic_events.services.refresh.worker import RefreshWorker


@lru_cache
def get_db() -> SQLiteDatabase:
    db = SQLiteDatabase(DATABASE_PATH)
    db.connect()
    return db


def get_conference_repo():
    return SQLiteConferenceRepository(get_db())


def get_date_repo():
    return SQLiteImportantDateRepository(get_db())


def get_source_repo():
    return SQLiteSourceRepository(get_db())


def get_extraction_repo():
    return SQLiteExtractionRepository(get_db())


def get_discovery_repo():
    return SQLiteDiscoveryRepository(get_db())


def get_conference_service() -> ConferenceService:
    return ConferenceService(
        conferences=get_conference_repo(),
        dates=get_date_repo(),
        sources=get_source_repo(),
    )


def get_ingestion_pipeline() -> IngestionPipeline:
    return IngestionPipeline(
        conferences=get_conference_repo(),
        sources=get_source_repo(),
        dates=get_date_repo(),
        extractions=get_extraction_repo(),
    )


def get_refresh_worker() -> RefreshWorker:
    return RefreshWorker(
        conferences=get_conference_repo(),
        sources=get_source_repo(),
        dates=get_date_repo(),
        extractions=get_extraction_repo(),
    )


def get_discovery_service() -> DiscoveryService:
    return DiscoveryService(discovery_repo=get_discovery_repo())
