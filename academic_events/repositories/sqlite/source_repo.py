from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from academic_events.models.conference import Source, SourceCreate, SourceType
from academic_events.repositories.interfaces import SourceRepository
from academic_events.repositories.sqlite.database import SQLiteDatabase


class SQLiteSourceRepository(SourceRepository):
    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def create(self, conference_id: str, data: SourceCreate) -> Source:
        src = Source(
            id=str(uuid.uuid4()),
            conference_id=conference_id,
            type=data.type,
            url=data.url,
            refresh_interval_hours=data.refresh_interval_hours or 24,
            refresh_enabled=data.refresh_enabled,
        )
        self._db.conn.execute(
            """INSERT INTO sources
               (id, conference_id, type, url, last_fetched_at, last_hash,
                fetch_status, refresh_interval_hours, refresh_enabled)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                src.id,
                src.conference_id,
                src.type.value,
                src.url,
                src.last_fetched_at,
                src.last_hash,
                src.fetch_status,
                src.refresh_interval_hours,
                int(src.refresh_enabled),
            ),
        )
        self._db.conn.commit()
        return src

    def _row_to_source(self, row) -> Source:
        return Source(
            id=row["id"],
            conference_id=row["conference_id"],
            type=SourceType(row["type"]),
            url=row["url"],
            last_fetched_at=row["last_fetched_at"],
            last_hash=row["last_hash"],
            fetch_status=row["fetch_status"],
            refresh_interval_hours=row["refresh_interval_hours"] or 24,
            refresh_enabled=bool(row["refresh_enabled"]),
        )

    def get(self, source_id: str) -> Source | None:
        row = self._db.conn.execute(
            "SELECT * FROM sources WHERE id = ?", (source_id,)
        ).fetchone()
        return self._row_to_source(row) if row else None

    def list_for_conference(self, conference_id: str) -> list[Source]:
        rows = self._db.conn.execute(
            "SELECT * FROM sources WHERE conference_id = ?", (conference_id,)
        ).fetchall()
        return [self._row_to_source(r) for r in rows]

    def update_fetch_status(
        self,
        source_id: str,
        *,
        last_fetched_at: str,
        last_hash: str | None = None,
        fetch_status: str = "success",
    ) -> None:
        self._db.conn.execute(
            """UPDATE sources SET last_fetched_at=?, last_hash=?, fetch_status=?
               WHERE id=?""",
            (last_fetched_at, last_hash, fetch_status, source_id),
        )
        self._db.conn.commit()

    def list_due_for_refresh(self) -> list[Source]:
        now = datetime.utcnow()
        rows = self._db.conn.execute(
            "SELECT * FROM sources WHERE refresh_enabled = 1"
        ).fetchall()
        due = []
        for row in rows:
            src = self._row_to_source(row)
            if src.last_fetched_at is None:
                due.append(src)
            else:
                last = datetime.fromisoformat(src.last_fetched_at)
                if now - last > timedelta(hours=src.refresh_interval_hours):
                    due.append(src)
        return due
