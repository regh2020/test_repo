"""Conference CRUD endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from academic_events.api.dependencies import get_conference_service
from academic_events.models.conference import (
    Conference,
    ConferenceCreate,
    ConferenceUpdate,
    ImportantDate,
    ImportantDateCreate,
    Source,
    SourceCreate,
)
from academic_events.services.conference_service import ConferenceService

router = APIRouter(prefix="/conferences", tags=["conferences"])


@router.post("", response_model=Conference, status_code=201)
def create_conference(
    data: ConferenceCreate,
    svc: ConferenceService = Depends(get_conference_service),
):
    return svc.create_conference(data)


@router.get("", response_model=list[Conference])
def list_conferences(
    name: str | None = None,
    acronym: str | None = None,
    topic: str | None = None,
    city: str | None = None,
    country: str | None = None,
    status: str | None = None,
    start_after: str | None = None,
    start_before: str | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    svc: ConferenceService = Depends(get_conference_service),
):
    return svc.list_conferences(
        name=name,
        acronym=acronym,
        topic=topic,
        city=city,
        country=country,
        status=status,
        start_after=start_after,
        start_before=start_before,
        limit=limit,
        offset=offset,
    )


@router.get("/{conference_id}", response_model=Conference)
def get_conference(
    conference_id: str,
    svc: ConferenceService = Depends(get_conference_service),
):
    conf = svc.get_conference(conference_id)
    if conf is None:
        raise HTTPException(status_code=404, detail="Conference not found")
    return conf


@router.patch("/{conference_id}", response_model=Conference)
def update_conference(
    conference_id: str,
    data: ConferenceUpdate,
    svc: ConferenceService = Depends(get_conference_service),
):
    conf = svc.update_conference(conference_id, data)
    if conf is None:
        raise HTTPException(status_code=404, detail="Conference not found")
    return conf


@router.delete("/{conference_id}", status_code=204)
def delete_conference(
    conference_id: str,
    svc: ConferenceService = Depends(get_conference_service),
):
    if not svc.delete_conference(conference_id):
        raise HTTPException(status_code=404, detail="Conference not found")


# --- Important dates ---


@router.post(
    "/{conference_id}/dates",
    response_model=ImportantDate,
    status_code=201,
)
def add_important_date(
    conference_id: str,
    data: ImportantDateCreate,
    svc: ConferenceService = Depends(get_conference_service),
):
    dt = svc.add_date(conference_id, data)
    if dt is None:
        raise HTTPException(status_code=404, detail="Conference not found")
    return dt


@router.get("/{conference_id}/dates", response_model=list[ImportantDate])
def list_important_dates(
    conference_id: str,
    svc: ConferenceService = Depends(get_conference_service),
):
    return svc.list_dates(conference_id)


@router.delete("/dates/{date_id}", status_code=204)
def delete_important_date(
    date_id: str,
    svc: ConferenceService = Depends(get_conference_service),
):
    if not svc.delete_date(date_id):
        raise HTTPException(status_code=404, detail="Date not found")


# --- Sources ---


@router.post(
    "/{conference_id}/sources",
    response_model=Source,
    status_code=201,
)
def add_source(
    conference_id: str,
    data: SourceCreate,
    svc: ConferenceService = Depends(get_conference_service),
):
    src = svc.add_source(conference_id, data)
    if src is None:
        raise HTTPException(status_code=404, detail="Conference not found")
    return src


@router.get("/{conference_id}/sources", response_model=list[Source])
def list_sources(
    conference_id: str,
    svc: ConferenceService = Depends(get_conference_service),
):
    return svc.list_sources(conference_id)
