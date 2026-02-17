"""Basic web search for conference discovery.

Uses httpx to query a search-engine-like endpoint. In a real deployment this
would call an actual search API (Google Custom Search, Bing, SerpAPI, etc.).
The current implementation provides the interface and a mock/demo mode.
"""

from __future__ import annotations

import logging
import re

import httpx

from academic_events.config import FETCH_TIMEOUT_SECONDS, USER_AGENT
from academic_events.models.discovery import DiscoveryCandidate

logger = logging.getLogger(__name__)


async def web_search(query: str, max_results: int = 10) -> list[DiscoveryCandidate]:
    """Search the web for conference pages matching *query*.

    This is a placeholder that attempts a real HTTP search against a
    configurable endpoint.  When no search API key is configured, it
    returns an empty list.  Integrators can swap this out for SerpAPI,
    Google Custom Search, etc.
    """
    # Placeholder: in production, call a real search API here.
    logger.info("Web search query: %s (max_results=%d)", query, max_results)
    return []
