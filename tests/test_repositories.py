"""Tests for SQLite repository implementations."""

from academic_events.models.conference import (
    ConferenceCreate,
    ConferenceStatus,
    ConferenceUpdate,
    ExtractionMethod,
    ExtractionRecord,
    ImportantDateCreate,
    ImportantDateType,
    SourceCreate,
    SourceType,
)
from academic_events.models.discovery import DiscoveryCandidate, DiscoveryRun


def test_create_and_get_conference(conference_repo):
    data = ConferenceCreate(
        name="ICML 2026",
        acronym="ICML",
        topics=["machine learning"],
        city="Vienna",
        country="Austria",
        status=ConferenceStatus.UPCOMING,
    )
    conf = conference_repo.create(data)
    assert conf.id is not None
    assert conf.name == "ICML 2026"

    fetched = conference_repo.get(conf.id)
    assert fetched is not None
    assert fetched.name == "ICML 2026"
    assert fetched.topics == ["machine learning"]


def test_list_conferences_with_filters(conference_repo):
    conference_repo.create(ConferenceCreate(name="ICML 2026", city="Vienna", country="Austria", status=ConferenceStatus.UPCOMING))
    conference_repo.create(ConferenceCreate(name="NeurIPS 2026", city="Vancouver", country="Canada", status=ConferenceStatus.UPCOMING))
    conference_repo.create(ConferenceCreate(name="CVPR 2025", city="Nashville", country="USA", status=ConferenceStatus.PAST))

    all_confs = conference_repo.list_all()
    assert len(all_confs) == 3

    vienna = conference_repo.list_all(city="Vienna")
    assert len(vienna) == 1

    upcoming = conference_repo.list_all(status="upcoming")
    assert len(upcoming) == 2


def test_update_conference(conference_repo):
    conf = conference_repo.create(ConferenceCreate(name="Test Conf"))
    updated = conference_repo.update(conf.id, ConferenceUpdate(name="Updated Conf", city="Berlin"))
    assert updated is not None
    assert updated.name == "Updated Conf"
    assert updated.city == "Berlin"


def test_delete_conference(conference_repo):
    conf = conference_repo.create(ConferenceCreate(name="To Delete"))
    assert conference_repo.delete(conf.id) is True
    assert conference_repo.get(conf.id) is None
    assert conference_repo.delete("nonexistent") is False


def test_important_dates(conference_repo, date_repo):
    conf = conference_repo.create(ConferenceCreate(name="Test"))
    dt = date_repo.create(
        conf.id,
        ImportantDateCreate(
            type=ImportantDateType.SUBMISSION_DEADLINE,
            date_time="2026-06-15",
            note="Abstract deadline",
        ),
    )
    assert dt.conference_id == conf.id
    dates = date_repo.list_for_conference(conf.id)
    assert len(dates) == 1
    assert dates[0].type == ImportantDateType.SUBMISSION_DEADLINE

    assert date_repo.delete(dt.id) is True
    assert date_repo.list_for_conference(conf.id) == []


def test_sources(conference_repo, source_repo):
    conf = conference_repo.create(ConferenceCreate(name="Test"))
    src = source_repo.create(
        conf.id,
        SourceCreate(type=SourceType.WEBSITE, url="https://example.com/conf"),
    )
    assert src.conference_id == conf.id
    assert src.refresh_enabled is True

    sources = source_repo.list_for_conference(conf.id)
    assert len(sources) == 1

    source_repo.update_fetch_status(
        src.id,
        last_fetched_at="2026-01-01T00:00:00",
        last_hash="abc123",
        fetch_status="success",
    )
    updated = source_repo.get(src.id)
    assert updated is not None
    assert updated.last_hash == "abc123"


def test_sources_due_for_refresh(conference_repo, source_repo):
    conf = conference_repo.create(ConferenceCreate(name="Test"))
    source_repo.create(
        conf.id,
        SourceCreate(type=SourceType.WEBSITE, url="https://example.com"),
    )
    # Never fetched -> due for refresh
    due = source_repo.list_due_for_refresh()
    assert len(due) == 1


def test_extraction_records(conference_repo, source_repo, extraction_repo):
    conf = conference_repo.create(ConferenceCreate(name="Test"))
    src = source_repo.create(
        conf.id,
        SourceCreate(type=SourceType.WEBSITE, url="https://example.com"),
    )
    rec = ExtractionRecord(
        source_id=src.id,
        field_name="name",
        extracted_value="Test Conference",
        confidence=0.9,
        extraction_method=ExtractionMethod.HEURISTIC,
    )
    created = extraction_repo.create(rec)
    assert created.id == rec.id

    records = extraction_repo.list_for_source(src.id)
    assert len(records) == 1

    field_records = extraction_repo.list_for_field(src.id, "name")
    assert len(field_records) == 1
    assert field_records[0].extracted_value == "Test Conference"


def test_discovery_run(discovery_repo):
    run = DiscoveryRun(
        query="AI conference 2026",
        candidates=[
            DiscoveryCandidate(url="https://example.com/conf1", title="Conf 1", score=0.8),
        ],
    )
    created = discovery_repo.create(run)
    assert created.id == run.id

    fetched = discovery_repo.get(run.id)
    assert fetched is not None
    assert len(fetched.candidates) == 1
    assert fetched.candidates[0].url == "https://example.com/conf1"

    all_runs = discovery_repo.list_all()
    assert len(all_runs) == 1
