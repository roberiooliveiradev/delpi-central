"""Market data domain model (PROC-0076).

Owns the canonical entities for externally sourced market quotations:
licensed sources, metal instruments, normalized observations, FX rates
and ingestion run bookkeeping. Values are monetary — ``Decimal`` only,
never float. ``None`` means "no data" and is never coerced to zero.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

# --- Feed / catalog identifiers ---------------------------------------------

FEED_FX_DAILY = "fx-daily"
FEED_METALS_MONTHLY = "metals-monthly"
FEED_COMEX_MONTHLY = "comex-import-monthly"
FEED_IPP_MONTHLY = "ipp-monthly"
SUPPORTED_FEEDS = (
    FEED_FX_DAILY,
    FEED_METALS_MONTHLY,
    FEED_COMEX_MONTHLY,
    FEED_IPP_MONTHLY,
)

KIND_METAL = "metal"
KIND_FX = "fx"
KIND_COMEX = "comex"
KIND_IPP = "producer_price"

PAIR_USD_BRL = "USD/BRL"

RATE_KIND_PTAX_CLOSING_SELL = "ptax_closing_sell"
RATE_KIND_PTAX_CLOSING_BUY = "ptax_closing_buy"
SUPPORTED_RATE_KINDS = (RATE_KIND_PTAX_CLOSING_SELL, RATE_KIND_PTAX_CLOSING_BUY)

QUALITY_VALIDATED = "validated"
QUALITY_ESTIMATED = "estimated"

GRANULARITY_MONTH = "month"
GRANULARITY_YEAR = "year"
GRANULARITY_DAY = "day"

# Provider ids — source rights are recorded in the catalog rows seeded by
# migration; the job refuses to ingest from a source that is not active
# and licensed in the database.
PROVIDER_BCB_PTAX = "bcb-ptax"
PROVIDER_WORLDBANK_PINK_SHEET = "world-bank-pink-sheet"
PROVIDER_MDIC_COMEX = "mdic-comex-stat"
PROVIDER_IBGE_IPP = "ibge-ipp-sidra"

SCHEMA_VERSION = "v1"


@dataclass(frozen=True)
class MarketDataSource:
    source_id: str
    provider_id: str
    source_kind: str
    attribution: str
    license_reference: str
    license_reviewed_at: date | None
    allowed_use_scope: str
    active: bool


@dataclass(frozen=True)
class MetalInstrument:
    instrument_id: int
    instrument_code: str
    metal_code: str
    label: str
    market: str
    quotation_basis: str
    native_currency: str
    unit_code: str
    unit_label: str
    source_id: str
    source_series_key: str
    granularity: str
    active: bool


@dataclass(frozen=True)
class MetalObservation:
    instrument_code: str
    observation_date: date
    price: Decimal
    currency: str
    unit_code: str
    quote_basis: str
    quality: str
    source_id: str
    retrieved_at: datetime


@dataclass(frozen=True)
class FxObservation:
    pair_code: str
    rate_kind: str
    reference_date: date
    value: Decimal
    source_id: str
    retrieved_at: datetime


@dataclass(frozen=True)
class IngestionRun:
    run_id: str
    provider_id: str
    feed: str
    started_at: datetime
    finished_at: datetime | None
    outcome: str
    fetched_count: int
    inserted_count: int
    updated_count: int
    skipped_count: int
    safe_error_code: str | None
    correlation_id: str | None
    version: str


@dataclass(frozen=True)
class FeedStatus:
    feed: str
    source_id: str | None
    active: bool
    last_run_started_at: datetime | None
    last_run_finished_at: datetime | None
    last_successful_at: datetime | None
    last_outcome: str | None
    last_error_code: str | None
    latest_observation_date: date | None
    observation_count: int
