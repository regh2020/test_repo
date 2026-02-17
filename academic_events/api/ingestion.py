"""Ingestion endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from academic_events.api.dependencies import get_ingestion_pipeline
from academic_events.services.ingestion.pipeline import IngestionPipeline

router = APIRouter(tags=["ingestion"])


class IngestRequest(BaseModel):
    url: str
    attach_to_conference_id: str | None = None


class IngestResponse(BaseModel):
    conference_id: str | None
    source_id: str
    extraction_count: int
    error: str | None = None


@router.post("/ingest/url", response_model=IngestResponse)
async def ingest_url(
    body: IngestRequest,
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
):
    result = await pipeline.ingest_url(
        url=body.url,
        attach_to_conference_id=body.attach_to_conference_id,
    )
    return IngestResponse(
        conference_id=result.conference_id,
        source_id=result.source.id,
        extraction_count=len(result.records),
        error=result.error,
    )
