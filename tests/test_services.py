"""Tests for service layer."""

from academic_events.models.conference import (
    ConferenceCreate,
    ConferenceUpdate,
    ImportantDateCreate,
    ImportantDateType,
    SourceCreate,
    SourceType,
)
from academic_events.services.conference_service import ConferenceService
from academic_events.services.ingestion.cleaner import clean_html, get_meta_and_structured
from academic_events.services.ingestion.extractor import extract_fields


def test_conference_service_crud(conference_repo, date_repo, source_repo):
    svc = ConferenceService(conference_repo, date_repo, source_repo)

    conf = svc.create_conference(ConferenceCreate(name="Test Conf"))
    assert conf.name == "Test Conf"

    fetched = svc.get_conference(conf.id)
    assert fetched is not None

    updated = svc.update_conference(conf.id, ConferenceUpdate(city="Berlin"))
    assert updated is not None
    assert updated.city == "Berlin"

    confs = svc.list_conferences()
    assert len(confs) == 1

    assert svc.delete_conference(conf.id) is True
    assert svc.get_conference(conf.id) is None


def test_conference_service_dates(conference_repo, date_repo, source_repo):
    svc = ConferenceService(conference_repo, date_repo, source_repo)
    conf = svc.create_conference(ConferenceCreate(name="Test"))

    dt = svc.add_date(
        conf.id,
        ImportantDateCreate(type=ImportantDateType.SUBMISSION_DEADLINE, date_time="2026-06-15"),
    )
    assert dt is not None

    dates = svc.list_dates(conf.id)
    assert len(dates) == 1

    # Adding date to nonexistent conference returns None
    assert svc.add_date("nonexistent", ImportantDateCreate(type=ImportantDateType.OTHER, date_time="2026-01-01")) is None


def test_conference_service_sources(conference_repo, date_repo, source_repo):
    svc = ConferenceService(conference_repo, date_repo, source_repo)
    conf = svc.create_conference(ConferenceCreate(name="Test"))

    src = svc.add_source(conf.id, SourceCreate(type=SourceType.WEBSITE, url="https://example.com"))
    assert src is not None

    sources = svc.list_sources(conf.id)
    assert len(sources) == 1


def test_clean_html():
    html = """
    <html>
    <head><title>Test Conference</title></head>
    <body>
    <nav>Navigation</nav>
    <main>
    <h1>Test Conference 2026</h1>
    <p>Submission deadline: January 15, 2026</p>
    </main>
    <footer>Footer</footer>
    </body>
    </html>
    """
    text = clean_html(html)
    assert "Test Conference 2026" in text
    assert "Submission deadline" in text
    assert "Navigation" not in text
    assert "Footer" not in text


def test_get_meta_and_structured():
    html = """
    <html>
    <head>
        <title>ICML 2026</title>
        <meta property="og:title" content="ICML - Int'l Conference on ML">
    </head>
    <body>Content</body>
    </html>
    """
    meta = get_meta_and_structured(html)
    assert meta["title"] == "ICML 2026"
    assert meta["og:title"] == "ICML - Int'l Conference on ML"


def test_get_meta_jsonld():
    html = """
    <html>
    <head><title>Conf</title></head>
    <body>
    <script type="application/ld+json">
    {"@type": "Event", "name": "ICML 2026", "startDate": "2026-07-20", "endDate": "2026-07-25"}
    </script>
    </body>
    </html>
    """
    meta = get_meta_and_structured(html)
    assert "jsonld" in meta
    assert meta["jsonld"]["name"] == "ICML 2026"


def test_extract_fields_from_text():
    text = "Submission deadline: January 15, 2026\nNotification: March 1, 2026"
    meta = {"title": "ICML 2026"}
    records = extract_fields(text, meta, source_id="src1")

    field_names = [r.field_name for r in records]
    assert "name" in field_names
    assert any("submission_deadline" in fn for fn in field_names)
    assert any("notification" in fn for fn in field_names)


def test_extract_fields_from_jsonld():
    text = "Some page text"
    meta = {
        "jsonld": {
            "@type": "Event",
            "name": "NeurIPS 2026",
            "startDate": "2026-12-01",
            "endDate": "2026-12-08",
            "location": {
                "name": "Convention Center",
                "address": {"addressLocality": "Vancouver", "addressCountry": "Canada"},
            },
        }
    }
    records = extract_fields(text, meta, source_id="src1")

    values = {r.field_name: r.extracted_value for r in records}
    assert values.get("name") == "NeurIPS 2026"
    assert values.get("start_date") == "2026-12-01"
    assert values.get("city") == "Vancouver"
    assert values.get("country") == "Canada"
    assert values.get("venue") == "Convention Center"

    # Structured data should have high confidence
    name_rec = [r for r in records if r.field_name == "name" and r.extraction_method.value == "structured"][0]
    assert name_rec.confidence >= 0.9


def test_get_meta_jsonld_from_list():
    """JSON-LD Event inside a list should be extracted and not overwritten by later script tags."""
    html = """
    <html>
    <head><title>Conf</title></head>
    <body>
    <script type="application/ld+json">
    [{"@type": "Event", "name": "First Conf", "startDate": "2026-05-01"}]
    </script>
    <script type="application/ld+json">
    {"@type": "Organization", "name": "Some Org"}
    </script>
    </body>
    </html>
    """
    meta = get_meta_and_structured(html)
    assert "jsonld" in meta
    assert meta["jsonld"]["name"] == "First Conf"
    assert meta["jsonld"]["@type"] == "Event"


def test_extract_fields_og_title_fallback():
    """When <title> is absent, og:title should be used for conference name."""
    text = "Some conference page text"
    meta = {"og:title": "AAAI 2026 Conference"}
    records = extract_fields(text, meta, source_id="src1")

    name_recs = [r for r in records if r.field_name == "name"]
    assert len(name_recs) == 1
    assert name_recs[0].extracted_value == "AAAI 2026 Conference"
    assert name_recs[0].confidence == 0.65


def test_extract_fields_og_description_dates():
    """Dates in og:description should be extracted via heuristic parsing."""
    text = "Welcome to the conference"
    meta = {
        "title": "My Conf",
        "og:description": "Submission deadline: February 20, 2026",
    }
    records = extract_fields(text, meta, source_id="src1")

    date_recs = [r for r in records if r.field_name.startswith("important_date:")]
    assert any(r.field_name == "important_date:submission_deadline" for r in date_recs)


async def test_pipeline_extraction_records_have_correct_source_id(
    conference_repo, source_repo, date_repo, extraction_repo
):
    """Extraction records should reference the persisted source, not a temp ID."""
    from unittest.mock import AsyncMock, patch

    from academic_events.services.ingestion.fetcher import FetchResult
    from academic_events.services.ingestion.pipeline import IngestionPipeline

    pipeline = IngestionPipeline(
        conferences=conference_repo,
        sources=source_repo,
        dates=date_repo,
        extractions=extraction_repo,
    )

    fake_html = """
    <html>
    <head><title>Test Conf 2026</title></head>
    <body>
    <p>Submission deadline: March 10, 2026</p>
    </body>
    </html>
    """
    fake_result = FetchResult(
        url="https://example.com/conf",
        html=fake_html,
        content_hash="abc123",
        status_code=200,
    )

    with patch(
        "academic_events.services.ingestion.pipeline.fetch_url",
        new_callable=AsyncMock,
        return_value=fake_result,
    ):
        result = await pipeline.ingest_url("https://example.com/conf")

    assert result.error is None
    assert result.conference_id is not None

    # The source should exist in the DB
    persisted_source = source_repo.get(result.source.id)
    assert persisted_source is not None

    # All extraction records should reference the persisted source
    stored_records = extraction_repo.list_for_source(result.source.id)
    assert len(stored_records) > 0
    for rec in stored_records:
        assert rec.source_id == result.source.id
