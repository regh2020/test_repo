from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ConferenceStatus(str, enum.Enum):
    UPCOMING = "upcoming"
    PAST = "past"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


class ImportantDateType(str, enum.Enum):
    SUBMISSION_DEADLINE = "submission_deadline"
    NOTIFICATION = "notification"
    CAMERA_READY = "camera_ready"
    WORKSHOP_DEADLINE = "workshop_deadline"
    EARLY_REGISTRATION = "early_registration"
    CONFERENCE_START = "conference_start"
    CONFERENCE_END = "conference_end"
    OTHER = "other"


class SourceType(str, enum.Enum):
    WEBSITE = "website"
    CFP = "cfp"
    TWITTER = "twitter"
    RSS = "rss"


class ExtractionMethod(str, enum.Enum):
    HEURISTIC = "heuristic"
    STRUCTURED = "structured"
    MANUAL = "manual"


# --- Creation / Update schemas ---


class ConferenceCreate(BaseModel):
    name: str
    acronym: str | None = None
    series: str | None = None
    topics: list[str] = Field(default_factory=list)
    city: str | None = None
    country: str | None = None
    venue: str | None = None
    is_online: bool = False
    is_hybrid: bool = False
    start_date: str | None = None
    end_date: str | None = None
    cfp_url: str | None = None
    website_url: str | None = None
    status: ConferenceStatus = ConferenceStatus.UNKNOWN


class ConferenceUpdate(BaseModel):
    name: str | None = None
    acronym: str | None = None
    series: str | None = None
    topics: list[str] | None = None
    city: str | None = None
    country: str | None = None
    venue: str | None = None
    is_online: bool | None = None
    is_hybrid: bool | None = None
    start_date: str | None = None
    end_date: str | None = None
    cfp_url: str | None = None
    website_url: str | None = None
    status: ConferenceStatus | None = None


class ImportantDateCreate(BaseModel):
    type: ImportantDateType
    date_time: str
    timezone: str | None = None
    note: str | None = None


class SourceCreate(BaseModel):
    type: SourceType
    url: str
    refresh_interval_hours: int | None = None
    refresh_enabled: bool = True


# --- Full models (read) ---


class Conference(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    acronym: str | None = None
    series: str | None = None
    topics: list[str] = Field(default_factory=list)
    city: str | None = None
    country: str | None = None
    venue: str | None = None
    is_online: bool = False
    is_hybrid: bool = False
    start_date: str | None = None
    end_date: str | None = None
    cfp_url: str | None = None
    website_url: str | None = None
    status: ConferenceStatus = ConferenceStatus.UNKNOWN
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ImportantDate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conference_id: str
    type: ImportantDateType
    date_time: str
    timezone: str | None = None
    note: str | None = None


class Source(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conference_id: str | None = None
    type: SourceType
    url: str
    last_fetched_at: str | None = None
    last_hash: str | None = None
    fetch_status: str | None = None
    refresh_interval_hours: int = 24
    refresh_enabled: bool = True


class ExtractionRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str
    extracted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    field_name: str
    extracted_value: str
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: ExtractionMethod = ExtractionMethod.HEURISTIC
    raw_snippet: str | None = None
