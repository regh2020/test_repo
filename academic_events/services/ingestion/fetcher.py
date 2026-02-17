"""Fetch HTML content from a URL."""

from __future__ import annotations

import hashlib
import logging

import httpx

from academic_events.config import FETCH_TIMEOUT_SECONDS, USER_AGENT

logger = logging.getLogger(__name__)


class FetchResult:
    def __init__(self, url: str, html: str, content_hash: str, status_code: int):
        self.url = url
        self.html = html
        self.content_hash = content_hash
        self.status_code = status_code


async def fetch_url(url: str) -> FetchResult:
    """Download HTML from *url* and return a FetchResult."""
    async with httpx.AsyncClient(
        follow_redirects=True,
        timeout=FETCH_TIMEOUT_SECONDS,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text
        content_hash = hashlib.sha256(html.encode()).hexdigest()
        logger.info("Fetched %s (status=%d, hash=%s)", url, resp.status_code, content_hash[:12])
        return FetchResult(
            url=url,
            html=html,
            content_hash=content_hash,
            status_code=resp.status_code,
        )
