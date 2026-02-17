"""Tests for Pydantic data models."""

from academic_events.models.conference import (
    Conference,
    ConferenceCreate,
    ConferenceStatus,
    ExtractionMethod,
    ExtractionRecord,
    ImportantDate,
    ImportantDateType,
    Source,
    SourceType,
)
from academic_events.models.discovery import DiscoveryCandidate, DiscoveryQuery, DiscoveryRun


def test_conference_create_defaults():
    c = ConferenceCreate(name="ICML 2026")
    assert c.name == "ICML 2026"
    assert c.topics == []
    assert c.status == ConferenceStatus.UNKNOWN
    assert c.is_online is False


def test_conference_has_uuid():
    c = Conference(name="NeurIPS")
    assert len(c.id) == 36  # UUID format
    assert c.created_at is not None


def test_important_date_types():
    assert ImportantDateType.SUBMISSION_DEADLINE.value == "submission_deadline"
    assert ImportantDateType.CAMERA_READY.value == "camera_ready"


def test_source_types():
    assert SourceType.WEBSITE.value == "website"
    assert SourceType.TWITTER.value == "twitter"


def test_extraction_record_confidence_bounds():
    r = ExtractionRecord(
        source_id="s1",
        field_name="name",
        extracted_value="ICML",
        confidence=0.85,
    )
    assert 0.0 <= r.confidence <= 1.0


def test_discovery_query_defaults():
    q = DiscoveryQuery(keywords=["machine learning"])
    assert q.include_twitter is False
    assert q.topics == []


def test_discovery_run_has_id():
    run = DiscoveryRun(query="AI conference")
    assert run.id is not None
    assert run.candidates == []
