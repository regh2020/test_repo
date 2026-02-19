"""Discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from academic_events.api.dependencies import get_discovery_service, get_pending_discovery_repo
from academic_events.models.discovery import DiscoveryQuery, DiscoveryRun, PendingDiscovery
from academic_events.repositories.sqlite.pending_discovery_repo import SQLitePendingDiscoveryRepository
from academic_events.services.discovery.discovery_service import DiscoveryService

router = APIRouter(tags=["discovery"])


@router.post("/discover", response_model=DiscoveryRun)
async def discover(
    query: DiscoveryQuery,
    svc: DiscoveryService = Depends(get_discovery_service),
):
    return await svc.discover(query)


class SaveToPendingRequest(BaseModel):
    url: str
    title: str | None = None
    snippet: str | None = None
    score: float = 0.0
    source_type: str = "web"


@router.post("/import", response_model=PendingDiscovery, status_code=201)
def save_candidate_to_pending(
    body: SaveToPendingRequest,
    repo: SQLitePendingDiscoveryRepository = Depends(get_pending_discovery_repo),
):
    """Save a discovered candidate to Pending Discoveries.

    AI extraction and conference creation are NOT triggered here.
    Use POST /pending-discoveries/{id}/import to perform the actual import.
    """
    return repo.create(
        url=body.url,
        title=body.title,
        snippet=body.snippet,
        score=body.score,
        source_type=body.source_type,
    )
