"""Global important dates endpoint."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends

from academic_events.api.dependencies import get_conference_service, get_conference_repo
from academic_events.models.conference import ImportantDate, Conference
from academic_events.services.conference_service import ConferenceService
from pydantic import BaseModel

router = APIRouter(prefix="/important-dates", tags=["important-dates"])


class GlobalImportantDate(BaseModel):
    date: ImportantDate
    conference: Conference


@router.get("", response_model=list[GlobalImportantDate])
def list_global_important_dates(
    svc: ConferenceService = Depends(get_conference_service),
):
    """Return all globally displayed important dates with their conference info."""
    dates = svc.list_global_dates()

    # Build conference lookup by fetching all referenced conferences
    conf_ids = {d.conference_id for d in dates}
    conferences: dict[str, Conference] = {}
    for cid in conf_ids:
        conf = svc.get_conference(cid)
        if conf:
            conferences[cid] = conf

    result = []
    for d in dates:
        conf = conferences.get(d.conference_id)
        if conf:
            result.append(GlobalImportantDate(date=d, conference=conf))
    return result
