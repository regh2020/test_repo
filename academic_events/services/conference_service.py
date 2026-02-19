"""Core conference service - orchestrates CRUD, sources, and dates."""

from __future__ import annotations

import logging

from academic_events.models.conference import (
    Conference,
    ConferenceCreate,
    ConferenceUpdate,
    ImportantDate,
    ImportantDateCreate,
    Source,
    SourceCreate,
)
from academic_events.repositories.interfaces import (
    ConferenceRepository,
    ImportantDateRepository,
    SourceRepository,
)

logger = logging.getLogger(__name__)


class ConferenceService:
    def __init__(
        self,
        conferences: ConferenceRepository,
        dates: ImportantDateRepository,
        sources: SourceRepository,
    ):
        self._conferences = conferences
        self._dates = dates
        self._sources = sources

    def create_conference(self, data: ConferenceCreate) -> Conference:
        conf = self._conferences.create(data)
        logger.info("Created conference %s (%s)", conf.id, conf.name)
        return conf

    def get_conference(self, conference_id: str) -> Conference | None:
        return self._conferences.get(conference_id)

    def list_conferences(self, **filters) -> list[Conference]:
        return self._conferences.list_all(**filters)

    def update_conference(
        self, conference_id: str, data: ConferenceUpdate
    ) -> Conference | None:
        conf = self._conferences.update(conference_id, data)
        if conf:
            logger.info("Updated conference %s", conference_id)
        return conf

    def delete_conference(self, conference_id: str) -> bool:
        ok = self._conferences.delete(conference_id)
        if ok:
            logger.info("Deleted conference %s", conference_id)
        return ok

    # --- Important dates ---

    def add_date(
        self, conference_id: str, data: ImportantDateCreate
    ) -> ImportantDate | None:
        if self._conferences.get(conference_id) is None:
            return None
        return self._dates.create(conference_id, data)

    def list_dates(self, conference_id: str) -> list[ImportantDate]:
        return self._dates.list_for_conference(conference_id)

    def delete_date(self, date_id: str) -> bool:
        return self._dates.delete(date_id)

    def update_date_display_globally(self, date_id: str, display_globally: bool) -> ImportantDate | None:
        return self._dates.update_display_globally(date_id, display_globally)

    def list_global_dates(self) -> list[ImportantDate]:
        return self._dates.list_global()

    # --- Sources ---

    def add_source(self, conference_id: str, data: SourceCreate) -> Source | None:
        if self._conferences.get(conference_id) is None:
            return None
        return self._sources.create(conference_id, data)

    def list_sources(self, conference_id: str) -> list[Source]:
        return self._sources.list_for_conference(conference_id)
