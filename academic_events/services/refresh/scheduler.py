"""Refresh scheduler using APScheduler."""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from academic_events.config import DEFAULT_REFRESH_INTERVAL_HOURS

logger = logging.getLogger(__name__)


class RefreshScheduler:
    """Wraps APScheduler to periodically trigger refresh jobs."""

    def __init__(self, refresh_callback):
        """*refresh_callback* is an async callable that refreshes all due sources."""
        self._callback = refresh_callback
        self._scheduler = BackgroundScheduler()
        self._running = False

    def _run_refresh(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(self._callback())
            loop.close()
        except Exception:
            logger.exception("Scheduled refresh failed")

    def start(self, interval_hours: int = DEFAULT_REFRESH_INTERVAL_HOURS) -> None:
        if self._running:
            return
        self._scheduler.add_job(
            self._run_refresh,
            "interval",
            hours=interval_hours,
            id="refresh_all",
            replace_existing=True,
        )
        self._scheduler.start()
        self._running = True
        logger.info("Refresh scheduler started (interval=%dh)", interval_hours)

    def stop(self) -> None:
        if self._running:
            self._scheduler.shutdown(wait=False)
            self._running = False
            logger.info("Refresh scheduler stopped")
