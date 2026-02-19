"""SQLite database connection management and schema initialization."""

from __future__ import annotations

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS conferences (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    acronym TEXT,
    series TEXT,
    topics TEXT,  -- JSON array stored as text
    city TEXT,
    country TEXT,
    venue TEXT,
    is_online INTEGER DEFAULT 0,
    is_hybrid INTEGER DEFAULT 0,
    start_date TEXT,
    end_date TEXT,
    cfp_url TEXT,
    website_url TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    ai_summary TEXT,
    organizing_committee TEXT,  -- JSON array of Person objects
    scientific_committee TEXT   -- JSON array of Person objects
);

CREATE TABLE IF NOT EXISTS important_dates (
    id TEXT PRIMARY KEY,
    conference_id TEXT NOT NULL,
    type TEXT NOT NULL,
    date_time TEXT NOT NULL,
    timezone TEXT,
    note TEXT,
    display_globally INTEGER DEFAULT 0,
    FOREIGN KEY (conference_id) REFERENCES conferences(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS pending_discoveries (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    snippet TEXT,
    score REAL DEFAULT 0.0,
    source_type TEXT DEFAULT 'web',
    created_at TEXT NOT NULL,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    conference_id TEXT,
    type TEXT NOT NULL,
    url TEXT NOT NULL,
    last_fetched_at TEXT,
    last_hash TEXT,
    fetch_status TEXT,
    refresh_interval_hours INTEGER DEFAULT 24,
    refresh_enabled INTEGER DEFAULT 1,
    FOREIGN KEY (conference_id) REFERENCES conferences(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS extraction_records (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    extracted_at TEXT NOT NULL,
    field_name TEXT NOT NULL,
    extracted_value TEXT NOT NULL,
    confidence REAL NOT NULL,
    extraction_method TEXT NOT NULL,
    raw_snippet TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS discovery_runs (
    id TEXT PRIMARY KEY,
    query TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    candidates TEXT  -- JSON array stored as text
);

CREATE INDEX IF NOT EXISTS idx_conferences_name ON conferences(name);
CREATE INDEX IF NOT EXISTS idx_conferences_status ON conferences(status);
CREATE INDEX IF NOT EXISTS idx_conferences_start_date ON conferences(start_date);
CREATE INDEX IF NOT EXISTS idx_important_dates_conference ON important_dates(conference_id);
CREATE INDEX IF NOT EXISTS idx_sources_conference ON sources(conference_id);
CREATE INDEX IF NOT EXISTS idx_extraction_records_source ON extraction_records(source_id);
"""


class SQLiteDatabase:
    def __init__(self, db_path: str | Path = ":memory:"):
        self._db_path = str(db_path)
        self._conn: sqlite3.Connection | None = None

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            if self._db_path != ":memory:":
                Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.executescript(_SCHEMA)
            self._run_migrations()
        return self._conn

    def _run_migrations(self) -> None:
        """Apply incremental schema migrations for existing databases."""
        assert self._conn is not None

        # --- important_dates table migrations ---
        date_cols = {
            row[1]
            for row in self._conn.execute("PRAGMA table_info(important_dates)")
        }
        if "display_globally" not in date_cols:
            self._conn.execute(
                "ALTER TABLE important_dates ADD COLUMN display_globally INTEGER DEFAULT 0"
            )

        # --- conferences table migrations ---
        conf_cols = {
            row[1]
            for row in self._conn.execute("PRAGMA table_info(conferences)")
        }
        if "ai_summary" not in conf_cols:
            self._conn.execute("ALTER TABLE conferences ADD COLUMN ai_summary TEXT")
        if "organizing_committee" not in conf_cols:
            self._conn.execute(
                "ALTER TABLE conferences ADD COLUMN organizing_committee TEXT"
            )
        if "scientific_committee" not in conf_cols:
            self._conn.execute(
                "ALTER TABLE conferences ADD COLUMN scientific_committee TEXT"
            )

        # Migrate 'unknown' and 'upcoming' statuses
        self._conn.execute(
            "UPDATE conferences SET status = 'active' WHERE status IN ('unknown', 'upcoming')"
        )

        # --- Migrate old ImportantDateType values to canonical names ---
        _TYPE_RENAMES = {
            "notification": "notification_date",
            "camera_ready": "camera_ready_deadline",
            "conference_start": "conference_start_date",
            "conference_end": "conference_end_date",
            "early_registration": "registration_deadline",
        }
        for old_val, new_val in _TYPE_RENAMES.items():
            self._conn.execute(
                "UPDATE important_dates SET type = ? WHERE type = ?",
                (new_val, old_val),
            )

        # --- Remove duplicate typed dates, keeping one entry per (conference_id, type) ---
        # Uses EXISTS subquery to avoid requiring window function support.
        self._conn.execute(
            """DELETE FROM important_dates
               WHERE type != 'other'
                 AND rowid NOT IN (
                   SELECT MIN(rowid)
                   FROM important_dates
                   WHERE type != 'other'
                   GROUP BY conference_id, type
                 )"""
        )

        # --- Add unique partial index for non-'other' dates ---
        self._conn.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_important_dates_conference_type
               ON important_dates(conference_id, type)
               WHERE type != 'other'"""
        )

        self._conn.commit()

    @property
    def conn(self) -> sqlite3.Connection:
        return self.connect()

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None
