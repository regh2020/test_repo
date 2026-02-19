from __future__ import annotations

import uuid
from datetime import datetime

from academic_events.models.discovery import PendingDiscovery
from academic_events.repositories.sqlite.database import SQLiteDatabase


class SQLitePendingDiscoveryRepository:
    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def _row_to_pending(self, row) -> PendingDiscovery:
        return PendingDiscovery(
            id=row["id"],
            url=row["url"],
            title=row["title"],
            snippet=row["snippet"],
            score=row["score"] or 0.0,
            source_type=row["source_type"] or "web",
            created_at=row["created_at"],
            status=row["status"] or "pending",
        )

    def create(self, url: str, title: str | None = None, snippet: str | None = None,
               score: float = 0.0, source_type: str = "web") -> PendingDiscovery:
        pd = PendingDiscovery(
            id=str(uuid.uuid4()),
            url=url,
            title=title,
            snippet=snippet,
            score=score,
            source_type=source_type,
            created_at=datetime.utcnow().isoformat(),
            status="pending",
        )
        self._db.conn.execute(
            """INSERT INTO pending_discoveries
               (id, url, title, snippet, score, source_type, created_at, status)
               VALUES (?,?,?,?,?,?,?,?)""",
            (pd.id, pd.url, pd.title, pd.snippet, pd.score, pd.source_type, pd.created_at, pd.status),
        )
        self._db.conn.commit()
        return pd

    def get(self, pending_id: str) -> PendingDiscovery | None:
        row = self._db.conn.execute(
            "SELECT * FROM pending_discoveries WHERE id = ?", (pending_id,)
        ).fetchone()
        return self._row_to_pending(row) if row else None

    def list_all(self) -> list[PendingDiscovery]:
        rows = self._db.conn.execute(
            "SELECT * FROM pending_discoveries ORDER BY created_at DESC"
        ).fetchall()
        return [self._row_to_pending(r) for r in rows]

    def update_status(self, pending_id: str, status: str) -> None:
        self._db.conn.execute(
            "UPDATE pending_discoveries SET status = ? WHERE id = ?",
            (status, pending_id),
        )
        self._db.conn.commit()

    def delete(self, pending_id: str) -> bool:
        cur = self._db.conn.execute(
            "DELETE FROM pending_discoveries WHERE id = ?", (pending_id,)
        )
        self._db.conn.commit()
        return cur.rowcount > 0
