"""Market-data ingest scheduler (PROC-0076 R10).

Canonical runtime trigger for scheduled feeds: a dedicated container
(``external-data-scheduler``) running this loop — versioned in the
compose file, restart-safe, and outside the HTTP request path. Portal
page loads never reach upstream.

Semantics per feed:

- at most one attempt per local day, after
  ``EXTERNAL_DATA_SCHEDULER_RUN_AT`` (container TZ);
- an attempt is due only when the last SUCCESSFUL run is older than
  the feed's interval (``EXTERNAL_DATA_SCHEDULER_<FEED>_INTERVAL_DAYS``,
  default ``EXTERNAL_DATA_SCHEDULER_INTERVAL_DAYS``);
- a failed attempt is retried on the next day — never a hot retry
  loop, so a blocked provider cannot burn the API weight allowance;
- every attempt is recorded in ``market_data_ingestion_runs`` by the
  job itself and surfaces in ``/v1/market-data/ingestion-status``;
- due/attempt state derives from persisted run rows, so a container
  restart can neither skip a due feed nor repeat a done one;
- per-feed env flags and the source catalog/rights guard inside the
  job remain the effective kill switch — this scheduler can never
  run a disabled feed.

The job is invoked via ``python -m app.jobs.ingest_market_data`` so
the tested CLI contract (flags, advisory lock, logging, exit codes)
is reused verbatim.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from datetime import date, datetime, time as dtime, timedelta
from typing import Any, Callable

from app.domain.market_data import SUPPORTED_FEEDS
from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.market_data_repository import (
    MarketDataRepository,
)
from app.infrastructure.persistence.plugins_db import get_connection

logger = logging.getLogger("external-data-api.jobs.ingest_scheduler")


def _parse_run_at(raw: str) -> dtime:
    """HH:MM local wall-clock — invalid input fails closed to 20:30."""
    try:
        hour, minute = raw.split(":", 1)
        return dtime(hour=int(hour), minute=int(minute))
    except (ValueError, TypeError):
        logger.warning("scheduler_run_at_invalid raw=%s fallback=20:30", raw)
        return dtime(hour=20, minute=30)


def _interval_days(feed: str) -> int:
    env_name = (
        "EXTERNAL_DATA_SCHEDULER_"
        + feed.upper().replace("-", "_")
        + "_INTERVAL_DAYS"
    )
    raw = os.getenv(env_name, "").strip()
    if raw:
        try:
            return max(1, int(raw))
        except ValueError:
            logger.warning(
                "scheduler_interval_invalid feed=%s raw=%s", feed, raw
            )
    return max(1, Settings.EXTERNAL_DATA_SCHEDULER_INTERVAL_DAYS)


def feed_due(
    *,
    now: datetime,
    last_attempt_at: datetime | None,
    last_success_at: datetime | None,
    interval_days: int,
    run_at: dtime,
) -> bool:
    """Decide whether ``feed`` should attempt a run right now.

    - before ``run_at`` today → not due;
    - any attempt already recorded today (success OR failure — a
      manual recovery run counts) → not due until tomorrow;
    - last success within ``interval_days`` → not due.
    """
    if now.time() < run_at:
        return False
    if last_attempt_at is not None and last_attempt_at.date() >= now.date():
        return False
    if last_success_at is not None and (
        last_success_at.date() + timedelta(days=interval_days) > now.date()
    ):
        return False
    return True


def _last_attempt(success_entry: dict[str, Any]) -> datetime | None:
    for key in ("last_run_started_at", "last_successful_at"):
        value = success_entry.get(key)
        if isinstance(value, datetime):
            return value
    return None


def _run_feed(feed: str) -> int:
    return subprocess.call(
        [sys.executable, "-m", "app.jobs.ingest_market_data", "--feed", feed]
    )


def _tick(
    *,
    repo: MarketDataRepository,
    feeds: tuple[str, ...],
    now: datetime,
    run_at: dtime,
    runner: Callable[[str], int] = _run_feed,
) -> None:
    statuses = {s["feed"]: s for s in repo.feed_statuses()}
    for feed in feeds:
        if feed not in SUPPORTED_FEEDS:
            logger.warning("scheduler_unknown_feed feed=%s", feed)
            continue
        entry = statuses.get(feed) or {}
        due = feed_due(
            now=now,
            last_attempt_at=_last_attempt(entry),
            last_success_at=entry.get("last_successful_at"),
            interval_days=_interval_days(feed),
            run_at=run_at,
        )
        if not due:
            continue
        logger.info("scheduler_feed_due feed=%s", feed)
        code = runner(feed)
        logger.info("scheduler_feed_done feed=%s exit_code=%s", feed, code)


def _sleep_idle() -> None:
    # Disabled scheduler stays alive but inert — a clean exit(0) would
    # be restart-looped by the container policy, and a disabled state
    # must be observable, not crash-looping.
    time.sleep(3600)


def main() -> int:
    logging.basicConfig(
        level=getattr(logging, (Settings.LOG_LEVEL or "INFO").upper())
    )
    run_at = _parse_run_at(Settings.EXTERNAL_DATA_SCHEDULER_RUN_AT)
    feeds = Settings.EXTERNAL_DATA_SCHEDULER_FEEDS
    poll = max(30, Settings.EXTERNAL_DATA_SCHEDULER_POLL_SECONDS)
    logger.info(
        "scheduler_start enabled=%s feeds=%s run_at=%s poll_s=%s",
        Settings.EXTERNAL_DATA_SCHEDULER_ENABLED,
        ",".join(feeds),
        run_at.isoformat(timespec="minutes"),
        poll,
    )
    while True:
        if not Settings.EXTERNAL_DATA_SCHEDULER_ENABLED:
            _sleep_idle()
            continue
        try:
            with get_connection() as conn:
                repo = MarketDataRepository(
                    conn, schema=Settings.EXTERNAL_DATA_SCHEMA
                )
                _tick(repo=repo, feeds=feeds, now=datetime.now(),
                      run_at=run_at)
        except Exception:  # noqa: BLE001 — scheduler must not die
            logger.exception("scheduler_tick_failed")
        time.sleep(poll)


if __name__ == "__main__":
    sys.exit(main())
