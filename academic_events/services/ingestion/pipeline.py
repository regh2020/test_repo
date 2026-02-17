"""Ingestion pipeline: fetch -> clean -> extract -> store."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from academic_events.models.conference import (
    ConferenceCreate,
    ConferenceUpdate,
    ExtractionRecord,
    ImportantDateCreate,
    ImportantDateType,
    Source,
    SourceCreate,
    SourceType,
)
from academic_events.repositories.interfaces import (
    ConferenceRepository,
    ExtractionRepository,
    ImportantDateRepository,
    SourceRepository,
)
from academic_events.services.ingestion.cleaner import clean_html, get_meta_and_structured
from academic_events.services.ingestion.extractor import extract_fields
from academic_events.services.ingestion.fetcher import FetchResult, fetch_url

logger = logging.getLogger(__name__)


class IngestionResult:
    def __init__(
        self,
        source: Source,
        records: list[ExtractionRecord],
        conference_id: str | None = None,
        error: str | None = None,
    ):
        self.source = source
        self.records = records
        self.conference_id = conference_id
        self.error = error


class IngestionPipeline:
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

    async def ingest_url(
        self, url: str, attach_to_conference_id: str | None = None
    ) -> IngestionResult:
        """Full pipeline: fetch URL, extract data, store results."""
        # 1. Fetch
        try:
            result = await fetch_url(url)
        except Exception as exc:
            logger.error("Fetch failed for %s: %s", url, exc)
            return IngestionResult(
                source=Source(
                    id=str(uuid.uuid4()),
                    type=SourceType.WEBSITE,
                    url=url,
                    fetch_status="error",
                ),
                records=[],
                error=str(exc),
            )

        # 2. Clean and extract metadata
        text = clean_html(result.html)
        meta = get_meta_and_structured(result.html)

        # 3. Create or reuse source
        source_data = SourceCreate(type=SourceType.WEBSITE, url=url)
        if attach_to_conference_id:
            source = self._sources.create(attach_to_conference_id, source_data)
        else:
            source = Source(
                id=str(uuid.uuid4()),
                type=SourceType.WEBSITE,
                url=url,
            )

        # 4. Extract fields
        records = extract_fields(text, meta, source.id)

        # 5. Store extraction records
        for rec in records:
            self._extractions.create(rec)

        # 6. Update source fetch status
        if attach_to_conference_id:
            self._sources.update_fetch_status(
                source.id,
                last_fetched_at=datetime.utcnow().isoformat(),
                last_hash=result.content_hash,
                fetch_status="success",
            )

        # 7. Auto-create conference if not attaching
        conference_id = attach_to_conference_id
        if conference_id is None:
            name = self._best_value(records, "name") or f"Conference from {url}"
            conf = self._conferences.create(
                ConferenceCreate(
                    name=name,
                    website_url=url,
                    city=self._best_value(records, "city"),
                    country=self._best_value(records, "country"),
                    venue=self._best_value(records, "venue"),
                    start_date=self._best_value(records, "start_date"),
                    end_date=self._best_value(records, "end_date"),
                    cfp_url=self._best_value(records, "cfp_url"),
                )
            )
            conference_id = conf.id
            # Now create the source attached to the conference
            source = self._sources.create(conference_id, source_data)
            self._sources.update_fetch_status(
                source.id,
                last_fetched_at=datetime.utcnow().isoformat(),
                last_hash=result.content_hash,
                fetch_status="success",
            )
        else:
            # Update existing conference with extracted data
            update_fields: dict = {}
            for field in ("name", "city", "country", "venue", "start_date", "end_date", "cfp_url", "website_url"):
                val = self._best_value(records, field)
                if val:
                    update_fields[field] = val
            if update_fields:
                self._conferences.update(
                    conference_id, ConferenceUpdate(**update_fields)
                )

        # 8. Create important dates from extraction records
        for rec in records:
            if rec.field_name.startswith("important_date:"):
                date_type_str = rec.field_name.split(":", 1)[1]
                try:
                    date_type = ImportantDateType(date_type_str)
                except ValueError:
                    date_type = ImportantDateType.OTHER
                self._dates.create(
                    conference_id,
                    ImportantDateCreate(
                        type=date_type,
                        date_time=rec.extracted_value,
                        note=rec.raw_snippet,
                    ),
                )

        logger.info(
            "Ingested %s: %d extraction records, conference=%s",
            url,
            len(records),
            conference_id,
        )
        return IngestionResult(
            source=source,
            records=records,
            conference_id=conference_id,
        )

    @staticmethod
    def _best_value(records: list[ExtractionRecord], field: str) -> str | None:
        """Pick highest-confidence value for a given field."""
        candidates = [r for r in records if r.field_name == field]
        if not candidates:
            return None
        candidates.sort(key=lambda r: r.confidence, reverse=True)
        return candidates[0].extracted_value
