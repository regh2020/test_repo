"""Discovery service: search web and social platforms for conferences."""

from __future__ import annotations

import logging
from datetime import datetime

from academic_events.models.discovery import DiscoveryCandidate, DiscoveryQuery, DiscoveryRun
from academic_events.repositories.interfaces import DiscoveryRepository
from academic_events.services.discovery.twitter_connector import StubTwitterConnector, TwitterConnector
from academic_events.services.discovery.web_search import web_search

logger = logging.getLogger(__name__)


class DiscoveryService:
    def __init__(
        self,
        discovery_repo: DiscoveryRepository,
        twitter_connector: TwitterConnector | None = None,
    ):
        self._repo = discovery_repo
        self._twitter = twitter_connector or StubTwitterConnector()

    async def discover(self, query: DiscoveryQuery) -> DiscoveryRun:
        search_terms = " ".join(query.keywords + query.topics)
        if query.date_range_start:
            search_terms += f" {query.date_range_start}"
        search_terms += " conference"

        run = DiscoveryRun(query=search_terms)

        # Web search
        web_candidates = await web_search(search_terms)
        run.candidates.extend(web_candidates)

        # Twitter search
        if query.include_twitter:
            twitter_candidates = await self._twitter.search(search_terms)
            for c in twitter_candidates:
                c.source_type = "twitter"
            run.candidates.extend(twitter_candidates)

        # Deduplicate by URL
        seen_urls: set[str] = set()
        deduped: list[DiscoveryCandidate] = []
        for c in run.candidates:
            if c.url not in seen_urls:
                seen_urls.add(c.url)
                deduped.append(c)
        run.candidates = deduped

        run.finished_at = datetime.utcnow().isoformat()

        # Persist
        self._repo.create(run)
        logger.info("Discovery run %s: %d candidates", run.id, len(run.candidates))
        return run
