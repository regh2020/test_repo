"""Pending discoveries endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from academic_events.api.dependencies import (
    get_ingestion_pipeline,
    get_pending_discovery_repo,
)
from academic_events.models.discovery import PendingDiscovery
from academic_events.repositories.sqlite.pending_discovery_repo import (
    SQLitePendingDiscoveryRepository,
)
from academic_events.services.ingestion.pipeline import IngestionPipeline
from pydantic import BaseModel

router = APIRouter(prefix="/pending-discoveries", tags=["pending-discoveries"])


class AddPendingRequest(BaseModel):
    url: str
    title: str | None = None
    snippet: str | None = None
    score: float = 0.0
    source_type: str = "web"


class ImportPendingResponse(BaseModel):
    conference_id: str | None
    source_id: str
    extraction_count: int
    error: str | None = None


@router.post("", response_model=PendingDiscovery, status_code=201)
def add_pending_discovery(
    body: AddPendingRequest,
    repo: SQLitePendingDiscoveryRepository = Depends(get_pending_discovery_repo),
):
    return repo.create(
        url=body.url,
        title=body.title,
        snippet=body.snippet,
        score=body.score,
        source_type=body.source_type,
    )


@router.get("", response_model=list[PendingDiscovery])
def list_pending_discoveries(
    repo: SQLitePendingDiscoveryRepository = Depends(get_pending_discovery_repo),
):
    return repo.list_all()


@router.delete("/{pending_id}", status_code=204)
def delete_pending_discovery(
    pending_id: str,
    repo: SQLitePendingDiscoveryRepository = Depends(get_pending_discovery_repo),
):
    if not repo.delete(pending_id):
        raise HTTPException(status_code=404, detail="Pending discovery not found")


@router.post("/{pending_id}/import", response_model=ImportPendingResponse)
async def import_pending_discovery(
    pending_id: str,
    repo: SQLitePendingDiscoveryRepository = Depends(get_pending_discovery_repo),
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
):
    """Import a pending discovery: run full extraction pipeline (including AI) and create conference."""
    pending = repo.get(pending_id)
    if pending is None:
        raise HTTPException(status_code=404, detail="Pending discovery not found")

    repo.update_status(pending_id, "importing")
    result = await pipeline.ingest_url(url=pending.url)

    if result.error:
        repo.update_status(pending_id, "failed")
    else:
        repo.update_status(pending_id, "imported")

    return ImportPendingResponse(
        conference_id=result.conference_id,
        source_id=result.source.id,
        extraction_count=len(result.records),
        error=result.error,
    )
