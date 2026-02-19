from __future__ import annotations

import uuid

from academic_events.models.conference import (
    ImportantDate,
    ImportantDateCreate,
    ImportantDateType,
    UNIQUE_DATE_TYPES,
)
from academic_events.repositories.interfaces import ImportantDateRepository
from academic_events.repositories.sqlite.database import SQLiteDatabase

# Types that are always shown globally by default
_AUTO_GLOBAL_TYPES = frozenset({
    ImportantDateType.SUBMISSION_DEADLINE,
    ImportantDateType.CONFERENCE_START_DATE,
})


class DuplicateDateTypeError(ValueError):
    """Raised when trying to create a duplicate typed important date."""
    pass


class SQLiteImportantDateRepository(ImportantDateRepository):
    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def _get_existing_typed(self, conference_id: str, date_type: ImportantDateType) -> ImportantDate | None:
        """Return existing date of this type for the conference, or None."""
        row = self._db.conn.execute(
            "SELECT * FROM important_dates WHERE conference_id = ? AND type = ?",
            (conference_id, date_type.value),
        ).fetchone()
        return self._row_to_date(row) if row else None

    def create(self, conference_id: str, data: ImportantDateCreate) -> ImportantDate:
        """Create a new important date. Raises DuplicateDateTypeError if non-'other' type already exists."""
        if data.type in UNIQUE_DATE_TYPES:
            existing = self._get_existing_typed(conference_id, data.type)
            if existing is not None:
                raise DuplicateDateTypeError(
                    f"A date of type '{data.type.value}' already exists for this conference."
                )

        auto_global = data.type in _AUTO_GLOBAL_TYPES
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

    def upsert(self, conference_id: str, data: ImportantDateCreate) -> ImportantDate:
        """Upsert a date: for unique types, update existing if present; for 'other', always insert."""
        if data.type not in UNIQUE_DATE_TYPES:
            # 'other' type: always insert fresh
            return self.create(conference_id, data)

        auto_global = data.type in _AUTO_GLOBAL_TYPES
        display_globally = auto_global or data.display_globally

        existing = self._get_existing_typed(conference_id, data.type)
        if existing is not None:
            # Update in place
            self._db.conn.execute(
                """UPDATE important_dates
                   SET date_time = ?, timezone = ?, note = ?, display_globally = ?
                   WHERE id = ?""",
                (
                    data.date_time,
                    data.timezone,
                    data.note,
                    int(display_globally),
                    existing.id,
                ),
            )
            self._db.conn.commit()
            return self.get(existing.id)  # type: ignore[return-value]
        else:
            # Insert new
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
                  OR type IN ('submission_deadline', 'conference_start_date')
               ORDER BY date_time ASC""",
        ).fetchall()
        return [self._row_to_date(r) for r in rows]

    def delete(self, date_id: str) -> bool:
        cur = self._db.conn.execute(
            "DELETE FROM important_dates WHERE id = ?", (date_id,)
        )
        self._db.conn.commit()
        return cur.rowcount > 0
