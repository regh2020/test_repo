from __future__ import annotations

import json

from academic_events.models.discovery import DiscoveryCandidate, DiscoveryRun
from academic_events.repositories.interfaces import DiscoveryRepository
from academic_events.repositories.sqlite.database import SQLiteDatabase


class SQLiteDiscoveryRepository(DiscoveryRepository):
    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def create(self, run: DiscoveryRun) -> DiscoveryRun:
        self._db.conn.execute(
            """INSERT INTO discovery_runs (id, query, started_at, finished_at, candidates)
               VALUES (?,?,?,?,?)""",
            (
                run.id,
                run.query,
                run.started_at,
                run.finished_at,
                json.dumps([c.model_dump() for c in run.candidates]),
            ),
        )
        self._db.conn.commit()
        return run

    def _row_to_run(self, row) -> DiscoveryRun:
        candidates_raw = json.loads(row["candidates"]) if row["candidates"] else []
        return DiscoveryRun(
            id=row["id"],
            query=row["query"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            candidates=[DiscoveryCandidate(**c) for c in candidates_raw],
        )

    def get(self, run_id: str) -> DiscoveryRun | None:
        row = self._db.conn.execute(
            "SELECT * FROM discovery_runs WHERE id = ?", (run_id,)
        ).fetchone()
        return self._row_to_run(row) if row else None

    def list_all(self, limit: int = 50) -> list[DiscoveryRun]:
        rows = self._db.conn.execute(
            "SELECT * FROM discovery_runs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_run(r) for r in rows]
