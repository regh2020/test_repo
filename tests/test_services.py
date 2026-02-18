"""Tests for service layer."""

import json
from unittest.mock import AsyncMock, patch

from academic_events.models.conference import (
    ConferenceCreate,
    ConferenceUpdate,
    ExtractionMethod,
    ExtractionRecord,
    ImportantDateCreate,
    ImportantDateType,
    SourceCreate,
    SourceType,
)
from academic_events.services.conference_service import ConferenceService
from academic_events.services.ingestion.cleaner import clean_html, get_meta_and_structured
from academic_events.services.ingestion.extractor import extract_fields
from academic_events.services.ingestion.link_follower import extract_links


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


def test_extract_links_from_html():
    """Links to relevant sub-pages should be identified and scored."""
    html = """
    <html>
    <body>
    <a href="/cfp">Call for Papers</a>
    <a href="/dates">Important Dates</a>
    <a href="/venue">Venue Information</a>
    <a href="/sponsors">Sponsors</a>
    <a href="https://other-domain.com/page">External</a>
    <a href="#section">Anchor</a>
    <a href="mailto:info@conf.com">Email</a>
    </body>
    </html>
    """
    links = extract_links(html, "https://example.com/conf2026")

    urls = [l["url"] for l in links]
    # Relevant links should be found (resolved to absolute)
    assert "https://example.com/cfp" in urls
    assert "https://example.com/dates" in urls
    assert "https://example.com/venue" in urls

    # External domain, anchors, and mailto should be excluded
    assert not any("other-domain" in u for u in urls)
    assert not any(u.startswith("#") for u in urls)
    assert not any(u.startswith("mailto:") for u in urls)

    # CFP and dates should have higher relevance than sponsors
    cfp_link = next(l for l in links if "cfp" in l["url"])
    assert cfp_link["relevance_score"] > 0


def test_extract_links_deduplication():
    """Duplicate links should be deduplicated."""
    html = """
    <html><body>
    <a href="/cfp">CFP Page</a>
    <a href="/cfp">Call for Papers</a>
    </body></html>
    """
    links = extract_links(html, "https://example.com")
    cfp_urls = [l["url"] for l in links if "cfp" in l["url"]]
    assert len(cfp_urls) == 1


async def test_ai_extract_fields_no_api_key():
    """AI extraction should gracefully return empty when no API key is set."""
    from academic_events.services.ingestion.ai_extractor import ai_extract_fields

    records, links = await ai_extract_fields(
        text="Some conference text",
        page_url="https://example.com",
        source_id="src1",
        api_key=None,
    )
    assert records == []
    assert links == []


async def test_ai_extract_fields_with_mock():
    """AI extraction should parse a proper API response into ExtractionRecords."""
    from academic_events.services.ingestion.ai_extractor import ai_extract_fields

    fake_response = json.dumps({
        "name": "ICML 2026",
        "acronym": "ICML",
        "series": "International Conference on Machine Learning",
        "topics": ["machine learning", "deep learning", "AI"],
        "city": "Vienna",
        "country": "Austria",
        "venue": "Austria Center Vienna",
        "is_online": False,
        "is_hybrid": True,
        "start_date": "2026-07-20",
        "end_date": "2026-07-26",
        "cfp_url": "https://icml.cc/cfp",
        "website_url": "https://icml.cc",
        "important_dates": [
            {"type": "submission_deadline", "date": "2026-02-01", "note": "Paper submission deadline"},
            {"type": "notification", "date": "2026-04-15", "note": "Author notification"},
        ],
        "relevant_links": [
            {"url": "/cfp", "description": "Call for papers", "relevance": "high"},
            {"url": "/venue", "description": "Venue details", "relevance": "medium"},
        ],
    })

    # Mock the Anthropic API client
    mock_message = AsyncMock()
    mock_message.content = [AsyncMock(text=fake_response)]

    mock_client_instance = AsyncMock()
    mock_client_instance.messages.create = AsyncMock(return_value=mock_message)

    with patch(
        "academic_events.services.ingestion.ai_extractor.anthropic.AsyncAnthropic",
        return_value=mock_client_instance,
    ):
        records, links = await ai_extract_fields(
            text="Some conference page about ICML 2026 in Vienna...",
            page_url="https://icml.cc",
            source_id="src1",
            api_key="fake-key",
        )

    # Verify extracted fields
    values = {r.field_name: r.extracted_value for r in records}
    assert values["name"] == "ICML 2026"
    assert values["acronym"] == "ICML"
    assert values["city"] == "Vienna"
    assert values["country"] == "Austria"
    assert values["venue"] == "Austria Center Vienna"
    assert values["start_date"] == "2026-07-20"
    assert values["end_date"] == "2026-07-26"
    assert values["cfp_url"] == "https://icml.cc/cfp"
    assert values["website_url"] == "https://icml.cc"

    # Verify is_hybrid was extracted
    assert values.get("is_hybrid") == "true"

    # Verify topics
    assert "topics" in values
    topics = json.loads(values["topics"])
    assert "machine learning" in topics

    # Verify important dates
    date_recs = [r for r in records if r.field_name.startswith("important_date:")]
    assert len(date_recs) == 2
    assert any(r.field_name == "important_date:submission_deadline" for r in date_recs)
    assert any(r.field_name == "important_date:notification" for r in date_recs)

    # Verify all AI records have high confidence
    for r in records:
        assert r.confidence >= 0.8
        assert r.extraction_method == ExtractionMethod.STRUCTURED

    # Verify relevant links
    assert len(links) == 2
    assert links[0]["url"] == "/cfp"


async def test_pipeline_with_ai_extraction(
    conference_repo, source_repo, date_repo, extraction_repo
):
    """Pipeline should use AI extraction and populate all fields including topics."""
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
    <head><title>AAAI 2026</title></head>
    <body>
    <p>The 40th AAAI Conference on Artificial Intelligence</p>
    <p>February 20-27, 2026 in Philadelphia, PA, USA</p>
    <p>Submission deadline: September 15, 2025</p>
    </body>
    </html>
    """
    fake_result = FetchResult(
        url="https://aaai.org/conference/aaai-26",
        html=fake_html,
        content_hash="hash123",
        status_code=200,
    )

    ai_response = json.dumps({
        "name": "AAAI 2026 - 40th AAAI Conference on Artificial Intelligence",
        "acronym": "AAAI",
        "series": "AAAI Conference on Artificial Intelligence",
        "topics": ["artificial intelligence", "machine learning", "NLP"],
        "city": "Philadelphia",
        "country": "USA",
        "venue": "Pennsylvania Convention Center",
        "is_online": False,
        "is_hybrid": False,
        "start_date": "2026-02-20",
        "end_date": "2026-02-27",
        "cfp_url": None,
        "website_url": "https://aaai.org/conference/aaai-26",
        "important_dates": [
            {"type": "submission_deadline", "date": "2025-09-15", "note": "Paper submission"},
            {"type": "conference_start", "date": "2026-02-20", "note": "Conference begins"},
        ],
        "relevant_links": [],
    })

    mock_message = AsyncMock()
    mock_message.content = [AsyncMock(text=ai_response)]
    mock_client_instance = AsyncMock()
    mock_client_instance.messages.create = AsyncMock(return_value=mock_message)

    with patch(
        "academic_events.services.ingestion.pipeline.fetch_url",
        new_callable=AsyncMock,
        return_value=fake_result,
    ), patch(
        "academic_events.services.ingestion.pipeline.AI_EXTRACTION_ENABLED",
        True,
    ), patch(
        "academic_events.services.ingestion.pipeline.ANTHROPIC_API_KEY",
        "fake-key",
    ), patch(
        "academic_events.services.ingestion.ai_extractor.anthropic.AsyncAnthropic",
        return_value=mock_client_instance,
    ), patch(
        "academic_events.services.ingestion.pipeline.follow_relevant_links",
        new_callable=AsyncMock,
        return_value=[],
    ):
        result = await pipeline.ingest_url("https://aaai.org/conference/aaai-26")

    assert result.error is None
    assert result.conference_id is not None

    # Verify conference was populated with AI-extracted data
    conf = conference_repo.get(result.conference_id)
    assert conf is not None
    assert "AAAI" in conf.name
    assert conf.city == "Philadelphia"
    assert conf.country == "USA"
    assert conf.start_date == "2026-02-20"
    assert conf.end_date == "2026-02-27"

    # Verify important dates were created
    dates = date_repo.list_for_conference(result.conference_id)
    assert len(dates) >= 2

    # Verify extraction records were stored
    stored = extraction_repo.list_for_source(result.source.id)
    assert len(stored) > 0


async def test_pipeline_merge_ai_over_heuristic(
    conference_repo, source_repo, date_repo, extraction_repo
):
    """AI records should override heuristic records for the same field."""
    from academic_events.services.ingestion.pipeline import IngestionPipeline

    records = IngestionPipeline._merge_records(
        ai_records=[
            ExtractionRecord(
                source_id="s1",
                field_name="name",
                extracted_value="AI Conference Name",
                confidence=0.85,
                extraction_method=ExtractionMethod.STRUCTURED,
            ),
            ExtractionRecord(
                source_id="s1",
                field_name="city",
                extracted_value="Vienna",
                confidence=0.85,
                extraction_method=ExtractionMethod.STRUCTURED,
            ),
        ],
        heuristic_records=[
            ExtractionRecord(
                source_id="s1",
                field_name="name",
                extracted_value="Heuristic Name",
                confidence=0.7,
                extraction_method=ExtractionMethod.HEURISTIC,
            ),
            ExtractionRecord(
                source_id="s1",
                field_name="important_date:submission_deadline",
                extracted_value="2026-03-15",
                confidence=0.6,
                extraction_method=ExtractionMethod.HEURISTIC,
            ),
        ],
    )

    values = {r.field_name: r.extracted_value for r in records}
    # AI should win for "name"
    assert values["name"] == "AI Conference Name"
    # AI city should be present
    assert values["city"] == "Vienna"
    # Heuristic-only field should still be included
    assert "important_date:submission_deadline" in values
