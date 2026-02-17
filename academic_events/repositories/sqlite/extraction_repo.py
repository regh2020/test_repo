from __future__ import annotations

from academic_events.models.conference import ExtractionMethod, ExtractionRecord
from academic_events.repositories.interfaces import ExtractionRepository
from academic_events.repositories.sqlite.database import SQLiteDatabase


class SQLiteExtractionRepository(ExtractionRepository):
    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def create(self, record: ExtractionRecord) -> ExtractionRecord:
        self._db.conn.execute(
            """INSERT INTO extraction_records
               (id, source_id, extracted_at, field_name, extracted_value,
                confidence, extraction_method, raw_snippet)
               VALUES (?,?,?,?,?,?,?,?)""",
            (
                record.id,
                record.source_id,
                record.extracted_at,
                record.field_name,
                record.extracted_value,
                record.confidence,
                record.extraction_method.value,
                record.raw_snippet,
            ),
        )
        self._db.conn.commit()
        return record

    def _row_to_record(self, row) -> ExtractionRecord:
        return ExtractionRecord(
            id=row["id"],
            source_id=row["source_id"],
            extracted_at=row["extracted_at"],
            field_name=row["field_name"],
            extracted_value=row["extracted_value"],
            confidence=row["confidence"],
            extraction_method=ExtractionMethod(row["extraction_method"]),
            raw_snippet=row["raw_snippet"],
        )

    def list_for_source(self, source_id: str) -> list[ExtractionRecord]:
        rows = self._db.conn.execute(
            "SELECT * FROM extraction_records WHERE source_id = ? ORDER BY extracted_at DESC",
            (source_id,),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]

    def list_for_field(
        self, source_id: str, field_name: str
    ) -> list[ExtractionRecord]:
        rows = self._db.conn.execute(
            """SELECT * FROM extraction_records
               WHERE source_id = ? AND field_name = ?
               ORDER BY extracted_at DESC""",
            (source_id, field_name),
        ).fetchall()
        return [self._row_to_record(r) for r in rows]
