"""Follow relevant links from a conference page to gather additional data."""

from __future__ import annotations

import logging
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from academic_events.services.ingestion.cleaner import clean_html
from academic_events.services.ingestion.fetcher import fetch_url

logger = logging.getLogger(__name__)

# Keywords that indicate a link leads to relevant conference sub-pages
_RELEVANT_LINK_KEYWORDS = [
    "call for paper",
    "cfp",
    "important date",
    "deadline",
    "submission",
    "registration",
    "venue",
    "program",
    "schedule",
    "speaker",
    "keynote",
    "workshop",
    "tutorial",
    "accepted paper",
    "camera ready",
    "author info",
    "committee",
]

# Maximum number of sub-pages to follow
MAX_LINKED_PAGES = 5


def extract_links(html: str, base_url: str) -> list[dict]:
    """Extract all links from HTML, resolving relative URLs.

    Returns list of dicts with 'url', 'text', and 'relevance_score' keys.
    """
    soup = BeautifulSoup(html, "lxml")
    base_domain = urlparse(base_url).netloc
    links: list[dict] = []
    seen_urls: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
            continue

        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Only follow links on the same domain or common conference domains
        if parsed.netloc and parsed.netloc != base_domain:
            continue

        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # Score relevance based on link text and URL
        link_text = a_tag.get_text(strip=True).lower()
        url_lower = full_url.lower()
        score = 0
        for keyword in _RELEVANT_LINK_KEYWORDS:
            if keyword in link_text or keyword.replace(" ", "") in url_lower:
                score += 1

        if score > 0:
            links.append(
                {
                    "url": full_url,
                    "text": a_tag.get_text(strip=True),
                    "relevance_score": score,
                }
            )

    # Sort by relevance, highest first
    links.sort(key=lambda x: x["relevance_score"], reverse=True)
    return links


async def follow_relevant_links(
    html: str,
    base_url: str,
    ai_suggested_links: list[dict] | None = None,
    max_pages: int = MAX_LINKED_PAGES,
) -> list[dict]:
    """Fetch relevant sub-pages linked from the main conference page.

    Returns list of dicts with 'url' and 'text' (cleaned content) keys.
    """
    # Collect links from HTML analysis
    page_links = extract_links(html, base_url)

    # Merge AI-suggested links (they get priority)
    all_urls: list[str] = []
    seen: set[str] = set()

    if ai_suggested_links:
        for link in ai_suggested_links:
            url = link.get("url", "")
            if url and url not in seen and url != base_url:
                # Resolve relative URLs from AI suggestions too
                resolved = urljoin(base_url, url)
                if resolved not in seen:
                    all_urls.append(resolved)
                    seen.add(resolved)

    for link in page_links:
        url = link["url"]
        if url not in seen and url != base_url:
            all_urls.append(url)
            seen.add(url)

    # Limit to max_pages
    urls_to_fetch = all_urls[:max_pages]
    results: list[dict] = []

    for url in urls_to_fetch:
        try:
            fetch_result = await fetch_url(url)
            text = clean_html(fetch_result.html)
            if text.strip():
                results.append({"url": url, "text": text})
                logger.info("Followed link: %s (%d chars)", url, len(text))
        except Exception as exc:
            logger.warning("Failed to follow link %s: %s", url, exc)
            continue

    return results
