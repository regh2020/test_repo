"""Shared test fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from academic_events.repositories.sqlite import (
    SQLiteConferenceRepository,
    SQLiteDatabase,
    SQLiteDiscoveryRepository,
    SQLiteExtractionRepository,
    SQLiteImportantDateRepository,
    SQLiteSourceRepository,
)


@pytest.fixture
def db():
    database = SQLiteDatabase(":memory:")
    database.connect()
    yield database
    database.close()


@pytest.fixture
def conference_repo(db):
    return SQLiteConferenceRepository(db)


@pytest.fixture
def date_repo(db):
    return SQLiteImportantDateRepository(db)


@pytest.fixture
def source_repo(db):
    return SQLiteSourceRepository(db)


@pytest.fixture
def extraction_repo(db):
    return SQLiteExtractionRepository(db)


@pytest.fixture
def discovery_repo(db):
    return SQLiteDiscoveryRepository(db)


@pytest.fixture
def client(db):
    """TestClient wired to an in-memory DB."""
    from academic_events.api import dependencies as deps
    from academic_events.main import app

    # Override the DB singleton
    deps.get_db.cache_clear()
    original = deps.get_db

    def _override():
        return db

    deps.get_db = _override  # type: ignore[assignment]

    with TestClient(app) as c:
        yield c

    deps.get_db = original
