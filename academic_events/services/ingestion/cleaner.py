"""Remove boilerplate / navigation from HTML and return clean text."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup


def clean_html(html: str) -> str:
    """Strip navigation, scripts, styles and return visible text."""
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def get_meta_and_structured(html: str) -> dict:
    """Extract meta tags and schema.org Event JSON-LD if present."""
    soup = BeautifulSoup(html, "lxml")
    meta: dict = {}

    # <title>
    if soup.title and soup.title.string:
        meta["title"] = soup.title.string.strip()

    # Open Graph / meta description
    for tag in soup.find_all("meta"):
        prop = tag.get("property", tag.get("name", "")).lower()
        content = tag.get("content", "")
        if prop in ("og:title", "og:description", "description", "og:url"):
            meta[prop] = content

    # schema.org JSON-LD
    import json

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict) and data.get("@type") in ("Event", "ScholarlyArticle"):
                meta["jsonld"] = data
                break
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") in (
                        "Event",
                        "ScholarlyArticle",
                    ):
                        meta["jsonld"] = item
                        break
                if "jsonld" in meta:
                    break
        except (json.JSONDecodeError, TypeError):
            continue

    return meta
