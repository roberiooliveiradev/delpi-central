"""Scheduled ingestion job — market data feeds (PROC-0076).

Runs outside the HTTP request path (cron / container exec):

    python -m app.jobs.ingest_market_data --feed fx-daily
    python -m app.jobs.ingest_market_data --feed metals-monthly \
        --from 2024-01-01 --to 2026-12-31

Guards: the feed must be enabled by env flag AND its source must be
active+licensed in the catalog; a PostgreSQL advisory lock prevents
concurrent runs of the same feed; upserts are idempotent so re-running
a window is safe. Exit code is non-zero on failure so schedulers alert.
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid
from datetime import date, timedelta

from app.application.contracts import ExternalDataError
from app.application.market_data_ingestion import (
    MarketDataIngestionService,
    feed_enabled,
)
from app.domain.market_data import (
    FEED_COMEX_MONTHLY,
    FEED_FX_DAILY,
    FEED_IPP_MONTHLY,
    FEED_METALS_DAILY,
    FEED_METALS_MONTHLY,
    FEED_METALS_PRICES_DAILY,
    SUPPORTED_FEEDS,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.market_contract_readiness import (
    check_market_contract_ready,
)
from app.infrastructure.persistence.market_data_repository import (
    MarketDataRepository,
)
from app.infrastructure.persistence.plugins_db import get_connection
from app.infrastructure.providers.comex_import_provider import (
    build_comex_provider,
)
from app.infrastructure.providers.ibge_ipp_provider import build_ipp_provider
from app.infrastructure.providers.ptax_fx_provider import build_ptax_provider
from app.infrastructure.providers.metalcharts_provider import (
    build_metalcharts_provider,
)
from app.infrastructure.providers.worldbank_pinksheet_provider import (
    build_pinksheet_provider,
)

logger = logging.getLogger("external-data-api.jobs.ingest_market_data")

# Rolling defaults: PTAX publishes on business days; the Pink Sheet
# publishes monthly with a few days of lag.
_DEFAULT_WINDOW_DAYS = {
    FEED_FX_DAILY: 35,
    FEED_METALS_MONTHLY: 400,
    # MetalCharts Free hard-stops history beyond 30 days (verified
    # S1: a 35-day window is refused upstream with 403); 29 days keeps
    # every request inside the plan's daily-bars window with margin.
    FEED_METALS_DAILY: 29,
    # R11 — /v1/prices is a snapshot call; the CLI window is unused, but
    # the key must exist for manual runs.
    FEED_METALS_PRICES_DAILY: 1,
    FEED_COMEX_MONTHLY: 400,
    FEED_IPP_MONTHLY: 400,
}


def _parse_date(raw: str | None, fallback: date) -> date:
    if not raw:
        return fallback
    return date.fromisoformat(raw)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ingest_market_data",
        description="external-data-api market data ingestion job",
    )
    parser.add_argument("--feed", required=True, choices=SUPPORTED_FEEDS)
    parser.add_argument("--from", dest="date_from", default=None)
    parser.add_argument("--to", dest="date_to", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=getattr(logging, (Settings.LOG_LEVEL or "INFO").upper())
    )
    args = _build_parser().parse_args(argv)
    feed = args.feed

    if not feed_enabled(feed):
        logger.warning("ingest_skipped feed=%s reason=disabled", feed)
        return 0  # disabled is a deliberate state, not a failure
    if not Settings.plugins_db_configured():
        logger.error("ingest_failed feed=%s reason=storage_not_configured", feed)
        return 2

    today = date.today()
    date_from = _parse_date(
        args.date_from, today - timedelta(days=_DEFAULT_WINDOW_DAYS[feed])
    )
    date_to = _parse_date(args.date_to, today)

    correlation_id = str(uuid.uuid4())
    try:
        with get_connection() as conn:
            # The feed may be enabled by env while the rights contract is
            # still pending — an unproven catalog must not be written to.
            check_market_contract_ready(conn)
            repo = MarketDataRepository(
                conn, schema=Settings.EXTERNAL_DATA_SCHEMA
            )
            service = MarketDataIngestionService(
                repository=repo,
                fx_provider=build_ptax_provider(),
                metals_provider=build_pinksheet_provider(),
                metalcharts_provider=build_metalcharts_provider(),
                comex_provider=build_comex_provider(),
                ipp_provider=build_ipp_provider(),
            )
            result = service.run(
                feed,
                date_from=date_from,
                date_to=date_to,
                correlation_id=correlation_id,
            )
    except ExternalDataError as exc:
        logger.error(
            "ingest_failed feed=%s code=%s correlation_id=%s",
            feed,
            exc.code,
            correlation_id,
        )
        return 3
    except Exception:  # noqa: BLE001 — top-level job guard
        logger.exception(
            "ingest_failed feed=%s reason=unexpected correlation_id=%s",
            feed,
            correlation_id,
        )
        return 3

    logger.info(
        "ingest_done feed=%s outcome=%s fetched=%s inserted=%s updated=%s "
        "skipped=%s correlation_id=%s",
        feed,
        result.outcome,
        result.fetched_count,
        result.inserted_count,
        result.updated_count,
        result.skipped_count,
        correlation_id,
    )
    return 0 if result.outcome in {"success", "partial"} else 4


if __name__ == "__main__":
    sys.exit(main())
