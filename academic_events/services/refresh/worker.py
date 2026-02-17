"""Refresh worker: re-fetches sources and updates conference data."""

from __future__ import annotations

import logging
from datetime import datetime

from academic_events.models.conference import (
    ConferenceUpdate,
    ExtractionRecord,
    ImportantDateCreate,
    ImportantDateType,
)
from academic_events.repositories.interfaces import (
    ConferenceRepository,
    ExtractionRepository,
    ImportantDateRepository,
    SourceRepository,
)
from academic_events.services.ingestion.cleaner import clean_html, get_meta_and_structured
from academic_events.services.ingestion.extractor import extract_fields
from academic_events.services.ingestion.fetcher import fetch_url

logger = logging.getLogger(__name__)


class RefreshResult:
    def __init__(
        self,
        source_id: str,
        changed: bool,
        new_records: list[ExtractionRecord],
        error: str | None = None,
    ):
        self.source_id = source_id
        self.changed = changed
        self.new_records = new_records
        self.error = error


class RefreshWorker:
    def __init__(
        self,
        conferences: ConferenceRepository,
        sources: SourceRepository,
        dates: ImportantDateRepository,
        extractions: ExtractionRepository,
    ):
        self._conferences = conferences
        self._sources = sources
        self._dates = dates
        self._extractions = extractions

    async def refresh_source(self, source_id: str) -> RefreshResult:
        source = self._sources.get(source_id)
        if source is None:
            return RefreshResult(source_id=source_id, changed=False, new_records=[], error="Source not found")

        try:
            result = await fetch_url(source.url)
        except Exception as exc:
            self._sources.update_fetch_status(
                source_id,
                last_fetched_at=datetime.utcnow().isoformat(),
                fetch_status=f"error: {exc}",
            )
            return RefreshResult(source_id=source_id, changed=False, new_records=[], error=str(exc))

        changed = result.content_hash != source.last_hash

        self._sources.update_fetch_status(
            source_id,
            last_fetched_at=datetime.utcnow().isoformat(),
            last_hash=result.content_hash,
            fetch_status="success",
        )

        new_records: list[ExtractionRecord] = []
        if changed:
            text = clean_html(result.html)
            meta = get_meta_and_structured(result.html)
            new_records = extract_fields(text, meta, source_id)

            for rec in new_records:
                self._extractions.create(rec)

            # Update conference with best new values
            if source.conference_id:
                update_fields: dict = {}
                for field in ("name", "city", "country", "venue", "start_date", "end_date", "cfp_url"):
                    candidates = [r for r in new_records if r.field_name == field]
                    if candidates:
                        candidates.sort(key=lambda r: r.confidence, reverse=True)
                        # Only update if new confidence >= existing
                        old = self._extractions.list_for_field(source_id, field)
                        old_best = max((r.confidence for r in old if r not in new_records), default=0.0)
                        if candidates[0].confidence >= old_best:
                            update_fields[field] = candidates[0].extracted_value

                if update_fields:
                    self._conferences.update(
                        source.conference_id,
                        ConferenceUpdate(**update_fields),
                    )

                # Add any new important dates
                for rec in new_records:
                    if rec.field_name.startswith("important_date:"):
                        date_type_str = rec.field_name.split(":", 1)[1]
                        try:
                            date_type = ImportantDateType(date_type_str)
                        except ValueError:
                            date_type = ImportantDateType.OTHER
                        self._dates.create(
                            source.conference_id,
                            ImportantDateCreate(
                                type=date_type,
                                date_time=rec.extracted_value,
                                note=rec.raw_snippet,
                            ),
                        )

        logger.info("Refreshed source %s: changed=%s, records=%d", source_id, changed, len(new_records))
        return RefreshResult(source_id=source_id, changed=changed, new_records=new_records)

    async def refresh_all_due(self) -> list[RefreshResult]:
        due = self._sources.list_due_for_refresh()
        results = []
        for source in due:
            r = await self.refresh_source(source.id)
            results.append(r)
        return results

    async def refresh_conference(self, conference_id: str) -> list[RefreshResult]:
        sources = self._sources.list_for_conference(conference_id)
        results = []
        for source in sources:
            r = await self.refresh_source(source.id)
            results.append(r)
        return results
