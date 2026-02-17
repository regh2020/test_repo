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
