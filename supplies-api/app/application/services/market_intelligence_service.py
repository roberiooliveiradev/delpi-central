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

METAL_GRANULARITIES = ("month", "year")
FX_GRANULARITIES = ("day", "month", "year")

MAX_RANGE_DAYS = 3660
DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 120

# Freshness policy — measured against the provider's real publication
# cadence on the *latest available* observation, never on the queried
# window: a complete historical period is "ok", not "stale".
# - Pink Sheet publishes monthly, a few days after month end (~5th).
# - PTAX publishes each business day; weekends and holidays have no
#   bulletin, so a multi-day grace is normal, not a failure.
FRESHNESS_METHOD = "provider_publication_cadence/v1"
PINK_SHEET_PUBLICATION_DAY = 5
FX_STALE_GRACE_DAYS = 4

_FEED_BY_KIND = {KIND_METAL: "metals-monthly", KIND_FX: "fx-daily"}


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
                    "last_run_outcome": entry.get("outcome"),
                    "last_successful_at": entry.get("last_successful_at"),
                    "latest_observation_date": entry.get(
                        "latest_observation_date"
                    ),
                }
        return {
            "last_successful_ingestion_at": latest,
            "feed_ingestion": feed_info,
        }

    def _expected_metal_period(self, today: date) -> date:
        """Latest month the Pink Sheet should have published by ``today``."""
        this_month = date(today.year, today.month, 1)
        lag = 1 if today.day >= PINK_SHEET_PUBLICATION_DAY else 2
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
        if kind == KIND_METAL:
            expected = self._expected_metal_period(today)
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
                    "granularities": list(METAL_GRANULARITIES),
                    "currencies": list(CURRENCIES),
                    "latest_observation_date": inst.get(
                        "latest_observation_date"
                    ),
                    "source_id": inst["source_id"],
                    # Default-deny: only an explicit display_allowed=true
                    # from the producer is selectable — absent/null/invalid
                    # means the producer version predates the rights
                    # contract, which is never a permission.
                    "selectable": inst.get("display_allowed") is True,
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
                    "granularities": list(FX_GRANULARITIES),
                    "currencies": ["BRL"],
                    "latest_observation_date": fx.get(
                        "latest_observation_date"
                    ),
                    "source_id": fx["source_id"],
                    "selectable": fx.get("display_allowed") is True,
                }
            )
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
        )
        return {
            "instruments": instruments,
            "currencies": list(CURRENCIES),
            "granularities": ["day", "month", "year"],
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
