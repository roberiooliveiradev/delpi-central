"""Market data ingestion use case (PROC-0076).

The job flow: enabled feed (env) → licensed+active source (catalog) →
advisory lock → provider fetch → validate/normalize → idempotent upsert
→ ingestion_run bookkeeping. A partial batch is marked ``partial``, a
failed fetch ``failed`` — never ``success``. Feeds refuse to run when
the source is missing, inactive or unlicensed.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.application.contracts import (
    ExternalDataError,
    RateLimitedError,
    SourceNotLicensedError,
    StorageUnavailableError,
)
from app.domain import usage_policy
from app.domain.market_data import (
    FEED_COMEX_MONTHLY,
    FEED_FX_DAILY,
    FEED_IPP_MONTHLY,
    FEED_METALS_DAILY,
    FEED_METALS_MONTHLY,
    FEED_METALS_PRICES_DAILY,
    PROVIDER_BCB_PTAX,
    PROVIDER_IBGE_IPP,
    PROVIDER_MDIC_COMEX,
    PROVIDER_METALCHARTS,
    PROVIDER_WORLDBANK_PINK_SHEET,
    QUALITY_VALIDATED,
    RETENTION_PERMANENT,
    spot_last_quote_basis,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.market_data_repository import utcnow
from app.infrastructure.providers.metalcharts_provider import (
    WEIGHT_HISTORY,
    WEIGHT_SPOT,
    params_hash,
)
from app.application.metalcharts_budget import MetalChartsBudget

logger = logging.getLogger("external-data-api.ingestion")

INGESTION_VERSION = "proc-0076-p0-v1"

# Distinct advisory lock keys per feed — prevents concurrent runs of the
# same feed while allowing metals and fx to ingest in parallel.
ADVISORY_LOCK_KEYS = {
    FEED_METALS_MONTHLY: 76007601,
    FEED_FX_DAILY: 76007602,
    FEED_COMEX_MONTHLY: 76007603,
    FEED_IPP_MONTHLY: 76007604,
    FEED_METALS_DAILY: 76007605,
    FEED_METALS_PRICES_DAILY: 76007606,
}


class FeedDisabledError(ExternalDataError):
    http_status = 503
    code = "EXTERNAL_DATA_FEED_DISABLED"


class IngestionLockedError(ExternalDataError):
    http_status = 503
    code = "EXTERNAL_DATA_INGESTION_LOCKED"


class NoApprovedSeriesError(ExternalDataError):
    """The feed is enabled and the source licensed, but the business
    allowlist is empty — no approved NCM/SIDRA series to collect."""

    http_status = 503
    code = "EXTERNAL_DATA_NO_APPROVED_SERIES"


@dataclass(frozen=True)
class IngestionResult:
    feed: str
    outcome: str
    fetched_count: int
    inserted_count: int
    updated_count: int
    skipped_count: int
    run_id: str | None
    error_code: str | None = None


def feed_enabled(feed: str) -> bool:
    if feed == FEED_FX_DAILY:
        return bool(Settings.EXTERNAL_DATA_FEED_FX_DAILY_ENABLED)
    if feed == FEED_METALS_MONTHLY:
        return bool(Settings.EXTERNAL_DATA_FEED_METALS_MONTHLY_ENABLED)
    if feed == FEED_METALS_DAILY:
        return bool(Settings.EXTERNAL_DATA_FEED_METALS_DAILY_ENABLED)
    if feed == FEED_METALS_PRICES_DAILY:
        return bool(
            Settings.EXTERNAL_DATA_FEED_METALS_PRICES_DAILY_ENABLED
        )
    if feed == FEED_COMEX_MONTHLY:
        return bool(Settings.EXTERNAL_DATA_FEED_COMEX_MONTHLY_ENABLED)
    if feed == FEED_IPP_MONTHLY:
        return bool(Settings.EXTERNAL_DATA_FEED_IPP_MONTHLY_ENABLED)
    return False


def provider_id_for_feed(feed: str) -> str:
    return {
        FEED_FX_DAILY: PROVIDER_BCB_PTAX,
        FEED_METALS_MONTHLY: PROVIDER_WORLDBANK_PINK_SHEET,
        FEED_METALS_DAILY: PROVIDER_METALCHARTS,
        FEED_METALS_PRICES_DAILY: PROVIDER_METALCHARTS,
        FEED_COMEX_MONTHLY: PROVIDER_MDIC_COMEX,
        FEED_IPP_MONTHLY: PROVIDER_IBGE_IPP,
    }[feed]


class MarketDataIngestionService:
    """Coordinates one feed run; every collaborator is injectable."""

    def __init__(
        self,
        *,
        repository: Any,
        fx_provider: Any = None,
        metals_provider: Any = None,
        metalcharts_provider: Any = None,
        metalcharts_budget: Any = None,
        comex_provider: Any = None,
        ipp_provider: Any = None,
        clock: Any = utcnow,
    ) -> None:
        self._repo = repository
        self._fx_provider = fx_provider
        self._metals_provider = metals_provider
        self._metalcharts_provider = metalcharts_provider
        self._metalcharts_budget = metalcharts_budget
        self._comex_provider = comex_provider
        self._ipp_provider = ipp_provider
        self._clock = clock

    def run(
        self,
        feed: str,
        *,
        date_from: date,
        date_to: date,
        correlation_id: str | None = None,
    ) -> IngestionResult:
        correlation_id = correlation_id or str(uuid.uuid4())
        if not feed_enabled(feed):
            raise FeedDisabledError(f"feed {feed} is disabled by configuration")
        lock_key = ADVISORY_LOCK_KEYS[feed]
        if not self._repo.try_advisory_lock(lock_key):
            raise IngestionLockedError(
                f"feed {feed} is already running (advisory lock held)"
            )
        try:
            return self._run_locked(
                feed,
                date_from=date_from,
                date_to=date_to,
                correlation_id=correlation_id,
            )
        finally:
            self._repo.release_advisory_lock(lock_key)

    # --- internals ---------------------------------------------------------

    def _run_locked(self, feed, *, date_from, date_to, correlation_id):
        provider_id = provider_id_for_feed(feed)
        run_id = self._repo.create_ingestion_run(
            provider_id=provider_id,
            feed=feed,
            correlation_id=correlation_id,
            version=INGESTION_VERSION,
        )
        self._repo.commit()

        fetched = inserted = updated = skipped = 0
        outcome = "failed"
        error_code: str | None = None
        try:
            if feed == FEED_METALS_MONTHLY:
                fetched, inserted, updated, skipped = self._ingest_metals(
                    date_from, date_to
                )
            elif feed == FEED_METALS_DAILY:
                fetched, inserted, updated, skipped = (
                    self._ingest_metals_daily(
                        date_from, date_to, correlation_id
                    )
                )
            elif feed == FEED_METALS_PRICES_DAILY:
                fetched, inserted, updated, skipped = (
                    self._ingest_metals_prices_daily(correlation_id)
                )
            elif feed == FEED_COMEX_MONTHLY:
                fetched, inserted, updated, skipped = self._ingest_comex(
                    date_from, date_to
                )
            elif feed == FEED_IPP_MONTHLY:
                fetched, inserted, updated, skipped = self._ingest_ipp(
                    date_from, date_to
                )
            else:
                fetched, inserted, updated, skipped = self._ingest_fx(
                    date_from, date_to
                )
            # A completed fetch is a successful run even when the upstream
            # window was empty or every row was an unchanged duplicate.
            outcome = "success"
        except SourceNotLicensedError as exc:
            error_code = exc.code
            logger.warning("ingestion_source_not_licensed feed=%s", feed)
        except ExternalDataError as exc:
            error_code = exc.code
            logger.warning("ingestion_failed feed=%s code=%s", feed, exc.code)
        except Exception:  # noqa: BLE001 — job must never swallow silently
            error_code = "UNEXPECTED_INGESTION_ERROR"
            logger.exception("ingestion_unexpected_failure feed=%s", feed)

        if error_code is not None and (inserted + updated) > 0:
            outcome = "partial"
        elif error_code is not None:
            outcome = "failed"

        self._repo.finish_ingestion_run(
            run_id,
            outcome=outcome,
            fetched_count=fetched,
            inserted_count=inserted,
            updated_count=updated,
            skipped_count=skipped,
            safe_error_code=error_code,
        )
        self._repo.commit()
        logger.info(
            "ingestion_run_finished feed=%s outcome=%s fetched=%s "
            "inserted=%s updated=%s skipped=%s",
            feed,
            outcome,
            fetched,
            inserted,
            updated,
            skipped,
        )
        return IngestionResult(
            feed=feed,
            outcome=outcome,
            fetched_count=fetched,
            inserted_count=inserted,
            updated_count=updated,
            skipped_count=skipped,
            run_id=run_id,
            error_code=error_code,
        )

    def _check_source(self, source_id: str) -> None:
        """Fail-closed per-operation rights (R1.2): active alone is not
        a grant — collecting and storing require explicit ``collect`` and
        ``store`` tokens in ``allowed_use_scope``. A feed enabled by env
        still cannot run while the recorded rights do not cover the
        operations it performs."""
        source = self._repo.get_source(source_id)
        if source is None or not source.active:
            raise SourceNotLicensedError(
                f"source {source_id} is not active/licensed in the catalog"
            )
        if not usage_policy.allows_all(
            source.allowed_use_scope,
            (usage_policy.OP_COLLECT, usage_policy.OP_STORE),
        ):
            raise SourceNotLicensedError(
                f"source {source_id} lacks approved collect/store use"
            )

    def _check_cache_source(self, source_id: str) -> None:
        """TTL-cache feeds need ``collect`` + ``store_cache_only`` —
        deliberately NOT the permanent ``store`` grant, so a source
        whose terms forbid retention can never reach the permanent
        observation tables through this path either."""
        source = self._repo.get_source(source_id)
        if source is None or not source.active:
            raise SourceNotLicensedError(
                f"source {source_id} is not active/licensed in the catalog"
            )
        if not usage_policy.allows_all(
            source.allowed_use_scope,
            (
                usage_policy.OP_COLLECT,
                usage_policy.OP_STORE_CACHE_ONLY,
            ),
        ):
            raise SourceNotLicensedError(
                f"source {source_id} lacks approved "
                "collect/store_cache_only use"
            )

    def _ingest_metals(self, date_from: date, date_to: date):
        source_id = PROVIDER_WORLDBANK_PINK_SHEET
        self._check_source(source_id)
        instruments = [
            inst
            for inst in self._repo.list_instruments()
            if inst.active and inst.source_id == source_id
        ]
        rows = self._metals_provider.fetch_period(
            instruments, date_from, date_to
        )
        by_code = {i.instrument_code: i for i in instruments}
        retrieved_at = self._clock()
        inserted = updated = skipped = 0
        for row in rows:
            inst = by_code.get(row["instrument_code"])
            if inst is None:
                skipped += 1
                continue
            outcome = self._repo.upsert_metal_observation(
                instrument_id=inst.instrument_id,
                observation_date=row["observation_date"],
                native_price=row["price"],
                native_currency=inst.native_currency,
                unit_code=inst.unit_code,
                quote_basis=inst.quotation_basis,
                source_id=source_id,
                source_record_key=row.get("source_record_key"),
                retrieved_at=retrieved_at,
            )
            if outcome == "inserted":
                inserted += 1
            elif outcome == "updated":
                updated += 1
            else:
                skipped += 1
        return len(rows), inserted, updated, skipped

    def _ingest_metals_daily(
        self, date_from: date, date_to: date, correlation_id: str
    ):
        """MetalCharts daily bars → TTL cache (PROC-0076 R5).

        Only active bindings with a verified ``source_series_key`` are
        collected — an unverified symbol is never guessed. Every call
        is pre-charged against the monthly + per-minute weight budget
        and recorded in the ledger; rows land in ``metal_quote_cache``
        with a mandatory ``expires_at`` (operational cache, not
        permanent retention)."""
        source_id = PROVIDER_METALCHARTS
        self._check_cache_source(source_id)
        if self._metalcharts_provider is None or not getattr(
            self._metalcharts_provider, "configured", lambda: True
        )():
            raise SourceNotLicensedError(
                "metalcharts provider is not configured (no api key)"
            )
        bindings = [
            b
            for b in self._repo.list_instrument_sources(
                source_id=source_id, active_only=True
            )
            if b.source_series_key
        ]
        if not bindings:
            raise NoApprovedSeriesError(
                "no active metalcharts bindings with verified symbols"
            )
        budget = self._metalcharts_budget or MetalChartsBudget(
            repository=self._repo, clock=self._clock
        )
        retrieved_at = self._clock()
        expires_at = retrieved_at + timedelta(
            hours=Settings.METALCHARTS_CACHE_TTL_HOURS
        )
        fetched = inserted = updated = skipped = 0
        for binding in bindings:
            weight = WEIGHT_HISTORY
            bars = self._fetch_history_paced(
                budget, weight, binding, date_from, date_to
            )
            budget.record(
                endpoint="history",
                params_key=params_hash(
                    binding.source_series_key,
                    date_from.isoformat(),
                    date_to.isoformat(),
                    "1d",
                ),
                weight=weight,
                http_status=200,
                correlation_id=correlation_id,
            )
            fetched += len(bars)
            for bar in bars:
                if not (
                    date_from <= bar["observation_date"] <= date_to
                ):
                    skipped += 1
                    continue
                outcome = self._repo.upsert_metal_cache(
                    instrument_id=binding.instrument_id,
                    source_id=source_id,
                    observation_date=bar["observation_date"],
                    native_price=bar["close"],
                    native_currency=binding.native_currency,
                    unit_code=binding.unit_code or "unknown",
                    quote_basis=binding.quotation_basis,
                    source_record_key=(
                        f"metalcharts:{binding.source_series_key}:"
                        f"{bar['observation_date'].isoformat()}"
                    ),
                    retrieved_at=retrieved_at,
                    expires_at=expires_at,
                    quality_status=QUALITY_VALIDATED,
                )
                if outcome == "inserted":
                    inserted += 1
                elif outcome == "updated":
                    updated += 1
                else:
                    skipped += 1
        self._repo.purge_expired_cache()
        return fetched, inserted, updated, skipped

    def _quote_source(self, feed: str) -> Any:
        """Rights gate for MetalCharts quote feeds — the destination
        table follows ``source.observation_retention``: 'permanent'
        requires ``collect`` + ``store``; anything else stays on the
        TTL-cache gate (``collect`` + ``store_cache_only``). A source
        without the permanent ``store`` grant can never reach the
        permanent observation table through this path."""
        source_id = provider_id_for_feed(feed)
        source = self._repo.get_source(source_id)
        if source is None or not source.active:
            raise SourceNotLicensedError(
                f"source {source_id} is not active/licensed in the catalog"
            )
        if getattr(source, "observation_retention", None) == (
            RETENTION_PERMANENT
        ):
            required = (usage_policy.OP_COLLECT, usage_policy.OP_STORE)
        else:
            required = (
                usage_policy.OP_COLLECT,
                usage_policy.OP_STORE_CACHE_ONLY,
            )
        if not usage_policy.allows_all(
            source.allowed_use_scope, required
        ):
            raise SourceNotLicensedError(
                f"source {source_id} lacks approved "
                f"{'/'.join(required)} use"
            )
        return source

    @staticmethod
    def _parse_provider_timestamp(raw: Any) -> datetime | None:
        """Normalize a MetalCharts ``timestamp`` field to an aware UTC
        datetime — ISO-8601 or epoch seconds; anything else is ``None``
        (the row is then skipped, never dated by the run clock)."""
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            try:
                return datetime.fromtimestamp(raw, tz=timezone.utc)
            except (OverflowError, OSError, ValueError):
                return None
        if isinstance(raw, str):
            try:
                parsed = datetime.fromisoformat(
                    raw.strip().replace("Z", "+00:00")
                )
            except ValueError:
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        return None

    def _ingest_metals_prices_daily(self, correlation_id: str):
        """MetalCharts /v1/prices last-quote refresh (PROC-0076 R11).

        A single call (weight 1) returns every bound symbol — five
        verified bindings cost ~31 weight/month, inside the budget.
        Rows keep the provider ``timestamp`` as ``observation_date``
        (UTC) and an honest ``*_last`` quote basis — an intraday "last"
        never overwrites a daily close (repository precedence guard)."""
        source_id = PROVIDER_METALCHARTS
        source = self._quote_source(FEED_METALS_PRICES_DAILY)
        if self._metalcharts_provider is None or not getattr(
            self._metalcharts_provider, "configured", lambda: True
        )():
            raise SourceNotLicensedError(
                "metalcharts provider is not configured (no api key)"
            )
        bindings = [
            b
            for b in self._repo.list_instrument_sources(
                source_id=source_id, active_only=True
            )
            if b.source_series_key
        ]
        if not bindings:
            raise NoApprovedSeriesError(
                "no active metalcharts bindings with verified symbols"
            )
        budget = self._metalcharts_budget or MetalChartsBudget(
            repository=self._repo, clock=self._clock
        )
        retrieved_at = self._clock()
        budget.acquire(weight=WEIGHT_SPOT)
        payload = self._metalcharts_provider.fetch_spot()
        budget.record(
            endpoint="prices",
            params_key="prices:all",
            weight=WEIGHT_SPOT,
            http_status=200,
            correlation_id=correlation_id,
        )
        permanent = (
            getattr(source, "observation_retention", None)
            == RETENTION_PERMANENT
        )
        expires_at = retrieved_at + timedelta(
            hours=Settings.METALCHARTS_CACHE_TTL_HOURS
        )
        fetched = inserted = updated = skipped = 0
        for binding in bindings:
            symbol = binding.source_series_key
            entry = payload.get(symbol)
            fetched += 1
            if not isinstance(entry, dict):
                skipped += 1
                continue
            price = entry.get("price")
            if price is None:
                skipped += 1
                continue
            timestamp = self._parse_provider_timestamp(
                entry.get("timestamp")
            )
            if timestamp is None or entry.get("stale"):
                # No trustworthy provider reference date — a missing or
                # stale tick must not fabricate today's bar.
                skipped += 1
                continue
            quote_basis = spot_last_quote_basis(
                entry.get("exchange"), entry.get("market_type")
            )
            record_key = (
                f"{source_id}:prices:{symbol}:"
                f"{timestamp.date().isoformat()}"
            )
            if permanent:
                outcome = self._repo.upsert_metal_observation(
                    instrument_id=binding.instrument_id,
                    observation_date=timestamp.date(),
                    native_price=price,
                    native_currency=binding.native_currency,
                    unit_code=binding.unit_code or "unknown",
                    quote_basis=quote_basis,
                    source_id=source_id,
                    source_record_key=record_key,
                    retrieved_at=retrieved_at,
                    observation_timestamp=timestamp,
                )
            else:
                outcome = self._repo.upsert_metal_cache(
                    instrument_id=binding.instrument_id,
                    source_id=source_id,
                    observation_date=timestamp.date(),
                    native_price=price,
                    native_currency=binding.native_currency,
                    unit_code=binding.unit_code or "unknown",
                    quote_basis=quote_basis,
                    source_record_key=record_key,
                    retrieved_at=retrieved_at,
                    expires_at=expires_at,
                    quality_status=QUALITY_VALIDATED,
                    observation_timestamp=timestamp,
                )
            if outcome == "inserted":
                inserted += 1
            elif outcome == "updated":
                updated += 1
            else:
                skipped += 1
        if not permanent:
            self._repo.purge_expired_cache()
        return fetched, inserted, updated, skipped

    def _fetch_history_paced(
        self,
        budget: Any,
        weight: int,
        binding: Any,
        date_from: date,
        date_to: date,
    ) -> list[dict[str, Any]]:
        """Acquire budget then fetch, pacing the job to the per-minute
        window instead of failing.

        A scheduled job can afford to wait for the next minute bucket —
        five verified bindings need 10 weight, above the deliberate
        8/min headroom budget — and an upstream 429 is retried once
        after ``Retry-After``. The monthly budget and repeated 429s
        still fail fast."""
        for attempt in range(3):
            try:
                budget.acquire(weight=weight)
                return self._metalcharts_provider.fetch_history(
                    binding.source_series_key, date_from, date_to
                )
            except RateLimitedError as exc:
                if "monthly" in str(exc) or attempt == 2:
                    raise
                wait = min(exc.retry_after or 60, 65)
                logger.info(
                    "ingestion_minute_pacing feed=metals-daily wait_s=%s",
                    wait,
                )
                time.sleep(wait)
        raise RateLimitedError("metalcharts pacing exhausted")

    def _ingest_fx(self, date_from: date, date_to: date):
        source_id = PROVIDER_BCB_PTAX
        self._check_source(source_id)
        rows = self._fx_provider.fetch_period(date_from, date_to)
        retrieved_at = self._clock()
        observations = self._fx_provider.to_observations(
            rows, source_id=source_id, retrieved_at=retrieved_at
        )
        inserted = updated = skipped = 0
        for obs in observations:
            outcome = self._repo.upsert_fx_observation(
                pair_code=obs["pair_code"],
                rate_kind=obs["rate_kind"],
                reference_date=obs["reference_date"],
                value=obs["value"],
                source_id=source_id,
                source_record_key=obs.get("source_record_key"),
                retrieved_at=retrieved_at,
            )
            if outcome == "inserted":
                inserted += 1
            elif outcome == "updated":
                updated += 1
            else:
                skipped += 1
        return len(rows), inserted, updated, skipped

    def _ingest_comex(self, date_from: date, date_to: date):
        source_id = PROVIDER_MDIC_COMEX
        self._check_source(source_id)
        approved = frozenset(
            row["ncm_code"]
            for row in self._repo.list_ncm_allowlist()
            if row["active"]
        )
        if not approved:
            # The NCM→product mapping is business-homologated — an empty
            # allowlist blocks the feed rather than widening scope.
            raise NoApprovedSeriesError(
                "no approved NCM in the Comex allowlist"
            )
        ncm_meta = {
            row["ncm_code"]: row for row in self._repo.list_ncm_allowlist()
        }
        years = sorted({date_from.year, date_to.year})
        retrieved_at = self._clock()
        fetched = inserted = updated = skipped = 0
        for year in range(years[0], years[-1] + 1):
            result = self._comex_provider.fetch_year(
                year, approved_ncm_codes=approved
            )
            fetched += len(result.aggregates)
            for agg in result.aggregates:
                if not (date_from <= agg.reference_month <= date_to):
                    skipped += 1
                    continue
                outcome = self._repo.upsert_comex_observation(
                    reference_month=agg.reference_month,
                    ncm_code=agg.ncm_code,
                    ncm_version=ncm_meta[agg.ncm_code]["ncm_version"],
                    country_code=agg.country_code,
                    state_code=agg.state_code,
                    fob_usd_total=agg.fob_usd_total,
                    net_weight_kg_total=agg.net_weight_kg_total,
                    unit_value_usd_per_t=agg.unit_value_usd_per_t,
                    contributing_rows=agg.contributing_rows,
                    quality_status=agg.quality_status,
                    dataset_year=result.dataset_year,
                    dataset_revision=None,
                    source_checksum=result.source_checksum,
                    source_id=source_id,
                    retrieved_at=retrieved_at,
                )
                if outcome == "inserted":
                    inserted += 1
                elif outcome == "updated":
                    updated += 1
                else:
                    skipped += 1
        return fetched, inserted, updated, skipped

    def _ingest_ipp(self, date_from: date, date_to: date):
        source_id = PROVIDER_IBGE_IPP
        self._check_source(source_id)
        series_list = [
            s for s in self._repo.list_producer_price_series() if s["active"]
        ]
        if not series_list:
            raise NoApprovedSeriesError(
                "no active producer price series in the catalog"
            )
        retrieved_at = self._clock()
        fetched = inserted = updated = skipped = 0
        for series in series_list:
            rows = self._ipp_provider.fetch_series(
                table_code=series["table_code"],
                classification_code=series["classification_code"],
                variable_code=series["variable_code"],
                activity_code=series["activity_code"],
                month_from=date_from,
                month_to=date_to,
            )
            fetched += len(rows)
            for row in rows:
                if not (date_from <= row["reference_month"] <= date_to):
                    skipped += 1
                    continue
                outcome = self._repo.upsert_producer_price_observation(
                    series_id=series["series_id"],
                    reference_month=row["reference_month"],
                    value=row["value"],
                    source_id=source_id,
                    source_record_key=row.get("source_record_key"),
                    published_at=None,
                    retrieved_at=retrieved_at,
                )
                if outcome == "inserted":
                    inserted += 1
                elif outcome == "updated":
                    updated += 1
                else:
                    skipped += 1
        return fetched, inserted, updated, skipped


def storage_ready() -> None:
    if not Settings.plugins_db_configured():
        raise StorageUnavailableError("plugins database is not configured")
