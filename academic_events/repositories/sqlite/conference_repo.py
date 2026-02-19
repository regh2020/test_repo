from __future__ import annotations

import json
import uuid
from datetime import datetime

from academic_events.models.conference import (
    Conference,
    ConferenceCreate,
    ConferenceStatus,
    ConferenceUpdate,
    Person,
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
                website_url, status, created_at, updated_at,
                ai_summary, organizing_committee, scientific_committee)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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
                conf.ai_summary,
                json.dumps([p.model_dump() for p in conf.organizing_committee]) if conf.organizing_committee else None,
                json.dumps([p.model_dump() for p in conf.scientific_committee]) if conf.scientific_committee else None,
            ),
        )
        self._db.conn.commit()
        return conf

    def _row_to_conference(self, row, *, submission_deadline: str | None = None) -> Conference:
        keys = row.keys() if hasattr(row, "keys") else []
        sd = submission_deadline
        if sd is None and "submission_deadline" in keys:
            sd = row["submission_deadline"]

        # Parse committee JSON columns safely
        def _parse_people(raw: str | None) -> list[Person]:
            if not raw:
                return []
            try:
                items = json.loads(raw)
                return [Person(**item) for item in items if isinstance(item, dict)]
            except (json.JSONDecodeError, TypeError, ValueError):
                return []

        # Handle rows that may not have new columns (pre-migration)
        ai_summary = row["ai_summary"] if "ai_summary" in keys else None
        organizing_raw = row["organizing_committee"] if "organizing_committee" in keys else None
        scientific_raw = row["scientific_committee"] if "scientific_committee" in keys else None

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
            status=ConferenceStatus(row["status"]) if row["status"] else ConferenceStatus.ACTIVE,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            submission_deadline=sd,
            ai_summary=ai_summary,
            organizing_committee=_parse_people(organizing_raw),
            scientific_committee=_parse_people(scientific_raw),
        )

    def get(self, conference_id: str) -> Conference | None:
        cur = self._db.conn.execute(
            "SELECT * FROM conferences WHERE id = ?", (conference_id,)
        )
        row = cur.fetchone()
        return self._row_to_conference(row) if row else None

    # Subquery to get the earliest upcoming submission deadline for a conference
    _SUBMISSION_DEADLINE_SUBQUERY = (
        "(SELECT MIN(date_time) FROM important_dates "
        " WHERE conference_id = c.id AND type = 'submission_deadline'"
        " AND date_time >= datetime('now'))"
    )

    # Allowed column names for sorting (whitelist to prevent SQL injection)
    _SORT_COLUMNS: dict[str, str] = {
        "name": "c.name",
        "acronym": "c.acronym",
        "location": "c.city",
        "start_date": "c.start_date",
        "status": "c.status",
        "updated_at": "c.updated_at",
    }

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
        sort_by: str | None = None,
        sort_order: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> list[Conference]:
        clauses: list[str] = []
        params: list = []

        if name:
            clauses.append("c.name LIKE ?")
            params.append(f"%{name}%")
        if acronym:
            clauses.append("c.acronym LIKE ?")
            params.append(f"%{acronym}%")
        if topic:
            clauses.append("c.topics LIKE ?")
            params.append(f"%{topic}%")
        if city:
            clauses.append("c.city LIKE ?")
            params.append(f"%{city}%")
        if country:
            clauses.append("c.country LIKE ?")
            params.append(f"%{country}%")
        if status:
            clauses.append("c.status = ?")
            params.append(status)
        if start_after:
            clauses.append("c.start_date >= ?")
            params.append(start_after)
        if start_before:
            clauses.append("c.start_date <= ?")
            params.append(start_before)

        where = " AND ".join(clauses) if clauses else "1=1"
        direction = "DESC" if sort_order.lower() == "desc" else "ASC"

        if sort_by == "submission_deadline":
            order_expr = f"{self._SUBMISSION_DEADLINE_SUBQUERY} {direction} NULLS LAST"
        else:
            sort_col = self._SORT_COLUMNS.get(sort_by or "", "c.start_date")
            order_expr = f"{sort_col} {direction}"

        query = (
            f"SELECT c.*, {self._SUBMISSION_DEADLINE_SUBQUERY} AS submission_deadline "
            f"FROM conferences c WHERE {where} "
            f"ORDER BY {order_expr} LIMIT ? OFFSET ?"
        )
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
            elif key in ("organizing_committee", "scientific_committee"):
                set_clauses.append(f"{key} = ?")
                if value is None:
                    params.append(None)
                else:
                    params.append(
                        json.dumps([p.model_dump() if hasattr(p, "model_dump") else p for p in value])
                    )
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
