"""Abstract repository interfaces.

These define the storage contract so the underlying engine (SQLite, Postgres, etc.)
can be swapped without touching business logic.
"""

from __future__ import annotations

import abc

from academic_events.models.conference import (
    Conference,
    ConferenceCreate,
    ConferenceUpdate,
    ExtractionRecord,
    ImportantDate,
    ImportantDateCreate,
    Source,
    SourceCreate,
)
from academic_events.models.discovery import DiscoveryRun


class ConferenceRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, data: ConferenceCreate) -> Conference: ...

    @abc.abstractmethod
    def get(self, conference_id: str) -> Conference | None: ...

    @abc.abstractmethod
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
    ) -> list[Conference]: ...

    @abc.abstractmethod
    def update(self, conference_id: str, data: ConferenceUpdate) -> Conference | None: ...

    @abc.abstractmethod
    def delete(self, conference_id: str) -> bool: ...


class ImportantDateRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, conference_id: str, data: ImportantDateCreate) -> ImportantDate: ...

    @abc.abstractmethod
    def get(self, date_id: str) -> ImportantDate | None: ...

    @abc.abstractmethod
    def list_for_conference(self, conference_id: str) -> list[ImportantDate]: ...

    @abc.abstractmethod
    def update_display_globally(self, date_id: str, display_globally: bool) -> ImportantDate | None: ...

    @abc.abstractmethod
    def list_global(self) -> list[ImportantDate]: ...

    @abc.abstractmethod
    def delete(self, date_id: str) -> bool: ...


class SourceRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, conference_id: str, data: SourceCreate) -> Source: ...

    @abc.abstractmethod
    def get(self, source_id: str) -> Source | None: ...

    @abc.abstractmethod
    def list_for_conference(self, conference_id: str) -> list[Source]: ...

    @abc.abstractmethod
    def update_fetch_status(
        self,
        source_id: str,
        *,
        last_fetched_at: str,
        last_hash: str | None = None,
        fetch_status: str = "success",
    ) -> None: ...

    @abc.abstractmethod
    def list_due_for_refresh(self) -> list[Source]: ...


class ExtractionRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, record: ExtractionRecord) -> ExtractionRecord: ...

    @abc.abstractmethod
    def list_for_source(self, source_id: str) -> list[ExtractionRecord]: ...

    @abc.abstractmethod
    def list_for_field(
        self, source_id: str, field_name: str
    ) -> list[ExtractionRecord]: ...


class DiscoveryRepository(abc.ABC):
    @abc.abstractmethod
    def create(self, run: DiscoveryRun) -> DiscoveryRun: ...

    @abc.abstractmethod
    def get(self, run_id: str) -> DiscoveryRun | None: ...

    @abc.abstractmethod
    def list_all(self, limit: int = 50) -> list[DiscoveryRun]: ...
