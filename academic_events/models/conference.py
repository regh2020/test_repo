from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class ConferenceStatus(str, enum.Enum):
    ACTIVE = "active"
    PAST = "past"
    CANCELLED = "cancelled"
    POSTPONED = "postponed"


class ImportantDateType(str, enum.Enum):
    SUBMISSION_DEADLINE = "submission_deadline"
    ABSTRACT_SUBMISSION_DEADLINE = "abstract_submission_deadline"
    NOTIFICATION_DATE = "notification_date"
    CAMERA_READY_DEADLINE = "camera_ready_deadline"
    CONFERENCE_START_DATE = "conference_start_date"
    CONFERENCE_END_DATE = "conference_end_date"
    WORKSHOP_DEADLINE = "workshop_deadline"
    REGISTRATION_DEADLINE = "registration_deadline"
    OTHER = "other"


# Types that may appear at most once per conference
UNIQUE_DATE_TYPES: frozenset[ImportantDateType] = frozenset(
    t for t in ImportantDateType if t != ImportantDateType.OTHER
)


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


class Person(BaseModel):
    fullName: str
    affiliation: str | None = None
    role: str | None = None
    personalUrl: str | None = None


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
    status: ConferenceStatus = ConferenceStatus.ACTIVE
    ai_summary: str | None = None
    organizing_committee: list[Person] = Field(default_factory=list)
    scientific_committee: list[Person] = Field(default_factory=list)


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
    ai_summary: str | None = None
    organizing_committee: list[Person] | None = None
    scientific_committee: list[Person] | None = None


class ImportantDateCreate(BaseModel):
    type: ImportantDateType
    date_time: str
    timezone: str | None = None
    note: str | None = None
    display_globally: bool = False


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
    status: ConferenceStatus = ConferenceStatus.ACTIVE
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    # Computed from important_dates; populated by repository on list queries
    submission_deadline: str | None = None
    # AI-generated summary
    ai_summary: str | None = None
    # Committee members
    organizing_committee: list[Person] = Field(default_factory=list)
    scientific_committee: list[Person] = Field(default_factory=list)


class ImportantDate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conference_id: str
    type: ImportantDateType
    date_time: str
    timezone: str | None = None
    note: str | None = None
    display_globally: bool = False


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
