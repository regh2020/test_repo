from __future__ import annotations

import json
import uuid
from datetime import datetime

from academic_events.models.conference import (
    Conference,
    ConferenceCreate,
    ConferenceStatus,
    ConferenceUpdate,
)
from academic_events.repositories.interfaces import ConferenceRepository
from academic_events.repositories.sqlite.database import SQLiteDatabase


class SQLiteConferenceRepository(ConferenceRepository):
    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def create(self, data: ConferenceCreate) -> Conference:
        conf = Conference(
            id=str(uuid.uuid4()),
            **data.model_dump(),
        )
        self._db.conn.execute(
            """INSERT INTO conferences
               (id, name, acronym, series, topics, city, country, venue,
                is_online, is_hybrid, start_date, end_date, cfp_url,
                website_url, status, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                conf.id,
                conf.name,
                conf.acronym,
                conf.series,
                json.dumps(conf.topics),
                conf.city,
                conf.country,
                conf.venue,
                int(conf.is_online),
                int(conf.is_hybrid),
                conf.start_date,
                conf.end_date,
                conf.cfp_url,
                conf.website_url,
                conf.status.value,
                conf.created_at,
                conf.updated_at,
            ),
        )
        self._db.conn.commit()
        return conf

    def _row_to_conference(self, row) -> Conference:
        return Conference(
            id=row["id"],
            name=row["name"],
            acronym=row["acronym"],
            series=row["series"],
            topics=json.loads(row["topics"]) if row["topics"] else [],
            city=row["city"],
            country=row["country"],
            venue=row["venue"],
            is_online=bool(row["is_online"]),
            is_hybrid=bool(row["is_hybrid"]),
            start_date=row["start_date"],
            end_date=row["end_date"],
            cfp_url=row["cfp_url"],
            website_url=row["website_url"],
            status=ConferenceStatus(row["status"]) if row["status"] else ConferenceStatus.UNKNOWN,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get(self, conference_id: str) -> Conference | None:
        cur = self._db.conn.execute(
            "SELECT * FROM conferences WHERE id = ?", (conference_id,)
        )
        row = cur.fetchone()
        return self._row_to_conference(row) if row else None

    def list_all(
        self,
        *,
        name: str | None = None,
        acronym: str | None = None,
        topic: str | None = None,
        city: str | None = None,
        country: str | None = None,
        status: str | None = None,
        start_after: str | None = None,
        start_before: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Conference]:
        clauses: list[str] = []
        params: list = []

        if name:
            clauses.append("name LIKE ?")
            params.append(f"%{name}%")
        if acronym:
            clauses.append("acronym LIKE ?")
            params.append(f"%{acronym}%")
        if topic:
            clauses.append("topics LIKE ?")
            params.append(f"%{topic}%")
        if city:
            clauses.append("city LIKE ?")
            params.append(f"%{city}%")
        if country:
            clauses.append("country LIKE ?")
            params.append(f"%{country}%")
        if status:
            clauses.append("status = ?")
            params.append(status)
        if start_after:
            clauses.append("start_date >= ?")
            params.append(start_after)
        if start_before:
            clauses.append("start_date <= ?")
            params.append(start_before)

        where = " AND ".join(clauses) if clauses else "1=1"
        query = f"SELECT * FROM conferences WHERE {where} ORDER BY start_date ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self._db.conn.execute(query, params).fetchall()
        return [self._row_to_conference(r) for r in rows]

    def update(self, conference_id: str, data: ConferenceUpdate) -> Conference | None:
        existing = self.get(conference_id)
        if existing is None:
            return None

        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return existing

        updates["updated_at"] = datetime.utcnow().isoformat()

        set_clauses = []
        params = []
        for key, value in updates.items():
            if key == "topics":
                set_clauses.append("topics = ?")
                params.append(json.dumps(value))
            elif key == "is_online" or key == "is_hybrid":
                set_clauses.append(f"{key} = ?")
                params.append(int(value))
            elif key == "status":
                set_clauses.append("status = ?")
                params.append(value.value if hasattr(value, "value") else value)
            else:
                set_clauses.append(f"{key} = ?")
                params.append(value)

        params.append(conference_id)
        self._db.conn.execute(
            f"UPDATE conferences SET {', '.join(set_clauses)} WHERE id = ?",
            params,
        )
        self._db.conn.commit()
        return self.get(conference_id)

    def delete(self, conference_id: str) -> bool:
        cur = self._db.conn.execute(
            "DELETE FROM conferences WHERE id = ?", (conference_id,)
        )
        self._db.conn.commit()
        return cur.rowcount > 0
