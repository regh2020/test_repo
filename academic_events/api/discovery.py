"""Discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from academic_events.api.dependencies import get_discovery_service, get_ingestion_pipeline
from academic_events.models.discovery import DiscoveryCandidate, DiscoveryQuery, DiscoveryRun
from academic_events.services.discovery.discovery_service import DiscoveryService
from academic_events.services.ingestion.pipeline import IngestionPipeline

router = APIRouter(tags=["discovery"])


@router.post("/discover", response_model=DiscoveryRun)
async def discover(
    query: DiscoveryQuery,
    svc: DiscoveryService = Depends(get_discovery_service),
):
    return await svc.discover(query)


class ImportRequest(BaseModel):
    candidate_url: str


class ImportResponse(BaseModel):
    conference_id: str | None
    source_id: str
    extraction_count: int
    error: str | None = None


@router.post("/import", response_model=ImportResponse)
async def import_candidate(
    body: ImportRequest,
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
):
    result = await pipeline.ingest_url(url=body.candidate_url)
    return ImportResponse(
        conference_id=result.conference_id,
        source_id=result.source.id,
        extraction_count=len(result.records),
        error=result.error,
    )
