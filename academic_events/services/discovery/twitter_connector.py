"""Pluggable Twitter/X connector interface and stub implementation."""

from __future__ import annotations

import abc

from academic_events.models.discovery import DiscoveryCandidate


class TwitterConnector(abc.ABC):
    """Interface for searching Twitter/X for conference announcements."""

    @abc.abstractmethod
    async def search(self, query: str, max_results: int = 20) -> list[DiscoveryCandidate]: ...


class StubTwitterConnector(TwitterConnector):
    """Stub that returns no results. Replace with real API connector when available."""

    async def search(self, query: str, max_results: int = 20) -> list[DiscoveryCandidate]:
        return []
