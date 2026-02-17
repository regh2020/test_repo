from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DiscoveryQuery(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    date_range_start: str | None = None
    date_range_end: str | None = None
    include_twitter: bool = False


class DiscoveryCandidate(BaseModel):
    url: str
    title: str | None = None
    snippet: str | None = None
    score: float = 0.0
    source_type: str = "web"


class DiscoveryRun(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    finished_at: str | None = None
    candidates: list[DiscoveryCandidate] = Field(default_factory=list)
