"""Market intelligence BFF composition (PROC-0076).

Owns the supplies-side semantics: catalog-driven instrument validation,
USD→BRL conversion against homologated FX, period aggregation and
coverage/freshness flags. All math is ``Decimal``; ``None`` means "no
data" and is never coerced to zero. The controller stays a thin HTTP
shell — every rule lives here.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Iterable

from app.infrastructure.gateways.market_data_gateway import MarketDataGateway

# Versioned method identifiers — a policy change is a version bump, never
# a silent semantic change.
FX_CONVERSION_METHOD = "metal_monthly_avg_x_ptax_monthly_avg/v1"
PERIOD_AVERAGE_METHOD = "mean_of_valid_observations/v1"
PERIOD_VARIATION_METHOD = "first_to_last/v1"
COVERAGE_METHOD = "coverage_vs_expected/v1"
SCHEMA_VERSION = "v1"

CURRENCIES = ("USD", "BRL")
FX_DEFAULT_KIND = "ptax_closing_sell"
FX_KINDS = ("ptax_closing_sell", "ptax_closing_buy")
FX_INSTRUMENT_CODE = "usd-brl"
FX_PAIR = "USD/BRL"

KIND_METAL = "metal"
KIND_FX = "fx"
KIND_IMPORT = "comex_import"
KIND_IPP = "producer_price"

METAL_GRANULARITIES = ("month", "year")
# ``week`` is a derived ISO-week bucket of *daily* series only — a
# monthly series can never produce weekly/daily observations.
FX_GRANULARITIES = ("day", "week", "month", "year")
IMPORT_GRANULARITIES = ("month", "year")
IPP_GRANULARITIES = ("month", "year")
ALL_GRANULARITIES = ("day", "week", "month", "year")

# R2 feeds — must mirror ``app.domain.market_data`` on the producer.
COMEX_FEED = "comex-import-monthly"
IPP_FEED = "ipp-monthly"

# Methodology identifiers for the new metric kinds.
IMPORT_UNIT_VALUE_METHOD = "sum_fob_usd_x_1000_div_sum_net_weight_kg/v1"
IMPORT_TOTALS_METHOD = "sum_of_valid_monthly_buckets/v1"
MIN_MAX_METHOD = "extremes_of_valid_observations/v1"
WEEK_BUCKET_METHOD = "mean_of_valid_daily_observations_per_iso_week/v1"
COMPARE_ALIGNMENT_METHOD = "period_outer_join_same_unit/v1"
# Maximum missing periods reported in a summary — informative, capped.
MAX_MISSING_PERIODS = 24

MAX_RANGE_DAYS = 3660
DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 120
MAX_QUOTE_INSTRUMENTS = 8

# Freshness policy — measured against the provider's real publication
# cadence on the *latest available* observation, never on the queried
# window: a complete historical period is "ok", not "stale".
# - Pink Sheet publishes monthly, a few days after month end (~5th).
# - PTAX publishes each business day; weekends and holidays have no
#   bulletin, so a multi-day grace is normal, not a failure.
FRESHNESS_METHOD = "provider_publication_cadence/v1"
PINK_SHEET_PUBLICATION_DAY = 5
# MDIC publishes consolidated monthly imports around mid-month; IBGE
# publishes the IPP of month M at the end of month M+1.
COMEX_PUBLICATION_DAY = 15
IPP_PUBLICATION_DAY = 30
FX_STALE_GRACE_DAYS = 4

_FEED_BY_KIND = {
    KIND_METAL: "metals-monthly",
    KIND_FX: "fx-daily",
    KIND_IMPORT: COMEX_FEED,
    KIND_IPP: IPP_FEED,
}

_PUBLICATION_DAY_BY_KIND = {
    KIND_METAL: PINK_SHEET_PUBLICATION_DAY,
    KIND_IMPORT: COMEX_PUBLICATION_DAY,
    KIND_IPP: IPP_PUBLICATION_DAY,
}


class MarketDataNotFoundError(LookupError):
    """Instrument/filter refers to something outside the catalog."""


@dataclass(frozen=True)
class Observation:
    period: date
    value: Decimal
    quality: str
    source_id: str | None


def _month_add(d: date, months: int) -> date:
    month_index = d.year * 12 + (d.month - 1) + months
    return date(month_index // 12, month_index % 12 + 1, 1)


def _month_range(start: date, end: date) -> list[date]:
    first = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    months = []
    current = first
    while current <= last:
        months.append(current)
        current = _month_add(current, 1)
    return months


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _week_key(d: date) -> str:
    iso = d.isocalendar()
    return f"{iso.year:04d}-W{iso.week:02d}"


def _week_range(start: date, end: date) -> list[str]:
    """Distinct ISO weeks touched by the range (Monday-anchored)."""
    seen: list[str] = []
    current = start
    while current <= end:
        key = _week_key(current)
        if not seen or seen[-1] != key:
            seen.append(key)
        current = date.fromordinal(current.toordinal() + 7)
    return seen


def _weekday_count(start: date, end: date) -> int:
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            days += 1
        current = date.fromordinal(current.toordinal() + 1)
    return days


def _dec(raw: Any) -> Decimal | None:
    if raw is None:
        return None
    try:
        return Decimal(str(raw))
    except Exception:
        return None


def _mean(values: Iterable[Decimal]) -> Decimal | None:
    values = list(values)
    if not values:
        return None
    return sum(values) / Decimal(len(values))


def _quant(value: Decimal | None, places: int = 6) -> Decimal | None:
    if value is None:
        return None
    return value.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def _fmt(value: Decimal | None, places: int = 6) -> str | None:
    """Canonical decimal string — quantized, trailing zeros stripped,
    at least one decimal place (``57003.0``, ``5.4321``)."""
    quantized = _quant(value, places)
    if quantized is None:
        return None
    text = format(quantized.normalize(), "f")
    return text if "." in text else text + ".0"


def _coverage(observed: int, expected: int) -> str:
    if expected <= 0 or observed <= 0:
        return "no_data"
    return "complete" if observed >= expected else "partial"


class MarketIntelligenceService:
    def __init__(self, *, gateway: MarketDataGateway | None = None) -> None:
        self._gateway = gateway or MarketDataGateway()

    # --- shared helpers ------------------------------------------------------

    def _catalog(self) -> dict[str, Any]:
        return self._gateway.catalog()

    def _resolve_instrument(
        self, catalog: dict[str, Any], instrument_code: str
    ) -> dict[str, Any]:
        code = (instrument_code or "").strip()
        if not code:
            raise ValueError("instrument is required")
        for inst in catalog.get("instruments") or []:
            if inst.get("instrument_code") == code:
                return inst
        for fx in catalog.get("fx_series") or []:
            if fx.get("instrument_code") == code:
                return fx
        raise MarketDataNotFoundError(f"unknown instrument: {code}")

    def _resolve_import_ncm(
        self, catalog: dict[str, Any], ncm_code: str
    ) -> dict[str, Any]:
        code = (ncm_code or "").strip()
        if not code:
            raise ValueError("ncm is required")
        for entry in catalog.get("import_ncms") or []:
            if entry.get("ncm_code") == code and entry.get("active"):
                return entry
        raise MarketDataNotFoundError(f"unknown import ncm: {code}")

    def _resolve_ipp_series(
        self, catalog: dict[str, Any], series_id: str
    ) -> dict[str, Any]:
        code = (series_id or "").strip()
        if not code:
            raise ValueError("series_id is required")
        for entry in catalog.get("producer_price_series") or []:
            if entry.get("series_id") == code and entry.get("active"):
                return entry
        raise MarketDataNotFoundError(
            f"unknown producer price series: {code}"
        )

    def _parse_range(
        self,
        date_from: str | None,
        date_to: str | None,
    ) -> tuple[date, date]:
        if not date_from or not date_to:
            raise ValueError("date_from and date_to are required")
        try:
            start = date.fromisoformat(str(date_from).strip())
            end = date.fromisoformat(str(date_to).strip())
        except ValueError as exc:
            raise ValueError("dates must be ISO YYYY-MM-DD") from exc
        if start > end:
            raise ValueError("date_from must be <= date_to")
        if (end - start).days > MAX_RANGE_DAYS:
            raise ValueError(
                f"date range exceeds {MAX_RANGE_DAYS} days"
            )
        return start, end

    def _validate_fx_kind(self, fx_kind: str | None) -> str:
        kind = (fx_kind or FX_DEFAULT_KIND).strip()
        if kind not in FX_KINDS:
            raise ValueError(f"unsupported fx_kind: {kind}")
        return kind

    def _validate_currency(self, currency: str | None, kind: str) -> str:
        value = (currency or "USD").strip().upper()
        if value not in CURRENCIES:
            raise ValueError(f"unsupported currency: {value}")
        if kind == KIND_FX and value != "BRL":
            raise ValueError("fx series is quoted natively in BRL")
        return value

    def _validate_granularity(
        self, granularity: str | None, kind: str
    ) -> str:
        value = (granularity or "month").strip().lower()
        allowed = FX_GRANULARITIES if kind == KIND_FX else METAL_GRANULARITIES
        if value not in allowed:
            raise ValueError(
                f"granularity {value} is not supported for this series"
            )
        return value

    # --- data access ---------------------------------------------------------

    def _metal_points(
        self, instrument_code: str, start: date, end: date
    ) -> list[Observation]:
        items = self._gateway.metal_observations(
            instrument_code, start, end
        )
        points = []
        for item in items:
            value = _dec(item.get("price"))
            if value is None:
                continue
            try:
                period = date.fromisoformat(item["observation_date"])
            except (KeyError, ValueError):
                continue
            points.append(
                Observation(
                    period=period,
                    value=value,
                    quality=item.get("quality") or "validated",
                    source_id=(item.get("source") or {}).get("source_id"),
                )
            )
        return points

    def _fx_points(
        self, fx_kind: str, start: date, end: date
    ) -> list[Observation]:
        items = self._gateway.fx_observations(fx_kind, start, end)
        points = []
        for item in items:
            value = _dec(item.get("value"))
            if value is None:
                continue
            try:
                period = date.fromisoformat(item["reference_date"])
            except (KeyError, ValueError):
                continue
            points.append(
                Observation(
                    period=period,
                    value=value,
                    quality=item.get("quality") or "validated",
                    source_id=(item.get("source") or {}).get("source_id"),
                )
            )
        return points

    def _import_rows(
        self,
        ncm_code: str,
        start: date,
        end: date,
        country_code: str | None,
        state_code: str | None,
    ) -> list[dict[str, Any]]:
        return self._gateway.comex_imports(
            ncm_code,
            start,
            end,
            country_code=country_code,
            state_code=state_code,
        )

    def _ipp_points(
        self, series_id: str, start: date, end: date
    ) -> list[Observation]:
        items = self._gateway.producer_price_observations(
            series_id, start, end
        )
        points = []
        for item in items:
            value = _dec(item.get("value"))
            if value is None:
                continue
            try:
                period = date.fromisoformat(item["reference_month"])
            except (KeyError, ValueError):
                continue
            points.append(
                Observation(
                    period=period,
                    value=value,
                    quality=item.get("quality") or "validated",
                    source_id=(item.get("source") or {}).get("source_id"),
                )
            )
        return points

    def _fx_monthly_map(
        self, fx_kind: str, start: date, end: date
    ) -> dict[str, Decimal]:
        """Month → mean of valid daily FX observations in that month."""
        by_month: dict[str, list[Decimal]] = {}
        for point in self._fx_points(fx_kind, start, end):
            by_month.setdefault(_month_key(point.period), []).append(
                point.value
            )
        return {
            key: _mean(values) for key, values in by_month.items()
            if values
        }

    def _convert_to_brl(
        self,
        points: list[Observation],
        fx_monthly: dict[str, Decimal],
    ) -> tuple[list[Observation | None], list[str]]:
        """USD monthly price × PTAX monthly average of the same month.

        Returns per-point converted values (``None`` when FX is missing
        for that month) plus the list of months lacking FX.
        """
        converted: list[Observation | None] = []
        missing: list[str] = []
        for point in points:
            fx = fx_monthly.get(_month_key(point.period))
            if fx is None:
                missing.append(_month_key(point.period))
                converted.append(None)
                continue
            converted.append(
                Observation(
                    period=point.period,
                    value=point.value * fx,
                    quality=point.quality,
                    source_id=point.source_id,
                )
            )
        return converted, sorted(set(missing))

    def _ingestion_meta(self, feed: str | None = None) -> dict[str, Any]:
        """Last successful ingestion (global) + per-feed run evidence."""
        try:
            status = self._gateway.ingestion_status()
        except Exception:
            return {
                "last_successful_ingestion_at": None,
                "feed_ingestion": None,
            }
        latest = None
        feed_info = None
        for entry in status.get("feeds") or []:
            stamp = entry.get("last_successful_at")
            if stamp and (latest is None or stamp > latest):
                latest = stamp
            if feed and entry.get("feed") == feed:
                feed_info = {
                    "feed": entry.get("feed"),
                    "last_run_outcome": entry.get("last_outcome")
                    or entry.get("outcome"),
                    "last_error_code": entry.get("last_error_code"),
                    "source_active": entry.get("source_active"),
                    "last_successful_at": entry.get("last_successful_at"),
                    "latest_observation_date": entry.get(
                        "latest_observation_date"
                    ),
                }
        return {
            "last_successful_ingestion_at": latest,
            "feed_ingestion": feed_info,
        }

    def _expected_monthly_period(
        self, today: date, publication_day: int
    ) -> date:
        """Latest month a monthly source should have published by
        ``today``, given the provider's publication day in the
        following month."""
        this_month = date(today.year, today.month, 1)
        lag = 1 if today.day >= publication_day else 2
        return _month_add(this_month, -lag)

    def _last_business_day(self, today: date) -> date:
        """Approximation: weekdays only; holidays are unknown and must
        never be counted as missing publications."""
        current = today
        while current.weekday() >= 5:
            current = date.fromordinal(current.toordinal() - 1)
        return current

    def _freshness(
        self,
        *,
        kind: str,
        latest_available: date | None,
        feed_ingestion: dict[str, Any] | None,
        today: date | None = None,
    ) -> dict[str, Any]:
        """Feed freshness by provider cadence — evaluated on the
        instrument's latest available observation, independent of the
        queried window."""
        today = today or date.today()
        if kind != KIND_FX:
            expected = self._expected_monthly_period(
                today, _PUBLICATION_DAY_BY_KIND.get(kind, 5)
            )
            if latest_available is None:
                status = "unknown"
                lag = None
            else:
                lag = max(
                    0,
                    (expected.year - latest_available.year) * 12
                    + (expected.month - latest_available.month),
                )
                status = "current" if lag == 0 else "delayed"
            return {
                "status": status,
                "expected_cadence": "monthly",
                "expected_latest_period": expected.isoformat(),
                "latest_observation_date": latest_available.isoformat()
                if latest_available
                else None,
                "lag_periods": lag,
                "last_successful_ingestion_at": (feed_ingestion or {}).get(
                    "last_successful_at"
                ),
                "evaluation_date": today.isoformat(),
                "method": FRESHNESS_METHOD,
            }
        expected_day = self._last_business_day(today)
        if latest_available is None:
            status = "unknown"
            lag_days = None
        else:
            lag_days = max(0, (expected_day - latest_available).days)
            status = (
                "current" if lag_days <= FX_STALE_GRACE_DAYS else "delayed"
            )
        return {
            "status": status,
            "expected_cadence": "business_daily",
            "expected_latest_period": expected_day.isoformat(),
            "latest_observation_date": latest_available.isoformat()
            if latest_available
            else None,
            "lag_days": lag_days,
            "last_successful_ingestion_at": (feed_ingestion or {}).get(
                "last_successful_at"
            ),
            "evaluation_date": today.isoformat(),
            "method": FRESHNESS_METHOD,
        }

    @staticmethod
    def _instrument_latest(instrument: dict[str, Any]) -> date | None:
        """Latest available observation for the instrument (catalog-wide,
        independent of the queried window)."""
        raw = instrument.get("latest_observation_date")
        if not raw:
            return None
        try:
            return date.fromisoformat(str(raw)[:10])
        except ValueError:
            return None

    @staticmethod
    def _display_unit(instrument: dict[str, Any], currency: str) -> str:
        """Unit of the *displayed* value — BRL conversions keep the same
        physical unit (``USD/metric ton`` → ``BRL/metric ton``)."""
        unit = instrument.get("unit") or ""
        if currency == "BRL" and "/" in unit:
            return "BRL/" + unit.split("/", 1)[1]
        return unit or currency

    def _data_status(
        self,
        *,
        observed: int,
        expected: int,
        partial_reason: str | None,
    ) -> str:
        """Window-completeness only — one of ``ok`` | ``partial`` |
        ``no_data`` for the *requested period*.

        Feed freshness is a separate dimension reported in
        ``meta.freshness``: a fully covered historical window stays
        ``ok`` even when the source is currently behind its publication
        cadence (R1.1 — two dimensions, never conflated).

        ``partial_reason`` (e.g. ``fx_missing_months:*``) is only set when
        native observations exist but could not all be represented in the
        requested currency — that is a coverage gap, not absent data, so
        it must yield ``partial`` even when zero points survived
        conversion."""
        if observed <= 0:
            return "partial" if partial_reason else "no_data"
        if partial_reason or observed < expected:
            return "partial"
        return "ok"

    def _perspective_summary(
        self,
        *,
        points: list[dict[str, Any]],
        value_key: str,
        granularity: str,
        expected: int,
        feed_ingestion: dict[str, Any] | None,
        include_change: bool,
        include_average: bool = False,
        include_min_max: bool = False,
        totals: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Contextual KPI read model for one perspective (R3).

        Values come from the already-validated series points — the
        summary never recomputes semantics the BFF doesn't own, and
        ``None`` stays ``None`` (no zero-fill). ``unavailable_reason``
        explains an empty perspective by feed evidence, never by guess:
        ``provider_unavailable`` (last run failed upstream),
        ``feed_not_collected`` (no successful run yet),
        ``window_empty`` (ingested history exists outside the window).
        """
        valid = [p for p in points if p.get(value_key) is not None]
        observed = len(valid)
        latest = (
            {
                "period": valid[-1]["period"],
                "value": valid[-1][value_key],
            }
            if valid
            else None
        )
        change = None
        if include_change and len(valid) >= 2:
            first_v = _dec(valid[0][value_key])
            last_v = _dec(valid[-1][value_key])
            if first_v is not None and first_v != 0 and last_v is not None:
                change = _fmt(
                    (last_v - first_v) / first_v * Decimal(100), places=4
                )
        average = (
            _fmt(_mean(_dec(p[value_key]) for p in valid))
            if include_average
            else None
        )
        min_point = max_point = None
        if include_min_max and valid:
            ranked = sorted(valid, key=lambda p: _dec(p[value_key]))
            min_point = {
                "period": ranked[0]["period"],
                "value": ranked[0][value_key],
            }
            max_point = {
                "period": ranked[-1]["period"],
                "value": ranked[-1][value_key],
            }
        missing = (
            [p["period"] for p in points if p.get(value_key) is None][
                :MAX_MISSING_PERIODS
            ]
            if granularity == "month"
            else None
        )
        unavailable_reason = None
        if observed == 0:
            feed = feed_ingestion or {}
            error_code = feed.get("last_error_code")
            if error_code:
                unavailable_reason = (
                    "provider_unavailable"
                    if "UNAVAILABLE" in str(error_code).upper()
                    else "feed_failed"
                )
            elif feed.get("source_active") is False:
                unavailable_reason = "feed_disabled"
            elif feed.get("last_successful_at"):
                unavailable_reason = "window_empty"
            else:
                unavailable_reason = "feed_not_collected"
        return {
            "latest": latest,
            "period_average": average,
            "period_change_pct": change,
            "period_min": min_point,
            "period_max": max_point,
            "totals": totals,
            "observed": observed,
            "expected": expected,
            "coverage": _coverage(observed, expected),
            "missing_periods": missing,
            "unavailable_reason": unavailable_reason,
            "method_version": {
                "average": PERIOD_AVERAGE_METHOD if include_average else None,
                "period_change": (
                    PERIOD_VARIATION_METHOD if include_change else None
                ),
                "min_max": MIN_MAX_METHOD if include_min_max else None,
                "totals": IMPORT_TOTALS_METHOD if totals else None,
                "coverage": COVERAGE_METHOD,
            },
        }

    # --- endpoints -----------------------------------------------------------

    def get_filters(self) -> dict[str, Any]:
        """operationId: listMarketIntelligenceFiltersV1."""
        catalog = self._catalog()
        instruments = []
        for inst in catalog.get("instruments") or []:
            instruments.append(
                {
                    "code": inst["instrument_code"],
                    "kind": KIND_METAL,
                    "label": inst["label"],
                    "unit": inst["unit"],
                    "unit_code": inst["unit_code"],
                    "currency": inst["currency"],
                    "quote_basis": inst["quote_basis"],
                    "granularities": inst.get(
                        "supported_granularities"
                    )
                    or list(METAL_GRANULARITIES),
                    "currencies": list(CURRENCIES),
                    "latest_observation_date": inst.get(
                        "latest_observation_date"
                    ),
                    "source_id": inst["source_id"],
                    # Default-deny: only an explicit display_allowed=true
                    # from the producer grants data access — absent/
                    # null/invalid is never a permission.
                    "selectable": inst.get("display_allowed") is True,
                    # R4 D-04: catalog presence keeps the card
                    # selectable in the UI; data access stays the
                    # rights gate. The pair is emitted explicitly so no
                    # consumer conflates selection with authorization.
                    "selectable_in_ui": inst.get("selectable_in_ui")
                    is not False,
                    "data_access_allowed": inst.get(
                        "data_access_allowed",
                        inst.get("display_allowed") is True,
                    )
                    is True,
                }
            )
        for fx in catalog.get("fx_series") or []:
            instruments.append(
                {
                    "code": fx["instrument_code"],
                    "kind": KIND_FX,
                    "label": fx["label"],
                    "unit": fx["unit"],
                    "unit_code": "brl_per_usd",
                    "currency": "BRL",
                    "quote_basis": FX_DEFAULT_KIND,
                    "granularities": fx.get("supported_granularities")
                    or list(FX_GRANULARITIES),
                    "currencies": ["BRL"],
                    "latest_observation_date": fx.get(
                        "latest_observation_date"
                    ),
                    "source_id": fx["source_id"],
                    "selectable": fx.get("display_allowed") is True,
                    "selectable_in_ui": fx.get("selectable_in_ui")
                    is not False,
                    "data_access_allowed": fx.get(
                        "data_access_allowed",
                        fx.get("display_allowed") is True,
                    )
                    is True,
                }
            )
        import_ncms = [
            {
                "ncm_code": n["ncm_code"],
                "kind": KIND_IMPORT,
                "description": n["description"],
                "family_code": n.get("family_code"),
                "ncm_version": n.get("ncm_version"),
                "unit": "USD/metric ton",
                "granularities": n.get("supported_granularities")
                or list(IMPORT_GRANULARITIES),
                "source_id": n.get("source_id"),
                "latest_observation_date": n.get(
                    "latest_observation_date"
                ),
                # Default-deny — identical posture to instruments.
                "selectable": n.get("display_allowed") is True,
                "selectable_in_ui": n.get("selectable_in_ui") is not False,
                "data_access_allowed": n.get(
                    "data_access_allowed",
                    n.get("display_allowed") is True,
                )
                is True,
            }
            for n in catalog.get("import_ncms") or []
        ]
        producer_price_series = [
            {
                "series_id": s["series_id"],
                "kind": KIND_IPP,
                "label": s["label"],
                "activity_code": s["activity_code"],
                "activity_label": s["activity_label"],
                "variable_code": s["variable_code"],
                "variable_label": s["variable_label"],
                "table_code": s["table_code"],
                "metric_kind": s["metric_kind"],
                "unit": s["unit"],
                "base_reference": s["base_reference"],
                "granularities": s.get("supported_granularities")
                or list(IPP_GRANULARITIES),
                "source_id": s.get("source_id"),
                "latest_observation_date": s.get(
                    "latest_observation_date"
                ),
                "selectable": s.get("display_allowed") is True,
                "selectable_in_ui": s.get("selectable_in_ui") is not False,
                "data_access_allowed": s.get(
                    "data_access_allowed",
                    s.get("display_allowed") is True,
                )
                is True,
            }
            for s in catalog.get("producer_price_series") or []
        ]
        sources = [
            {
                "source_id": s["source_id"],
                "provider_id": s["provider_id"],
                "attribution": s["attribution"],
                "license_reference": s["license_reference"],
            }
            for s in catalog.get("sources") or []
        ]
        meta = self._ingestion_meta()
        selectable = [i for i in instruments if i["selectable"]]
        has_data = any(
            i["latest_observation_date"] for i in selectable
        ) or any(
            s["selectable"] and s["latest_observation_date"]
            for s in import_ncms + producer_price_series
        )
        return {
            "instruments": instruments,
            "import_ncms": import_ncms,
            "producer_price_series": producer_price_series,
            "currencies": list(CURRENCIES),
            "granularities": list(ALL_GRANULARITIES),
            "fx_kinds": list(FX_KINDS),
            "default_fx_kind": FX_DEFAULT_KIND,
            "default_instrument": (
                selectable[0]["code"] if selectable else None
            ),
            "sources": sources,
            "meta": {
                "data_status": "ok" if has_data else "no_data",
                "schema_version": SCHEMA_VERSION,
                **meta,
            },
        }

    def get_summary(
        self,
        *,
        instrument_code: str,
        currency: str | None,
        fx_kind: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> dict[str, Any]:
        """operationId: getMarketIntelligenceSummaryV1."""
        catalog = self._catalog()
        instrument = self._resolve_instrument(catalog, instrument_code)
        kind = instrument.get("kind", KIND_METAL)
        currency = self._validate_currency(currency, kind)
        fx_kind = self._validate_fx_kind(fx_kind)
        start, end = self._parse_range(date_from, date_to)

        partial_reason = None
        if kind == KIND_FX:
            raw_points = self._fx_points(fx_kind, start, end)
            points: list[Observation | None] = list(raw_points)
        else:
            raw_points = self._metal_points(
                instrument["instrument_code"], start, end
            )
            if currency == "BRL":
                fx_monthly = self._fx_monthly_map(fx_kind, start, end)
                points, missing = self._convert_to_brl(
                    raw_points, fx_monthly
                )
                if missing:
                    partial_reason = f"fx_missing_months:{','.join(missing)}"
            else:
                points = list(raw_points)

        valid = [p for p in points if p is not None]
        expected = (
            _weekday_count(start, end)
            if kind == KIND_FX
            else len(_month_range(start, end))
        )

        display_unit = self._display_unit(instrument, currency)
        native_unit = instrument.get("unit")
        converted = currency == "BRL" and kind == KIND_METAL
        last_quote = None
        if valid:
            latest = valid[-1]
            last_quote = {
                "value": _fmt(latest.value),
                "reference_date": latest.period.isoformat(),
                "currency": currency,
                "unit": display_unit,
            }
            if converted:
                native = next(
                    (p for p in reversed(raw_points) if p.period == latest.period),
                    None,
                )
                month_key = _month_key(latest.period)
                last_quote["native"] = {
                    "value": _fmt(native.value) if native else None,
                    "currency": "USD",
                    "unit": native_unit,
                }
                last_quote["conversion"] = {
                    "method": FX_CONVERSION_METHOD,
                    "fx_kind": fx_kind,
                    "fx_rate": _fmt(fx_monthly.get(month_key)),
                    "fx_reference_period": month_key,
                }
        average_value = _mean([p.value for p in valid])
        period_average = {
            "value": _fmt(average_value),
            "valid_observations": len(valid),
            "coverage": _coverage(len(valid), expected),
            "unit": display_unit,
            "method": PERIOD_AVERAGE_METHOD,
        }
        variation = None
        if len(valid) >= 2 and valid[0].value != 0:
            variation = _quant(
                (valid[-1].value / valid[0].value - Decimal(1))
                * Decimal(100),
                places=4,
            )
        period_variation = {
            "percent": _fmt(variation, places=4),
            "calculation_method": PERIOD_VARIATION_METHOD,
        }

        fx_reference = {"value": None, "pair": FX_PAIR,
                        "rate_kind": fx_kind, "reference_date": None}
        fx_points = self._fx_points(fx_kind, start, end)
        if fx_points:
            fx_reference = {
                "value": _fmt(fx_points[-1].value),
                "pair": FX_PAIR,
                "rate_kind": fx_kind,
                "reference_date": fx_points[-1].period.isoformat(),
            }

        meta = self._ingestion_meta(_FEED_BY_KIND[kind])
        freshness = self._freshness(
            kind=kind,
            latest_available=self._instrument_latest(instrument),
            feed_ingestion=meta["feed_ingestion"],
        )
        data_status = self._data_status(
            observed=len(valid),
            expected=expected,
            partial_reason=partial_reason,
        )
        return {
            "instrument": {
                "code": instrument["instrument_code"],
                "kind": kind,
                "label": instrument["label"],
                "unit": instrument.get("unit"),
                "quote_basis": instrument.get("quote_basis"),
            },
            "last_quote": last_quote,
            "period_average": period_average,
            "period_variation": period_variation,
            "fx_reference": fx_reference,
            "meta": {
                "data_status": data_status,
                "source_id": instrument.get("source_id"),
                "currency": currency,
                "unit": display_unit,
                "native_unit": native_unit,
                "freshness": freshness,
                "method_version": {
                    "fx_conversion": FX_CONVERSION_METHOD
                    if currency == "BRL" and kind == KIND_METAL
                    else None,
                    "average": PERIOD_AVERAGE_METHOD,
                    "variation": PERIOD_VARIATION_METHOD,
                    "coverage": COVERAGE_METHOD,
                },
                "partial_reason": partial_reason,
                **meta,
            },
        }

    def list_series(
        self,
        *,
        instrument_code: str,
        currency: str | None,
        granularity: str | None,
        fx_kind: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> dict[str, Any]:
        """operationId: listMarketIntelligenceSeriesV1."""
        catalog = self._catalog()
        instrument = self._resolve_instrument(catalog, instrument_code)
        kind = instrument.get("kind", KIND_METAL)
        currency = self._validate_currency(currency, kind)
        fx_kind = self._validate_fx_kind(fx_kind)
        granularity = self._validate_granularity(granularity, kind)
        start, end = self._parse_range(date_from, date_to)

        partial_reason = None
        points: list[dict[str, Any]]
        if kind == KIND_FX:
            points = self._fx_series(
                fx_kind, granularity, start, end
            )
            expected = self._expected_buckets(
                FX_GRANULARITIES, granularity, start, end
            )
            observed = sum(1 for p in points if p["value"] is not None)
        else:
            raw = self._metal_points(
                instrument["instrument_code"], start, end
            )
            if currency == "BRL":
                fx_monthly = self._fx_monthly_map(fx_kind, start, end)
                converted, missing = self._convert_to_brl(raw, fx_monthly)
                if missing:
                    partial_reason = (
                        f"fx_missing_months:{','.join(missing)}"
                    )
                native_by_month = {
                    _month_key(p.period): p for p in raw
                }
                converted_by_month = {
                    _month_key(c.period): c
                    for c in converted
                    if c is not None
                }
                points = self._metal_series(
                    granularity,
                    start,
                    end,
                    native_by_month,
                    converted_by_month,
                    currency,
                )
            else:
                native_by_month = {
                    _month_key(p.period): p for p in raw
                }
                points = self._metal_series(
                    granularity,
                    start,
                    end,
                    native_by_month,
                    native_by_month,
                    currency,
                )
            expected = self._expected_buckets(
                METAL_GRANULARITIES, granularity, start, end
            )
            observed = sum(1 for p in points if p["value"] is not None)

        for point in points:
            point.pop("period_date", None)

        meta = self._ingestion_meta(_FEED_BY_KIND[kind])
        freshness = self._freshness(
            kind=kind,
            latest_available=self._instrument_latest(instrument),
            feed_ingestion=meta["feed_ingestion"],
        )
        data_status = self._data_status(
            observed=observed,
            expected=expected,
            partial_reason=partial_reason,
        )
        return {
            "instrument": {
                "code": instrument["instrument_code"],
                "kind": kind,
                "label": instrument["label"],
                "unit": instrument.get("unit"),
                "quote_basis": instrument.get("quote_basis"),
            },
            "currency": currency,
            "unit": self._display_unit(instrument, currency),
            "native_unit": instrument.get("unit"),
            "granularity": granularity,
            "points": points,
            "meta": {
                "source_id": instrument.get("source_id"),
                "freshness": freshness,
                "fx_source_id": "bcb-ptax"
                if currency == "BRL" or kind == KIND_FX
                else None,
                "fx_kind": fx_kind
                if currency == "BRL" or kind == KIND_FX
                else None,
                "method_version": {
                    "fx_conversion": FX_CONVERSION_METHOD
                    if currency == "BRL" and kind == KIND_METAL
                    else None,
                    "coverage": COVERAGE_METHOD,
                },
                "data_status": data_status,
                "partial_reason": partial_reason,
                "schema_version": SCHEMA_VERSION,
                **meta,
            },
        }

    # --- R4 multi-instrument quotes (Metais perspective) ---------------------

    def list_quotes_series(
        self,
        *,
        instruments: str | None,
        granularity: str | None,
        currency: str | None,
        fx_kind: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> dict[str, Any]:
        """operationId: listMarketIntelligenceQuoteSeriesV1.

        Multi-instrument metal series for the Metais perspective. Each
        requested instrument yields one entry: authorized instruments
        carry real points + summary; quarantined/unapproved instruments
        carry only catalog identity + ``availability`` — selection in
        the UI never bypasses ``display_allowed`` (R4 D-04).
        """
        catalog = self._catalog()
        codes = [
            c.strip() for c in (instruments or "").split(",") if c.strip()
        ]
        if not codes:
            raise ValueError("instruments is required")
        if len(codes) > MAX_QUOTE_INSTRUMENTS:
            raise ValueError(
                f"at most {MAX_QUOTE_INSTRUMENTS} instruments per request"
            )
        currency = self._validate_currency(currency, KIND_METAL)
        fx_kind = self._validate_fx_kind(fx_kind)
        granularity = self._validate_granularity(granularity, KIND_METAL)
        start, end = self._parse_range(date_from, date_to)
        expected = self._expected_buckets(
            METAL_GRANULARITIES, granularity, start, end
        )

        series = []
        for code in codes:
            instrument = self._resolve_instrument(catalog, code)
            if instrument.get("kind", KIND_METAL) != KIND_METAL:
                raise ValueError(
                    f"instrument is not a metal series: {code}"
                )
            display = instrument.get("display_allowed") is True
            availability = {
                "selectable_in_ui": instrument.get("selectable_in_ui")
                is not False,
                "data_access_allowed": display,
                "observations_available": bool(
                    instrument.get("latest_observation_date")
                ),
                "source_id": instrument.get("source_id"),
                "unavailable_reason": (
                    None if display else "source_use_pending"
                ),
            }
            instrument_meta = {
                "code": instrument["instrument_code"],
                "kind": KIND_METAL,
                "label": instrument["label"],
                "unit": instrument.get("unit"),
                "quote_basis": instrument.get("quote_basis"),
            }
            if not display:
                series.append(
                    {
                        "instrument": instrument_meta,
                        "unit": instrument.get("unit"),
                        "availability": availability,
                        "points": [],
                        "summary": None,
                    }
                )
                continue
            payload = self.list_series(
                instrument_code=code,
                currency=currency,
                granularity=granularity,
                fx_kind=fx_kind,
                date_from=date_from,
                date_to=date_to,
            )
            summary = self._perspective_summary(
                points=payload["points"],
                value_key="value",
                granularity=granularity,
                expected=expected,
                feed_ingestion=(payload.get("meta") or {}).get(
                    "feed_ingestion"
                ),
                include_change=True,
                include_average=True,
            )
            series.append(
                {
                    "instrument": instrument_meta,
                    "unit": payload.get("unit"),
                    "currency": payload.get("currency"),
                    "availability": availability,
                    "points": payload["points"],
                    "summary": summary,
                    "meta": payload.get("meta"),
                }
            )
        return {
            "granularity": granularity,
            "currency": currency,
            "series": series,
            "meta": {
                "data_status": (
                    "ok"
                    if any(
                        (s.get("summary") or {}).get("observed", 0) > 0
                        for s in series
                    )
                    else "no_data"
                ),
                "schema_version": SCHEMA_VERSION,
                **self._ingestion_meta(_FEED_BY_KIND[KIND_METAL]),
            },
        }

    def list_quotes_compare(
        self,
        *,
        instruments: str | None,
        granularity: str | None,
        currency: str | None,
        fx_kind: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> dict[str, Any]:
        """operationId: listMarketIntelligenceQuoteCompareV1.

        Period-aligned comparison over authorized series only —
        comparability requires >=2 data-access-allowed instruments with
        the same display unit and granularity. Unauthorized instruments
        keep their identity and reason but never values.
        """
        payload = self.list_quotes_series(
            instruments=instruments,
            granularity=granularity,
            currency=currency,
            fx_kind=fx_kind,
            date_from=date_from,
            date_to=date_to,
        )
        authorized = [
            s
            for s in payload["series"]
            if s["availability"]["data_access_allowed"]
        ]
        units = {s.get("unit") for s in authorized}
        comparable = len(authorized) >= 2 and len(units) == 1
        reason = None
        if len(authorized) < 2:
            reason = "insufficient_authorized_series"
        elif len(units) != 1:
            reason = "incompatible_units"

        periods = sorted(
            {
                p["period"]
                for s in authorized
                for p in s["points"]
            }
        )
        aligned_series = []
        for s in payload["series"]:
            if not s["availability"]["data_access_allowed"]:
                aligned_series.append(
                    {
                        "instrument": s["instrument"],
                        "unit": s.get("unit"),
                        "availability": s["availability"],
                        "values": None,
                    }
                )
                continue
            by_period = {p["period"]: p["value"] for p in s["points"]}
            aligned_series.append(
                {
                    "instrument": s["instrument"],
                    "unit": s.get("unit"),
                    "availability": s["availability"],
                    "summary": s.get("summary"),
                    "values": [by_period.get(period) for period in periods],
                }
            )
        return {
            "comparison": {
                "comparable": comparable,
                "reason": reason,
                "unit": next(iter(units)) if len(units) == 1 else None,
                "granularity": payload["granularity"],
                "currency": payload["currency"],
                "method": COMPARE_ALIGNMENT_METHOD,
            },
            "periods": periods,
            "series": aligned_series,
            "meta": payload["meta"],
        }

    def list_monthly_averages(
        self,
        *,
        instrument_code: str,
        currency: str | None,
        fx_kind: str | None,
        date_from: str | None,
        date_to: str | None,
        page: str | None,
        page_size: str | None,
    ) -> dict[str, Any]:
        """operationId: listMarketIntelligenceMonthlyAveragesV1."""
        catalog = self._catalog()
        instrument = self._resolve_instrument(catalog, instrument_code)
        kind = instrument.get("kind", KIND_METAL)
        currency = self._validate_currency(currency, kind)
        fx_kind = self._validate_fx_kind(fx_kind)
        start, end = self._parse_range(date_from, date_to)
        page_no, size = self._parse_pagination(page, page_size)

        partial_reason = None
        if kind == KIND_FX:
            raw = self._fx_points(fx_kind, start, end)
            rows = self._monthly_rows(
                start, end, raw, currency="BRL", fx_monthly=None
            )
        else:
            raw = self._metal_points(
                instrument["instrument_code"], start, end
            )
            if currency == "BRL":
                fx_monthly = self._fx_monthly_map(fx_kind, start, end)
                _, missing = self._convert_to_brl(raw, fx_monthly)
                if missing:
                    partial_reason = (
                        f"fx_missing_months:{','.join(missing)}"
                    )
                rows = self._monthly_rows(
                    start,
                    end,
                    raw,
                    currency="BRL",
                    fx_monthly=fx_monthly,
                )
            else:
                rows = self._monthly_rows(
                    start, end, raw, currency="USD", fx_monthly=None
                )

        total = len(rows)
        items = rows[(page_no - 1) * size : page_no * size]
        meta = self._ingestion_meta(_FEED_BY_KIND[kind])
        freshness = self._freshness(
            kind=kind,
            latest_available=self._instrument_latest(instrument),
            feed_ingestion=meta["feed_ingestion"],
        )
        observed = sum(1 for r in rows if r["average"] is not None)
        data_status = self._data_status(
            observed=observed,
            expected=total,
            partial_reason=partial_reason,
        )
        return {
            "instrument": {
                "code": instrument["instrument_code"],
                "kind": kind,
                "label": instrument["label"],
                "unit": instrument.get("unit"),
                "quote_basis": instrument.get("quote_basis"),
            },
            "currency": currency,
            "unit": self._display_unit(instrument, currency),
            "native_unit": instrument.get("unit"),
            "items": items,
            "page_info": {
                "page": page_no,
                "page_size": size,
                "total_items": total,
                "total_pages": max(1, -(-total // size)),
                "has_more": page_no * size < total,
            },
            "meta": {
                "method_version": {
                    "fx_conversion": FX_CONVERSION_METHOD
                    if currency == "BRL" and kind == KIND_METAL
                    else None,
                    "coverage": COVERAGE_METHOD,
                },
                "data_status": data_status,
                "freshness": freshness,
                "partial_reason": partial_reason,
                "source_id": instrument.get("source_id"),
                "schema_version": SCHEMA_VERSION,
                **meta,
            },
        }

    def list_import_series(
        self,
        *,
        ncm_code: str,
        granularity: str | None,
        date_from: str | None,
        date_to: str | None,
        country_code: str | None,
        state_code: str | None,
    ) -> dict[str, Any]:
        """operationId: listMarketIntelligenceImportSeriesV1.

        Monthly FOB import totals per approved NCM — ``USD/metric ton``
        is derived from aggregate sums, never from row-level ratios.
        """
        catalog = self._catalog()
        ncm = self._resolve_import_ncm(catalog, ncm_code)
        granularity = self._validate_granularity(granularity, KIND_IMPORT)
        start, end = self._parse_range(date_from, date_to)
        country = (country_code or "").strip() or None
        state = (state_code or "").strip() or None

        rows = self._import_rows(
            ncm["ncm_code"], start, end, country, state
        )
        by_month: dict[str, dict[str, Any]] = {}
        for row in rows:
            try:
                month = date.fromisoformat(row["reference_month"])
            except (KeyError, ValueError):
                continue
            key = _month_key(month)
            bucket = by_month.setdefault(
                key,
                {
                    "fob": Decimal(0),
                    "weight": Decimal(0),
                    "rows": 0,
                    "all_validated": True,
                },
            )
            bucket["fob"] += _dec(row.get("fob_usd_total")) or Decimal(0)
            bucket["weight"] += _dec(
                row.get("net_weight_kg_total")
            ) or Decimal(0)
            bucket["rows"] += int(row.get("contributing_rows") or 0)
            if (row.get("quality") or "") != "validated":
                bucket["all_validated"] = False

        points = self._import_points(granularity, start, end, by_month)
        expected = self._expected_buckets(
            IMPORT_GRANULARITIES, granularity, start, end
        )
        observed = sum(
            1 for p in points if p["unit_value_usd_per_t"] is not None
        )
        meta = self._ingestion_meta(COMEX_FEED)
        freshness = self._freshness(
            kind=KIND_IMPORT,
            latest_available=self._instrument_latest(ncm),
            feed_ingestion=meta["feed_ingestion"],
        )
        valid_points = [
            p for p in points if p["unit_value_usd_per_t"] is not None
        ]
        totals = None
        if valid_points:
            totals = {
                "fob_usd_total": _fmt(
                    sum(
                        (_dec(p["fob_usd_total"]) or Decimal(0)
                         for p in valid_points),
                        Decimal(0),
                    ),
                    places=2,
                ),
                "net_weight_t": _fmt(
                    sum(
                        (_dec(p["net_weight_t"]) or Decimal(0)
                         for p in valid_points),
                        Decimal(0),
                    )
                ),
            }
        summary = self._perspective_summary(
            points=points,
            value_key="unit_value_usd_per_t",
            granularity=granularity,
            expected=expected,
            feed_ingestion=meta["feed_ingestion"],
            include_change=True,
            totals=totals,
        )
        return {
            "series": {
                "ncm_code": ncm["ncm_code"],
                "ncm_version": ncm["ncm_version"],
                "description": ncm["description"],
                "family_code": ncm.get("family_code"),
                "kind": KIND_IMPORT,
                "unit": "USD/metric ton",
                "metric_kind": "import_fob_unit_value",
            },
            "filters": {
                "country_code": country,
                "state_code": state,
            },
            "granularity": granularity,
            "points": points,
            "summary": summary,
            "meta": {
                "source_id": "mdic-comex-stat",
                "freshness": freshness,
                "data_status": self._data_status(
                    observed=observed,
                    expected=expected,
                    partial_reason=None,
                ),
                "method_version": {
                    "unit_value": IMPORT_UNIT_VALUE_METHOD,
                    "coverage": COVERAGE_METHOD,
                },
                "schema_version": SCHEMA_VERSION,
                **meta,
            },
        }

    def _import_points(
        self,
        granularity: str,
        start: date,
        end: date,
        by_month: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        def _point(key, bucket, months_in_bucket):
            if bucket is None:
                return {
                    "period": key,
                    "fob_usd_total": None,
                    "net_weight_kg_total": None,
                    "net_weight_t": None,
                    "unit_value_usd_per_t": None,
                    "contributing_rows": 0,
                    "observation_count": 0,
                    "coverage": "no_data",
                }
            tonnes = bucket["weight"] / Decimal(1000)
            unit = (
                bucket["fob"] / tonnes if tonnes > 0 else None
            )
            return {
                "period": key,
                "fob_usd_total": _fmt(bucket["fob"], places=2),
                "net_weight_kg_total": _fmt(bucket["weight"], places=3),
                "net_weight_t": _fmt(tonnes, places=6),
                "unit_value_usd_per_t": _fmt(unit),
                "contributing_rows": bucket["rows"],
                "observation_count": 1,
                "quality": "validated"
                if bucket["all_validated"]
                else "partial",
                "coverage": _coverage(1, months_in_bucket)
                if granularity == "year"
                else "ok",
            }

        if granularity == "month":
            return [
                _point(
                    _month_key(month),
                    by_month.get(_month_key(month)),
                    1,
                )
                for month in _month_range(start, end)
            ]
        points = []
        for year in sorted({m.year for m in _month_range(start, end)}):
            months = [
                m for m in _month_range(start, end) if m.year == year
            ]
            fob = sum(
                (by_month[_month_key(m)]["fob"]
                 for m in months if _month_key(m) in by_month),
                Decimal(0),
            )
            weight = sum(
                (by_month[_month_key(m)]["weight"]
                 for m in months if _month_key(m) in by_month),
                Decimal(0),
            )
            present = [
                by_month[_month_key(m)]
                for m in months
                if _month_key(m) in by_month
            ]
            bucket = (
                {
                    "fob": fob,
                    "weight": weight,
                    "rows": sum(b["rows"] for b in present),
                    "all_validated": all(
                        b["all_validated"] for b in present
                    ),
                }
                if present
                else None
            )
            points.append(_point(str(year), bucket, len(months)))
        return points

    def list_producer_price_series(
        self,
        *,
        series_id: str,
        granularity: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> dict[str, Any]:
        """operationId: listMarketIntelligenceProducerPriceSeriesV1."""
        catalog = self._catalog()
        series = self._resolve_ipp_series(catalog, series_id)
        granularity = self._validate_granularity(granularity, KIND_IPP)
        start, end = self._parse_range(date_from, date_to)

        raw = self._ipp_points(series["series_id"], start, end)
        by_month = {_month_key(p.period): p for p in raw}
        points: list[dict[str, Any]] = []
        if granularity == "month":
            for month in _month_range(start, end):
                key = _month_key(month)
                point = by_month.get(key)
                points.append(
                    {
                        "period": key,
                        "value": _fmt(point.value)
                        if point is not None
                        else None,
                        "quality": point.quality if point else None,
                        "observation_count": 1 if point else 0,
                        "coverage": "ok" if point else "no_data",
                    }
                )
        else:
            for year in sorted(
                {m.year for m in _month_range(start, end)}
            ):
                months = [
                    m for m in _month_range(start, end) if m.year == year
                ]
                values = [
                    by_month[_month_key(m)].value
                    for m in months
                    if _month_key(m) in by_month
                ]
                points.append(
                    {
                        "period": str(year),
                        "value": _fmt(_mean(values)) if values else None,
                        "observation_count": len(values),
                        "coverage": _coverage(len(values), len(months)),
                    }
                )

        expected = self._expected_buckets(
            IPP_GRANULARITIES, granularity, start, end
        )
        observed = sum(1 for p in points if p["value"] is not None)
        meta = self._ingestion_meta(IPP_FEED)
        freshness = self._freshness(
            kind=KIND_IPP,
            latest_available=self._instrument_latest(series),
            feed_ingestion=meta["feed_ingestion"],
        )
        is_change_series = series["metric_kind"] != "ipp_index"
        summary = self._perspective_summary(
            points=points,
            value_key="value",
            granularity=granularity,
            expected=expected,
            feed_ingestion=meta["feed_ingestion"],
            # A percentage series has no period variation (a % of % is
            # not an approved metric) — amplitude is shown instead.
            include_change=not is_change_series,
            include_min_max=is_change_series,
        )
        return {
            "series": {
                "series_id": series["series_id"],
                "kind": KIND_IPP,
                "label": series["label"],
                "activity_code": series["activity_code"],
                "activity_label": series["activity_label"],
                "variable_code": series["variable_code"],
                "variable_label": series["variable_label"],
                "table_code": series["table_code"],
                "metric_kind": series["metric_kind"],
                "unit": series["unit"],
                "base_reference": series["base_reference"],
            },
            "granularity": granularity,
            "points": points,
            "summary": summary,
            "meta": {
                "source_id": series["source_id"],
                "freshness": freshness,
                "data_status": self._data_status(
                    observed=observed,
                    expected=expected,
                    partial_reason=None,
                ),
                "method_version": {
                    "average": PERIOD_AVERAGE_METHOD,
                    "coverage": COVERAGE_METHOD,
                },
                "schema_version": SCHEMA_VERSION,
                **meta,
            },
        }

    def list_fx_series(
        self,
        *,
        fx_kind: str | None,
        granularity: str | None,
        date_from: str | None,
        date_to: str | None,
    ) -> dict[str, Any]:
        """operationId: listMarketIntelligenceFxSeriesV1.

        PTAX closing bulletins — buy and sell are distinct rate kinds,
        missing business days stay missing (no forward-fill).
        """
        catalog = self._catalog()
        instrument = self._resolve_instrument(catalog, FX_INSTRUMENT_CODE)
        fx_kind = self._validate_fx_kind(fx_kind)
        granularity = self._validate_granularity(granularity, KIND_FX)
        start, end = self._parse_range(date_from, date_to)

        points = self._fx_series(fx_kind, granularity, start, end)
        for point in points:
            point.pop("period_date", None)
        expected = self._expected_buckets(
            FX_GRANULARITIES, granularity, start, end
        )
        observed = sum(1 for p in points if p["value"] is not None)
        meta = self._ingestion_meta(_FEED_BY_KIND[KIND_FX])
        freshness = self._freshness(
            kind=KIND_FX,
            latest_available=self._instrument_latest(instrument),
            feed_ingestion=meta["feed_ingestion"],
        )
        summary = self._perspective_summary(
            points=points,
            value_key="value",
            granularity=granularity,
            expected=expected,
            feed_ingestion=meta["feed_ingestion"],
            include_change=True,
            include_average=True,
        )
        return {
            "series": {
                "instrument_code": FX_INSTRUMENT_CODE,
                "kind": KIND_FX,
                "label": instrument["label"],
                "pair": FX_PAIR,
                "rate_kind": fx_kind,
                "unit": "BRL per USD",
            },
            "granularity": granularity,
            "points": points,
            "summary": summary,
            "meta": {
                "source_id": "bcb-ptax",
                "freshness": freshness,
                "data_status": self._data_status(
                    observed=observed,
                    expected=expected,
                    partial_reason=None,
                ),
                "method_version": {"coverage": COVERAGE_METHOD},
                "schema_version": SCHEMA_VERSION,
                **meta,
            },
        }

    # --- series builders -----------------------------------------------------

    def _metal_series(
        self,
        granularity: str,
        start: date,
        end: date,
        native_by_month: dict[str, Observation],
        value_by_month: dict[str, Observation],
        currency: str,
    ) -> list[dict[str, Any]]:
        points = []
        if granularity == "month":
            for month in _month_range(start, end):
                key = _month_key(month)
                point = value_by_month.get(key)
                has_native = key in native_by_month
                coverage = (
                    "ok"
                    if point is not None
                    else ("fx_missing" if has_native else "no_data")
                )
                points.append(
                    {
                        "period": key,
                        "period_date": month,
                        "value": _fmt(point.value)
                        if point is not None
                        else None,
                        "observation_count": 1 if has_native else 0,
                        "coverage": coverage,
                    }
                )
            return points
        # year — mean of valid months within each calendar year.
        years = sorted({m.year for m in _month_range(start, end)})
        for year in years:
            months = [
                m for m in _month_range(start, end) if m.year == year
            ]
            values = [
                value_by_month[_month_key(m)].value
                for m in months
                if _month_key(m) in value_by_month
            ]
            native_count = sum(
                1 for m in months if _month_key(m) in native_by_month
            )
            points.append(
                {
                    "period": str(year),
                    "period_date": date(year, 1, 1),
                    "value": _fmt(_mean(values)) if values else None,
                    "observation_count": len(values),
                    "coverage": _coverage(len(values), len(months)),
                    "native_observation_count": native_count,
                }
            )
        return points

    def _fx_series(
        self, fx_kind: str, granularity: str, start: date, end: date
    ) -> list[dict[str, Any]]:
        raw = self._fx_points(fx_kind, start, end)
        if granularity == "day":
            # Only observed business days — weekends/holidays are
            # legitimate non-publication days, not null buckets.
            return [
                {
                    "period": p.period.isoformat(),
                    "period_date": p.period,
                    "value": _fmt(p.value),
                    "observation_count": 1,
                    "coverage": "ok",
                }
                for p in raw
            ]
        if granularity == "week":
            # ISO-week buckets — mean of valid daily bulletins inside
            # each week; weeks without publications stay absent
            # (no forward-fill), weeks crossed by the window are
            # reported with their real coverage.
            by_week: dict[str, list[Decimal]] = {}
            for p in raw:
                by_week.setdefault(_week_key(p.period), []).append(
                    p.value
                )
            points = []
            for key in _week_range(start, end):
                values = by_week.get(key) or []
                points.append(
                    {
                        "period": key,
                        "period_date": start,
                        "value": _fmt(_mean(values)) if values else None,
                        "observation_count": len(values),
                        "coverage": "ok" if values else "no_data",
                    }
                )
            return points
        by_month: dict[str, list[Decimal]] = {}
        for p in raw:
            by_month.setdefault(_month_key(p.period), []).append(p.value)
        if granularity == "month":
            points = []
            for month in _month_range(start, end):
                key = _month_key(month)
                values = by_month.get(key) or []
                expected = _weekday_count(
                    month,
                    min(end, date(
                        month.year,
                        month.month,
                        calendar.monthrange(month.year, month.month)[1],
                    )),
                )
                points.append(
                    {
                        "period": key,
                        "period_date": month,
                        "value": _fmt(_mean(values))
                        if values
                        else None,
                        "observation_count": len(values),
                        "expected_observations": expected,
                        "coverage": _coverage(len(values), expected),
                    }
                )
            return points
        # year — mean of valid daily observations per calendar year.
        years = sorted({m.year for m in _month_range(start, end)})
        points = []
        for year in years:
            year_start = max(start, date(year, 1, 1))
            year_end = min(end, date(year, 12, 31))
            values = [
                p.value
                for p in raw
                if year_start <= p.period <= year_end
            ]
            expected = _weekday_count(year_start, year_end)
            points.append(
                {
                    "period": str(year),
                    "period_date": date(year, 1, 1),
                    "value": _fmt(_mean(values)) if values else None,
                    "observation_count": len(values),
                    "expected_observations": expected,
                    "coverage": _coverage(len(values), expected),
                }
            )
        return points

    def _monthly_rows(
        self,
        start: date,
        end: date,
        raw: list[Observation],
        *,
        currency: str,
        fx_monthly: dict[str, Decimal] | None,
    ) -> list[dict[str, Any]]:
        by_month: dict[str, list[Decimal]] = {}
        for p in raw:
            by_month.setdefault(_month_key(p.period), []).append(p.value)
        rows = []
        for month in _month_range(start, end):
            key = _month_key(month)
            values = by_month.get(key) or []
            fx_rate = None
            if currency == "BRL" and fx_monthly is not None:
                fx_rate = fx_monthly.get(key)
            if currency == "BRL" and fx_monthly is not None:
                avg = (
                    _mean(values) * fx_rate
                    if values and fx_rate is not None
                    else None
                )
                coverage = (
                    "ok"
                    if values and fx_rate is not None
                    else ("fx_missing" if values else "no_data")
                )
            else:
                avg = _mean(values)
                coverage = "ok" if values else "no_data"
            rows.append(
                {
                    "period": key,
                    "average": _fmt(avg),
                    "native_average": _fmt(_mean(values)) if values else None,
                    "observation_count": len(values),
                    "coverage": coverage,
                    "fx_rate": _fmt(fx_rate),
                    "period_start": month.isoformat(),
                    "period_end": date(
                        month.year,
                        month.month,
                        calendar.monthrange(month.year, month.month)[1],
                    ).isoformat(),
                }
            )
        return rows

    def _expected_buckets(self, allowed, granularity, start, end) -> int:
        if granularity == "week":
            return len(_week_range(start, end))
        if granularity == "month":
            return len(_month_range(start, end))
        if granularity == "year":
            return len({m.year for m in _month_range(start, end)})
        return _weekday_count(start, end)

    def _parse_pagination(
        self, page: str | None, page_size: str | None
    ) -> tuple[int, int]:
        try:
            page_no = int(page) if page else 1
            size = int(page_size) if page_size else DEFAULT_PAGE_SIZE
        except ValueError as exc:
            raise ValueError("page and page_size must be integers") from exc
        if page_no < 1:
            raise ValueError("page must be >= 1")
        if size < 1 or size > MAX_PAGE_SIZE:
            raise ValueError(
                f"page_size must be between 1 and {MAX_PAGE_SIZE}"
            )
        return page_no, size
