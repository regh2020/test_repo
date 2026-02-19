"""Ingestion pipeline: fetch -> clean -> extract (AI + heuristic) -> follow links -> store."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

from academic_events.config import AI_EXTRACTION_ENABLED, ANTHROPIC_API_KEY, MAX_LINKED_PAGES
from academic_events.models.conference import (
    ConferenceCreate,
    ConferenceUpdate,
    ExtractionRecord,
    ImportantDateCreate,
    ImportantDateType,
    Person,
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
from academic_events.services.ingestion.ai_extractor import ai_extract_fields
from academic_events.services.ingestion.cleaner import clean_html, get_meta_and_structured
from academic_events.services.ingestion.extractor import extract_fields
from academic_events.services.ingestion.fetcher import FetchResult, fetch_url
from academic_events.services.ingestion.link_follower import follow_relevant_links

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
        """Full pipeline: fetch URL, extract data with AI + heuristics, follow links, store results."""
        # 1. Fetch main page
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

        # 2. Clean and extract metadata (heuristic)
        text = clean_html(result.html)
        meta = get_meta_and_structured(result.html)

        # 3. Run heuristic extraction as baseline
        placeholder_source_id = str(uuid.uuid4())
        heuristic_records = extract_fields(text, meta, placeholder_source_id)

        # 4. Run AI extraction on the main page
        ai_records: list[ExtractionRecord] = []
        ai_relevant_links: list[dict] = []
        ai_summary: str | None = None
        ai_organizing_committee: list[Person] = []
        ai_scientific_committee: list[Person] = []
        if AI_EXTRACTION_ENABLED:
            ai_records, ai_relevant_links, ai_summary, ai_organizing_committee, ai_scientific_committee = await ai_extract_fields(
                text=text,
                page_url=url,
                source_id=placeholder_source_id,
                api_key=ANTHROPIC_API_KEY,
            )

            # 5. Conditionally follow deep links only if core fields are missing.
            # This prevents wasteful crawling when the main page is sufficient.
            merged_so_far = self._merge_records(ai_records, heuristic_records)
            if not self._has_core_fields(merged_so_far):
                # Core data incomplete — follow limited deep links (max 3)
                # that are most likely to contain dates or CFP info.
                linked_pages = await follow_relevant_links(
                    html=result.html,
                    base_url=url,
                    ai_suggested_links=ai_relevant_links,
                    max_pages=min(MAX_LINKED_PAGES, 3),
                )

                for linked in linked_pages:
                    page_records, _, _, page_org, page_sci = await ai_extract_fields(
                        text=linked["text"],
                        page_url=linked["url"],
                        source_id=placeholder_source_id,
                        api_key=ANTHROPIC_API_KEY,
                    )
                    ai_records.extend(page_records)
                    if page_org:
                        ai_organizing_committee.extend(page_org)
                    if page_sci:
                        ai_scientific_committee.extend(page_sci)
                    # Stop early once core fields are satisfied
                    if self._has_core_fields(self._merge_records(ai_records, heuristic_records)):
                        logger.info("Core fields satisfied after deep link, stopping crawl early")
                        break
            else:
                logger.info("Core fields present on main page — skipping deep link crawl")

        # 6. Merge records: AI records take priority (higher confidence),
        #    but keep heuristic records for fields AI didn't find
        records = self._merge_records(ai_records, heuristic_records)

        # 7. Create source and conference, then store records with correct source_id
        source_data = SourceCreate(type=SourceType.WEBSITE, url=url)
        conference_id = attach_to_conference_id

        if conference_id is None:
            # Auto-create conference from extracted data
            name = self._best_value(records, "name") or f"Conference from {url}"
            topics_raw = self._best_value(records, "topics")
            topics: list[str] = []
            if topics_raw:
                try:
                    topics = json.loads(topics_raw)
                except (json.JSONDecodeError, TypeError):
                    pass

            conf = self._conferences.create(
                ConferenceCreate(
                    name=name,
                    acronym=self._best_value(records, "acronym"),
                    series=self._best_value(records, "series"),
                    topics=topics,
                    website_url=url,
                    city=self._best_value(records, "city"),
                    country=self._best_value(records, "country"),
                    venue=self._best_value(records, "venue"),
                    is_online=self._best_value(records, "is_online") == "true",
                    is_hybrid=self._best_value(records, "is_hybrid") == "true",
                    start_date=self._best_value(records, "start_date"),
                    end_date=self._best_value(records, "end_date"),
                    cfp_url=self._best_value(records, "cfp_url"),
                    ai_summary=ai_summary,
                    organizing_committee=ai_organizing_committee,
                    scientific_committee=ai_scientific_committee,
                )
            )
            conference_id = conf.id

        # Create source attached to the conference
        source = self._sources.create(conference_id, source_data)
        self._sources.update_fetch_status(
            source.id,
            last_fetched_at=datetime.utcnow().isoformat(),
            last_hash=result.content_hash,
            fetch_status="success",
        )

        # Update extraction records with the real source_id and store them
        for rec in records:
            rec.source_id = source.id
            self._extractions.create(rec)

        if attach_to_conference_id:
            # Update existing conference with extracted data
            update_fields: dict = {}
            for field in (
                "name", "acronym", "series", "city", "country", "venue",
                "start_date", "end_date", "cfp_url", "website_url",
            ):
                val = self._best_value(records, field)
                if val:
                    update_fields[field] = val
            # Handle topics separately
            topics_val = self._best_value(records, "topics")
            if topics_val:
                try:
                    update_fields["topics"] = json.loads(topics_val)
                except (json.JSONDecodeError, TypeError):
                    pass
            # Handle boolean fields
            if self._best_value(records, "is_online") == "true":
                update_fields["is_online"] = True
            if self._best_value(records, "is_hybrid") == "true":
                update_fields["is_hybrid"] = True
            # Update AI summary and committees if extracted
            if ai_summary:
                update_fields["ai_summary"] = ai_summary
            if ai_organizing_committee:
                update_fields["organizing_committee"] = ai_organizing_committee
            if ai_scientific_committee:
                update_fields["scientific_committee"] = ai_scientific_committee
            if update_fields:
                self._conferences.update(
                    conference_id, ConferenceUpdate(**update_fields)
                )

        # 8. Upsert important dates from extraction records (prevents duplicates)
        for rec in records:
            if rec.field_name.startswith("important_date:"):
                date_type_str = rec.field_name.split(":", 1)[1]
                try:
                    date_type = ImportantDateType(date_type_str)
                except ValueError:
                    date_type = ImportantDateType.OTHER
                self._dates.upsert(
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

    @staticmethod
    def _has_core_fields(records: list[ExtractionRecord]) -> bool:
        """Return True if all four core fields are present in the extraction records.

        Core fields required to skip deep link crawling:
        - Conference start date
        - Conference end date
        - Location (city, country, or online flag)
        - Submission deadline important date
        """
        def _has(field: str) -> bool:
            return any(r.field_name == field and r.extracted_value for r in records)

        has_start = _has("start_date")
        has_end = _has("end_date")
        has_location = _has("city") or _has("country") or any(
            r.field_name == "is_online" and r.extracted_value == "true" for r in records
        )
        has_submission = any(
            r.field_name == "important_date:submission_deadline" for r in records
        )
        return has_start and has_end and has_location and has_submission

    @staticmethod
    def _merge_records(
        ai_records: list[ExtractionRecord],
        heuristic_records: list[ExtractionRecord],
    ) -> list[ExtractionRecord]:
        """Merge AI and heuristic records, preferring AI for same fields.

        AI records always come first. For each heuristic record,
        include it only if AI didn't already extract that field.
        """
        if not ai_records:
            return heuristic_records

        ai_fields: set[str] = set()
        for rec in ai_records:
            ai_fields.add(rec.field_name)

        merged = list(ai_records)
        for rec in heuristic_records:
            if rec.field_name not in ai_fields:
                merged.append(rec)

        return merged
