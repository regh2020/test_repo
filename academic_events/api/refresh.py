"""Refresh endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from academic_events.api.dependencies import get_refresh_worker
from academic_events.services.refresh.worker import RefreshWorker

router = APIRouter(tags=["refresh"])


class RefreshRequest(BaseModel):
    conference_id: str | None = None
    force: bool = False


class RefreshSourceResult(BaseModel):
    source_id: str
    changed: bool
    new_record_count: int
    error: str | None = None


class RefreshResponse(BaseModel):
    results: list[RefreshSourceResult]


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(
    body: RefreshRequest,
    worker: RefreshWorker = Depends(get_refresh_worker),
):
    if body.conference_id:
        results = await worker.refresh_conference(body.conference_id)
    else:
        results = await worker.refresh_all_due()

    return RefreshResponse(
        results=[
            RefreshSourceResult(
                source_id=r.source_id,
                changed=r.changed,
                new_record_count=len(r.new_records),
                error=r.error,
            )
            for r in results
        ]
    )


@router.post("/sources/{source_id}/refresh", response_model=RefreshSourceResult)
async def refresh_source(
    source_id: str,
    worker: RefreshWorker = Depends(get_refresh_worker),
):
    r = await worker.refresh_source(source_id)
    return RefreshSourceResult(
        source_id=r.source_id,
        changed=r.changed,
        new_record_count=len(r.new_records),
        error=r.error,
    )
