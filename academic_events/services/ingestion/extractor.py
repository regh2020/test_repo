"""Heuristic and structured extraction of conference fields from text / HTML."""

from __future__ import annotations

import re
from datetime import datetime

from dateutil import parser as dateparser

from academic_events.models.conference import ExtractionMethod, ExtractionRecord


# --- Helpers ---

_DATE_PATTERNS = [
    # "January 15, 2026" / "Jan 15 2026"
    r"\b(\w+ \d{1,2},?\s*\d{4})\b",
    # "15 January 2026"
    r"\b(\d{1,2}\s+\w+\s+\d{4})\b",
    # ISO-ish "2026-01-15"
    r"\b(\d{4}-\d{2}-\d{2})\b",
]

_DEADLINE_KEYWORDS = {
    "submission": "submission_deadline",
    "abstract": "submission_deadline",
    "paper": "submission_deadline",
    "notification": "notification",
    "acceptance": "notification",
    "camera.?ready": "camera_ready",
    "final": "camera_ready",
    "workshop": "workshop_deadline",
    "early.?registration": "early_registration",
    "registration": "early_registration",
}

_URL_RE = re.compile(r"https?://[^\s<>\"']+")


def _try_parse_date(text: str) -> str | None:
    try:
        dt = dateparser.parse(text, fuzzy=False)
        if dt and 2020 <= dt.year <= 2035:
            return dt.strftime("%Y-%m-%d")
    except (ValueError, OverflowError):
        pass
    return None


def extract_fields(
    text: str, meta: dict, source_id: str
) -> list[ExtractionRecord]:
    """Return ExtractionRecords for every detected field."""
    records: list[ExtractionRecord] = []

    # --- Conference name from meta / title ---
    if "title" in meta:
        records.append(
            ExtractionRecord(
                source_id=source_id,
                field_name="name",
                extracted_value=meta["title"],
                confidence=0.7,
                extraction_method=ExtractionMethod.HEURISTIC,
                raw_snippet=meta["title"],
            )
        )

    # --- From JSON-LD ---
    jsonld = meta.get("jsonld")
    if jsonld:
        if "name" in jsonld:
            records.append(
                ExtractionRecord(
                    source_id=source_id,
                    field_name="name",
                    extracted_value=jsonld["name"],
                    confidence=0.95,
                    extraction_method=ExtractionMethod.STRUCTURED,
                    raw_snippet=str(jsonld.get("name")),
                )
            )
        if "startDate" in jsonld:
            d = _try_parse_date(jsonld["startDate"])
            if d:
                records.append(
                    ExtractionRecord(
                        source_id=source_id,
                        field_name="start_date",
                        extracted_value=d,
                        confidence=0.95,
                        extraction_method=ExtractionMethod.STRUCTURED,
                        raw_snippet=jsonld["startDate"],
                    )
                )
        if "endDate" in jsonld:
            d = _try_parse_date(jsonld["endDate"])
            if d:
                records.append(
                    ExtractionRecord(
                        source_id=source_id,
                        field_name="end_date",
                        extracted_value=d,
                        confidence=0.95,
                        extraction_method=ExtractionMethod.STRUCTURED,
                        raw_snippet=jsonld["endDate"],
                    )
                )
        loc = jsonld.get("location")
        if isinstance(loc, dict):
            addr = loc.get("address")
            if isinstance(addr, dict):
                if addr.get("addressLocality"):
                    records.append(
                        ExtractionRecord(
                            source_id=source_id,
                            field_name="city",
                            extracted_value=addr["addressLocality"],
                            confidence=0.9,
                            extraction_method=ExtractionMethod.STRUCTURED,
                            raw_snippet=str(addr),
                        )
                    )
                if addr.get("addressCountry"):
                    records.append(
                        ExtractionRecord(
                            source_id=source_id,
                            field_name="country",
                            extracted_value=addr["addressCountry"],
                            confidence=0.9,
                            extraction_method=ExtractionMethod.STRUCTURED,
                            raw_snippet=str(addr),
                        )
                    )
            elif isinstance(addr, str):
                records.append(
                    ExtractionRecord(
                        source_id=source_id,
                        field_name="city",
                        extracted_value=addr,
                        confidence=0.6,
                        extraction_method=ExtractionMethod.STRUCTURED,
                        raw_snippet=str(loc),
                    )
                )
            if loc.get("name"):
                records.append(
                    ExtractionRecord(
                        source_id=source_id,
                        field_name="venue",
                        extracted_value=loc["name"],
                        confidence=0.85,
                        extraction_method=ExtractionMethod.STRUCTURED,
                        raw_snippet=str(loc),
                    )
                )
        if jsonld.get("url"):
            records.append(
                ExtractionRecord(
                    source_id=source_id,
                    field_name="website_url",
                    extracted_value=jsonld["url"],
                    confidence=0.9,
                    extraction_method=ExtractionMethod.STRUCTURED,
                    raw_snippet=jsonld["url"],
                )
            )

    # --- Heuristic date extraction from plain text ---
    lines = text.split("\n")
    for line in lines:
        lower = line.lower()
        for keyword_re, date_type in _DEADLINE_KEYWORDS.items():
            if re.search(keyword_re, lower):
                for pat in _DATE_PATTERNS:
                    m = re.search(pat, line)
                    if m:
                        d = _try_parse_date(m.group(1))
                        if d:
                            records.append(
                                ExtractionRecord(
                                    source_id=source_id,
                                    field_name=f"important_date:{date_type}",
                                    extracted_value=d,
                                    confidence=0.6,
                                    extraction_method=ExtractionMethod.HEURISTIC,
                                    raw_snippet=line.strip()[:200],
                                )
                            )
                            break

    # --- CFP URL detection ---
    for line in lines:
        lower = line.lower()
        if "call for paper" in lower or "cfp" in lower:
            urls = _URL_RE.findall(line)
            for u in urls:
                records.append(
                    ExtractionRecord(
                        source_id=source_id,
                        field_name="cfp_url",
                        extracted_value=u,
                        confidence=0.65,
                        extraction_method=ExtractionMethod.HEURISTIC,
                        raw_snippet=line.strip()[:200],
                    )
                )

    return records
