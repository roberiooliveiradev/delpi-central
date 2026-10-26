"""Market data read use cases (PROC-0076).

Serve only persisted, validated history — a request never triggers
external collection. Validation happens here (dates, ranges, cursors,
catalog membership); the repository only runs the parameterized SQL.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from app.application.contracts import (
    InvalidQueryError,
    StorageUnavailableError,
    UnknownInstrumentError,
    UnknownSeriesError,
    UseNotApprovedError,
)
from app.domain.market_data import (
    KIND_FX,
    KIND_METAL,
    PAIR_USD_BRL,
    PROVIDER_IBGE_IPP,
    PROVIDER_MDIC_COMEX,
    SCHEMA_VERSION,
    SUPPORTED_RATE_KINDS,
)
from app.domain import usage_policy
from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.market_contract_readiness import (
    check_market_contract_ready,
)
from app.infrastructure.persistence.market_data_repository import (
    MarketDataRepository,
    decode_cursor,
    rows_to_page,
)
from app.infrastructure.persistence.plugins_db import get_connection

DEFAULT_LIMIT = 100
MAX_LIMIT = 500
# Window bounds are granularity-aware: monthly series span far fewer rows
# per year than daily FX. Historical reads beyond the cap paginate.
MAX_RANGE_DAYS_MONTHLY = 3660
MAX_RANGE_DAYS_DAILY = 366


def _parse_iso_date(raw: str | None, field: str) -> date:
    text = (raw or "").strip()
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise InvalidQueryError(f"{field} must be an ISO date (YYYY-MM-DD)") from exc


def _parse_limit(raw: str | None) -> int:
    if raw is None or not str(raw).strip():
        return DEFAULT_LIMIT
    try:
        value = int(str(raw).strip())
    except ValueError as exc:
        raise InvalidQueryError("limit must be an integer") from exc
    if value < 1 or value > MAX_LIMIT:
        raise InvalidQueryError(f"limit must be between 1 and {MAX_LIMIT}")
    return value


def _parse_cursor(raw: str | None) -> tuple[date, int] | None:
    if raw is None or not str(raw).strip():
        return None
    try:
        return decode_cursor(str(raw).strip())
    except Exception as exc:
        raise InvalidQueryError("cursor is malformed") from exc


def _validate_range(date_from: date, date_to: date, *, max_days: int) -> None:
    if date_from > date_to:
        raise InvalidQueryError("date_from must be <= date_to")
    if (date_to - date_from).days > max_days:
        raise InvalidQueryError(
            f"date range exceeds the maximum window of {max_days} days"
        )


def _repo(conn) -> MarketDataRepository:
    return MarketDataRepository(conn, schema=Settings.EXTERNAL_DATA_SCHEMA)


def _require_storage():
    if not Settings.plugins_db_configured():
        raise StorageUnavailableError("market data storage is not configured")


def _source_dto(source) -> dict[str, Any]:
    return {
        "source_id": source.source_id,
        "provider_id": source.provider_id,
        "attribution": source.attribution,
        "license_reference": source.license_reference,
        "license_reviewed_at": (
            source.license_reviewed_at.isoformat()
            if source.license_reviewed_at
            else None
        ),
        "allowed_use_scope": source.allowed_use_scope,
    }


def _display_allowed(source) -> bool:
    """Fail-closed: only an explicit ``internal_display`` grant serves
    prices to consumers; pending/unknown scopes are denied."""
    return bool(source) and usage_policy.allows(
        source.allowed_use_scope, usage_policy.OP_INTERNAL_DISPLAY
    )


def _require_display(source, *, what: str) -> None:
    if not _display_allowed(source):
        raise UseNotApprovedError(
            f"source has no approved internal_display use for {what}"
        )


def _instrument_dto(inst, sources: dict[str, Any]) -> dict[str, Any]:
    source = sources.get(inst.source_id)
    return {
        "instrument_code": inst.instrument_code,
        "kind": KIND_METAL,
        "metal_code": inst.metal_code,
        "label": inst.label,
        "market": inst.market,
        "quote_basis": inst.quotation_basis,
        "currency": inst.native_currency,
        "unit_code": inst.unit_code,
        "unit": inst.unit_label,
        "granularity": inst.granularity,
        "source_id": inst.source_id,
        "active": inst.active,
        "display_allowed": _display_allowed(source),
    }


def get_catalog() -> dict[str, Any]:
    """operationId: listMarketDataCatalogV1."""
    _require_storage()
    with get_connection() as conn:
        check_market_contract_ready(conn)
        repo = _repo(conn)
        sources = {s.source_id: s for s in repo.list_sources()}
        instruments = repo.list_instruments()
        latest = repo.latest_observation_dates()
        # R2 catalog segments tolerate a pre-V005 database — absent
        # tables mean "no series", never a hard failure.
        ncm_rows = _optional_rows(repo, "list_ncm_allowlist")
        ipp_rows = _optional_rows(repo, "list_producer_price_series")

    return {
        "instruments": [
            {**_instrument_dto(i, sources), "latest_observation_date": _iso(latest.get(i.instrument_code))}
            for i in instruments
        ],
        "fx_series": [
            {
                "instrument_code": "usd-brl",
                "kind": KIND_FX,
                "label": "Dólar / Real",
                "pair": PAIR_USD_BRL,
                "rate_kinds": list(SUPPORTED_RATE_KINDS),
                "currency": "BRL",
                "unit": "BRL per USD",
                "granularity": "day",
                "source_id": "bcb-ptax",
                "display_allowed": _display_allowed(sources.get("bcb-ptax")),
                "latest_observation_date": _iso(
                    latest.get(f"{PAIR_USD_BRL}|ptax_closing_sell")
                ),
            }
        ],
        "import_ncms": [
            {
                "ncm_code": n["ncm_code"],
                "kind": "comex_import",
                "description": n["description"],
                "family_code": n["family_code"],
                "ncm_version": n["ncm_version"],
                "unit": "USD/metric ton",
                "granularity": "month",
                "source_id": PROVIDER_MDIC_COMEX,
                "active": n["active"],
                "display_allowed": _display_allowed(
                    sources.get(PROVIDER_MDIC_COMEX)
                ),
                "latest_observation_date": _iso(
                    latest.get(f"comex|{n['ncm_code']}")
                ),
            }
            for n in ncm_rows
        ],
        "producer_price_series": [
            {
                "series_id": s["series_id"],
                "kind": "producer_price",
                "label": f"{s['activity_label']} — {s['variable_label']}",
                "activity_code": s["activity_code"],
                "activity_label": s["activity_label"],
                "variable_code": s["variable_code"],
                "variable_label": s["variable_label"],
                "table_code": s["table_code"],
                "metric_kind": s["metric_kind"],
                "unit": s["unit_label"],
                "base_reference": s["base_reference"],
                "granularity": "month",
                "source_id": s["source_id"],
                "active": s["active"],
                "display_allowed": _display_allowed(
                    sources.get(s["source_id"])
                ),
                "latest_observation_date": _iso(
                    latest.get(f"ipp|{s['series_id']}")
                ),
            }
            for s in ipp_rows
        ],
        "sources": [_source_dto(s) for s in sources.values()],
        "meta": {"schema_version": SCHEMA_VERSION},
    }


def _optional_rows(repo, method: str):
    try:
        return getattr(repo, method)()
    except Exception:
        return []


def list_metal_observations(
    *,
    instrument_code: str,
    date_from_raw: str | None,
    date_to_raw: str | None,
    limit_raw: str | None,
    cursor_raw: str | None,
) -> dict[str, Any]:
    """operationId: listMetalObservationsV1."""
    _require_storage()
    code = (instrument_code or "").strip()
    if not code:
        raise InvalidQueryError("instrument_code is required")
    date_from = _parse_iso_date(date_from_raw, "date_from")
    date_to = _parse_iso_date(date_to_raw, "date_to")
    _validate_range(date_from, date_to, max_days=MAX_RANGE_DAYS_MONTHLY)
    limit = _parse_limit(limit_raw)
    cursor = _parse_cursor(cursor_raw)

    with get_connection() as conn:
        check_market_contract_ready(conn)
        repo = _repo(conn)
        instrument = repo.get_instrument(code)
        if instrument is None or not instrument.active:
            raise UnknownInstrumentError(
                f"unknown market instrument: {code}"
            )
        source = repo.get_source(instrument.source_id)
        _require_display(source, what=code)
        rows = repo.list_metal_observations(
            instrument_id=instrument.instrument_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            cursor=cursor,
        )

    items, next_cursor = rows_to_page(
        rows, limit=limit, date_key="observation_date", id_key="observation_id"
    )
    return {
        "instrument": _instrument_dto(instrument, {}),
        "items": [_metal_observation_dto(r, instrument, source) for r in items],
        "page_info": {
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
        },
        "meta": {
            "as_of": None,
            "data_status": "ok" if items else "no_data",
            "source_ids": [instrument.source_id],
            "schema_version": SCHEMA_VERSION,
        },
    }


def list_fx_observations(
    *,
    pair: str,
    rate_kind: str,
    date_from_raw: str | None,
    date_to_raw: str | None,
    limit_raw: str | None,
    cursor_raw: str | None,
) -> dict[str, Any]:
    """operationId: listFxObservationsV1."""
    _require_storage()
    pair_code = (pair or "").strip()
    kind = (rate_kind or "").strip()
    if not pair_code or not kind:
        raise InvalidQueryError("pair and rate_kind are required")
    if pair_code != PAIR_USD_BRL or kind not in SUPPORTED_RATE_KINDS:
        raise UnknownSeriesError(
            f"unknown fx series: {pair_code} {kind}"
        )
    date_from = _parse_iso_date(date_from_raw, "date_from")
    date_to = _parse_iso_date(date_to_raw, "date_to")
    _validate_range(date_from, date_to, max_days=MAX_RANGE_DAYS_DAILY)
    limit = _parse_limit(limit_raw)
    cursor = _parse_cursor(cursor_raw)

    with get_connection() as conn:
        check_market_contract_ready(conn)
        repo = _repo(conn)
        source = repo.get_source("bcb-ptax")
        _require_display(source, what=pair_code)
        rows = repo.list_fx_observations(
            pair_code=pair_code,
            rate_kind=kind,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            cursor=cursor,
        )

    items, next_cursor = rows_to_page(
        rows, limit=limit, date_key="reference_date", id_key="fx_id"
    )
    return {
        "series": {
            "pair": pair_code,
            "rate_kind": kind,
            "currency": "BRL",
            "unit": "BRL per USD",
            "granularity": "day",
        },
        "items": [_fx_observation_dto(r, source) for r in items],
        "page_info": {
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
        },
        "meta": {
            "as_of": None,
            "data_status": "ok" if items else "no_data",
            "source_ids": ["bcb-ptax"],
            "schema_version": SCHEMA_VERSION,
        },
    }


def get_ingestion_status() -> dict[str, Any]:
    """operationId: getMarketDataIngestionStatusV1."""
    _require_storage()
    with get_connection() as conn:
        check_market_contract_ready(conn)
        repo = _repo(conn)
        feeds = repo.feed_statuses()
        sources = {s.source_id: s for s in repo.list_sources()}

    feed_source = {
        "metals-monthly": "world-bank-pink-sheet",
        "fx-daily": "bcb-ptax",
        "comex-import-monthly": PROVIDER_MDIC_COMEX,
        "ipp-monthly": PROVIDER_IBGE_IPP,
    }
    return {
        "feeds": [
            {
                **feed,
                "source_id": feed_source.get(feed["feed"]),
                "source_active": (
                    sources[feed_source[feed["feed"]]].active
                    if feed_source.get(feed["feed"]) in sources
                    else None
                ),
                "source_allowed_use_scope": (
                    sources[feed_source[feed["feed"]]].allowed_use_scope
                    if feed_source.get(feed["feed"]) in sources
                    else None
                ),
                "last_run_started_at": _iso(feed["last_run_started_at"]),
                "last_run_finished_at": _iso(feed["last_run_finished_at"]),
                "last_successful_at": _iso(feed["last_successful_at"]),
                "latest_observation_date": _iso(
                    feed["latest_observation_date"]
                ),
            }
            for feed in feeds
        ],
        "meta": {"schema_version": SCHEMA_VERSION},
    }


def list_comex_imports(
    *,
    ncm_code: str,
    date_from_raw: str | None,
    date_to_raw: str | None,
    country_code: str | None,
    state_code: str | None,
    limit_raw: str | None,
    cursor_raw: str | None,
) -> dict[str, Any]:
    """operationId: listComexImportObservationsV1.

    Only catalog-allowlisted NCMs are queryable — an unapproved NCM is an
    unknown series, not an empty result that could masquerade as data.
    """
    _require_storage()
    code = (ncm_code or "").strip()
    if not code:
        raise InvalidQueryError("ncm_code is required")
    date_from = _parse_iso_date(date_from_raw, "date_from")
    date_to = _parse_iso_date(date_to_raw, "date_to")
    _validate_range(date_from, date_to, max_days=MAX_RANGE_DAYS_MONTHLY)
    limit = _parse_limit(limit_raw)
    cursor = _parse_cursor(cursor_raw)

    with get_connection() as conn:
        check_market_contract_ready(conn)
        repo = _repo(conn)
        ncm = repo.get_ncm_allowlist(code)
        if ncm is None or not ncm["active"]:
            raise UnknownSeriesError(f"unknown import series: {code}")
        source = repo.get_source(PROVIDER_MDIC_COMEX)
        _require_display(source, what=code)
        rows = repo.list_comex_observations(
            ncm_code=code,
            date_from=date_from,
            date_to=date_to,
            country_code=(country_code or "").strip() or None,
            state_code=(state_code or "").strip() or None,
            limit=limit,
            cursor=cursor,
        )

    items, next_cursor = rows_to_page(
        rows, limit=limit, date_key="reference_month", id_key="observation_id"
    )
    return {
        "series": {
            "ncm_code": code,
            "ncm_version": ncm["ncm_version"],
            "description": ncm["description"],
            "metric_kind": "comex_import",
            "unit": "USD/metric ton",
            "granularity": "month",
        },
        "items": [_comex_observation_dto(r, source) for r in items],
        "page_info": {
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
        },
        "meta": {
            "data_status": "ok" if items else "no_data",
            "source_ids": [PROVIDER_MDIC_COMEX],
            "schema_version": SCHEMA_VERSION,
        },
    }


def list_producer_price_observations(
    *,
    series_id: str,
    date_from_raw: str | None,
    date_to_raw: str | None,
    limit_raw: str | None,
    cursor_raw: str | None,
) -> dict[str, Any]:
    """operationId: listProducerPriceIndexObservationsV1."""
    _require_storage()
    sid = (series_id or "").strip()
    if not sid:
        raise InvalidQueryError("series_id is required")
    date_from = _parse_iso_date(date_from_raw, "date_from")
    date_to = _parse_iso_date(date_to_raw, "date_to")
    _validate_range(date_from, date_to, max_days=MAX_RANGE_DAYS_MONTHLY)
    limit = _parse_limit(limit_raw)
    cursor = _parse_cursor(cursor_raw)

    with get_connection() as conn:
        check_market_contract_ready(conn)
        repo = _repo(conn)
        series = repo.get_producer_price_series(sid)
        if series is None or not series["active"]:
            raise UnknownSeriesError(f"unknown producer price series: {sid}")
        source = repo.get_source(series["source_id"])
        _require_display(source, what=sid)
        rows = repo.list_producer_price_observations(
            series_id=sid,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            cursor=cursor,
        )

    items, next_cursor = rows_to_page(
        rows, limit=limit, date_key="reference_month", id_key="observation_id"
    )
    return {
        "series": {
            "series_id": sid,
            "metric_kind": series["metric_kind"],
            "activity_code": series["activity_code"],
            "activity_label": series["activity_label"],
            "variable_code": series["variable_code"],
            "variable_label": series["variable_label"],
            "table_code": series["table_code"],
            "unit": series["unit_label"],
            "base_reference": series["base_reference"],
            "granularity": "month",
        },
        "items": [_ipp_observation_dto(r, source) for r in items],
        "page_info": {
            "next_cursor": next_cursor,
            "has_more": next_cursor is not None,
        },
        "meta": {
            "data_status": "ok" if items else "no_data",
            "source_ids": [series["source_id"]],
            "schema_version": SCHEMA_VERSION,
        },
    }


def _comex_observation_dto(row, source) -> dict[str, Any]:
    return {
        "ncm_code": row["ncm_code"],
        "ncm_version": row["ncm_version"],
        "reference_month": row["reference_month"].isoformat(),
        "dimensions": {
            "country_code": row["country_code"],
            "state_code": row["state_code"],
        },
        "fob_usd_total": str(row["fob_usd_total"]),
        "net_weight_kg_total": str(row["net_weight_kg_total"]),
        "unit_value_usd_per_t": (
            str(row["unit_value_usd_per_t"])
            if row["unit_value_usd_per_t"] is not None
            else None
        ),
        "unit": "USD/metric ton",
        "contributing_rows": row["contributing_rows"],
        "quality": row["quality_status"],
        "dataset_year": row["dataset_year"],
        "dataset_revision": row["dataset_revision"],
        "source": {
            "source_id": row["source_id"],
            "provider_id": source.provider_id if source else None,
            "attribution": source.attribution if source else None,
            "retrieved_at": _iso(row["retrieved_at"]),
            "license_reference": (
                source.license_reference if source else None
            ),
            "schema_version": SCHEMA_VERSION,
        },
    }


def _ipp_observation_dto(row, source) -> dict[str, Any]:
    return {
        "series_id": row["series_id"],
        "reference_month": row["reference_month"].isoformat(),
        "value": str(row["value"]),
        "quality": row["quality_status"],
        "source": {
            "source_id": row["source_id"],
            "provider_id": source.provider_id if source else None,
            "attribution": source.attribution if source else None,
            "retrieved_at": _iso(row["retrieved_at"]),
            "published_at": _iso(row["published_at"]),
            "license_reference": (
                source.license_reference if source else None
            ),
            "schema_version": SCHEMA_VERSION,
        },
    }


def _metal_observation_dto(row, instrument, source) -> dict[str, Any]:
    return {
        "instrument_code": instrument.instrument_code,
        "observation_date": row["observation_date"].isoformat(),
        "price": str(row["native_price"]),
        "currency": row["native_currency"],
        "unit": instrument.unit_label,
        "quote_basis": row["quote_basis"],
        "quality": row["quality_status"],
        "source": {
            "source_id": row["source_id"],
            "provider_id": source.provider_id if source else None,
            "attribution": source.attribution if source else None,
            "retrieved_at": _iso(row["retrieved_at"]),
            "reference_date": row["observation_date"].isoformat(),
            "license_reference": (
                source.license_reference if source else None
            ),
            "schema_version": SCHEMA_VERSION,
        },
    }


def _fx_observation_dto(row, source) -> dict[str, Any]:
    return {
        "pair": row["pair_code"],
        "rate_kind": row["rate_kind"],
        "reference_date": row["reference_date"].isoformat(),
        "value": str(row["value"]),
        "quality": row["quality_status"],
        "source": {
            "source_id": row["source_id"],
            "provider_id": source.provider_id if source else None,
            "attribution": source.attribution if source else None,
            "retrieved_at": _iso(row["retrieved_at"]),
            "license_reference": (
                source.license_reference if source else None
            ),
            "schema_version": SCHEMA_VERSION,
        },
    }


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None
