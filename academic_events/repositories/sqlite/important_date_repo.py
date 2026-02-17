from __future__ import annotations

import uuid

from academic_events.models.conference import (
    ImportantDate,
    ImportantDateCreate,
    ImportantDateType,
)
from academic_events.repositories.interfaces import ImportantDateRepository
from academic_events.repositories.sqlite.database import SQLiteDatabase


class SQLiteImportantDateRepository(ImportantDateRepository):
    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def create(self, conference_id: str, data: ImportantDateCreate) -> ImportantDate:
        dt = ImportantDate(
            id=str(uuid.uuid4()),
            conference_id=conference_id,
            type=data.type,
            date_time=data.date_time,
            timezone=data.timezone,
            note=data.note,
        )
        self._db.conn.execute(
            """INSERT INTO important_dates (id, conference_id, type, date_time, timezone, note)
               VALUES (?,?,?,?,?,?)""",
            (dt.id, dt.conference_id, dt.type.value, dt.date_time, dt.timezone, dt.note),
        )
        self._db.conn.commit()
        return dt

    def _row_to_date(self, row) -> ImportantDate:
        return ImportantDate(
            id=row["id"],
            conference_id=row["conference_id"],
            type=ImportantDateType(row["type"]),
            date_time=row["date_time"],
            timezone=row["timezone"],
            note=row["note"],
        )

    def list_for_conference(self, conference_id: str) -> list[ImportantDate]:
        rows = self._db.conn.execute(
            "SELECT * FROM important_dates WHERE conference_id = ? ORDER BY date_time ASC",
            (conference_id,),
        ).fetchall()
        return [self._row_to_date(r) for r in rows]

    def delete(self, date_id: str) -> bool:
        cur = self._db.conn.execute(
            "DELETE FROM important_dates WHERE id = ?", (date_id,)
        )
        self._db.conn.commit()
        return cur.rowcount > 0
