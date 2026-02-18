"""AI-powered extraction of conference fields from unstructured text.

Uses the Anthropic Claude API to understand free-text conference pages
and extract structured data that heuristic regex patterns miss.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from academic_events.models.conference import ExtractionMethod, ExtractionRecord

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """\
You are an expert at extracting academic conference information from web pages.
Given the text content of a conference web page, extract all available information
into a structured JSON object.

Return ONLY a valid JSON object with these fields (use null for any field you cannot find):

{
  "name": "Full conference name",
  "acronym": "Conference acronym (e.g., ICML, NeurIPS, AAAI)",
  "series": "Conference series name if applicable",
  "topics": ["list", "of", "topics", "covered"],
  "city": "Host city",
  "country": "Host country",
  "venue": "Venue name",
  "is_online": false,
  "is_hybrid": false,
  "start_date": "YYYY-MM-DD format",
  "end_date": "YYYY-MM-DD format",
  "cfp_url": "URL to call for papers if found",
  "website_url": "Main conference website URL if found",
  "important_dates": [
    {
      "type": "submission_deadline|notification|camera_ready|workshop_deadline|early_registration|conference_start|conference_end|other",
      "date": "YYYY-MM-DD",
      "note": "Brief description of this date"
    }
  ],
  "relevant_links": [
    {
      "url": "URL",
      "description": "What this link leads to",
      "relevance": "high|medium|low"
    }
  ]
}

Rules:
- Dates must be in YYYY-MM-DD format. If only month/year given, use the 1st of the month.
- For is_online/is_hybrid, default to false unless clearly stated.
- Extract ALL important dates you find (deadlines, notifications, camera-ready, etc.).
- For relevant_links, identify links on the page that likely contain additional conference info (CFP pages, venue info, registration, important dates pages, etc.). Only include links with high or medium relevance.
- Be thorough: extract every piece of conference information visible in the text.
- Return ONLY the JSON object, no markdown, no explanation.
"""


async def ai_extract_fields(
    text: str,
    page_url: str,
    source_id: str,
    api_key: str | None = None,
) -> tuple[list[ExtractionRecord], list[dict]]:
    """Use AI to extract conference fields from unstructured text.

    Returns a tuple of (extraction_records, relevant_links).
    relevant_links is a list of dicts with 'url' and 'description' keys.
    """
    if not api_key:
        logger.warning("No Anthropic API key configured; AI extraction skipped")
        return [], []

    try:
        client = anthropic.AsyncAnthropic(api_key=api_key)
        message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Extract conference information from this web page.\n\n"
                        f"Page URL: {page_url}\n\n"
                        f"Page content:\n{text[:15000]}"
                    ),
                }
            ],
            system=_EXTRACTION_PROMPT,
        )
    except Exception as exc:
        logger.error("AI extraction API call failed: %s", exc)
        return [], []

    # Parse the AI response
    raw = message.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("AI extraction returned invalid JSON: %s", raw[:200])
        return [], []

    records: list[ExtractionRecord] = []

    # Map simple fields
    _FIELD_MAP = {
        "name": "name",
        "acronym": "acronym",
        "series": "series",
        "city": "city",
        "country": "country",
        "venue": "venue",
        "start_date": "start_date",
        "end_date": "end_date",
        "cfp_url": "cfp_url",
        "website_url": "website_url",
    }

    for json_key, field_name in _FIELD_MAP.items():
        value = data.get(json_key)
        if value and isinstance(value, str):
            records.append(
                ExtractionRecord(
                    source_id=source_id,
                    field_name=field_name,
                    extracted_value=value,
                    confidence=0.85,
                    extraction_method=ExtractionMethod.STRUCTURED,
                    raw_snippet=f"AI-extracted from {page_url}",
                )
            )

    # Boolean fields
    if data.get("is_online") is True:
        records.append(
            ExtractionRecord(
                source_id=source_id,
                field_name="is_online",
                extracted_value="true",
                confidence=0.85,
                extraction_method=ExtractionMethod.STRUCTURED,
                raw_snippet=f"AI-extracted from {page_url}",
            )
        )
    if data.get("is_hybrid") is True:
        records.append(
            ExtractionRecord(
                source_id=source_id,
                field_name="is_hybrid",
                extracted_value="true",
                confidence=0.85,
                extraction_method=ExtractionMethod.STRUCTURED,
                raw_snippet=f"AI-extracted from {page_url}",
            )
        )

    # Topics
    topics = data.get("topics")
    if topics and isinstance(topics, list):
        topics_str = json.dumps([t for t in topics if isinstance(t, str)])
        records.append(
            ExtractionRecord(
                source_id=source_id,
                field_name="topics",
                extracted_value=topics_str,
                confidence=0.8,
                extraction_method=ExtractionMethod.STRUCTURED,
                raw_snippet=f"AI-extracted from {page_url}",
            )
        )

    # Important dates
    important_dates = data.get("important_dates") or []
    for item in important_dates:
        if not isinstance(item, dict):
            continue
        date_type = item.get("type", "other")
        date_val = item.get("date")
        note = item.get("note", "")
        if date_val:
            records.append(
                ExtractionRecord(
                    source_id=source_id,
                    field_name=f"important_date:{date_type}",
                    extracted_value=date_val,
                    confidence=0.85,
                    extraction_method=ExtractionMethod.STRUCTURED,
                    raw_snippet=note or f"AI-extracted from {page_url}",
                )
            )

    # Relevant links
    relevant_links: list[dict] = []
    for link in data.get("relevant_links") or []:
        if isinstance(link, dict) and link.get("url"):
            relevance = link.get("relevance", "low")
            if relevance in ("high", "medium"):
                relevant_links.append(
                    {
                        "url": link["url"],
                        "description": link.get("description", ""),
                    }
                )

    logger.info(
        "AI extraction from %s: %d records, %d relevant links",
        page_url,
        len(records),
        len(relevant_links),
    )
    return records, relevant_links
