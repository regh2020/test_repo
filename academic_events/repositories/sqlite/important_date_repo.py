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
        # Submission deadlines and conference starts are always globally displayed
        auto_global = data.type in (
            ImportantDateType.SUBMISSION_DEADLINE,
            ImportantDateType.CONFERENCE_START,
        )
        display_globally = auto_global or data.display_globally
        dt = ImportantDate(
            id=str(uuid.uuid4()),
            conference_id=conference_id,
            type=data.type,
            date_time=data.date_time,
            timezone=data.timezone,
            note=data.note,
            display_globally=display_globally,
        )
        self._db.conn.execute(
            """INSERT INTO important_dates
               (id, conference_id, type, date_time, timezone, note, display_globally)
               VALUES (?,?,?,?,?,?,?)""",
            (
                dt.id,
                dt.conference_id,
                dt.type.value,
                dt.date_time,
                dt.timezone,
                dt.note,
                int(dt.display_globally),
            ),
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
            display_globally=bool(row["display_globally"]) if row["display_globally"] is not None else False,
        )

    def get(self, date_id: str) -> ImportantDate | None:
        cur = self._db.conn.execute(
            "SELECT * FROM important_dates WHERE id = ?", (date_id,)
        )
        row = cur.fetchone()
        return self._row_to_date(row) if row else None

    def list_for_conference(self, conference_id: str) -> list[ImportantDate]:
        rows = self._db.conn.execute(
            "SELECT * FROM important_dates WHERE conference_id = ? ORDER BY date_time ASC",
            (conference_id,),
        ).fetchall()
        return [self._row_to_date(r) for r in rows]

    def update_display_globally(self, date_id: str, display_globally: bool) -> ImportantDate | None:
        self._db.conn.execute(
            "UPDATE important_dates SET display_globally = ? WHERE id = ?",
            (int(display_globally), date_id),
        )
        self._db.conn.commit()
        return self.get(date_id)

    def list_global(self) -> list[ImportantDate]:
        """Return all dates shown in the global Important Dates screen."""
        rows = self._db.conn.execute(
            """SELECT * FROM important_dates
               WHERE display_globally = 1
                  OR type IN ('submission_deadline', 'conference_start')
               ORDER BY date_time ASC""",
        ).fetchall()
        return [self._row_to_date(r) for r in rows]

    def delete(self, date_id: str) -> bool:
        cur = self._db.conn.execute(
            "DELETE FROM important_dates WHERE id = ?", (date_id,)
        )
        self._db.conn.commit()
        return cur.rowcount > 0
