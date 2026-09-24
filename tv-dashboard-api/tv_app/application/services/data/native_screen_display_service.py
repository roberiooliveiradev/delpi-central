"""Materialize display* strings for legacy NativeScreens (FE-BE-002 / G18).

Reuses DisplayFormatService — no second formatter. Stock screens (OEE/OTD/PPM/stock/…)
bypass comunicado enrich; this closes the client formatDisplayValue path.
"""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.display_format_service import DisplayFormatService

_PCT = {"category": "percent", "decimalPlaces": 1}
_NUM = {"category": "number", "decimalPlaces": 2}
_CURRENCY = {"category": "currency", "currency": "BRL", "decimalPlaces": 2}


def apply_native_screen_display(payload: dict[str, Any], screen_key: str) -> dict[str, Any]:
    """Stamp ready-to-paint display fields on a native screen data payload."""
    if not isinstance(payload, dict) or payload.get("error"):
        return payload
    if screen_key == "custom_message":
        # Already enriched via ComunicadoEnrichmentService.
        return payload

    out = dict(payload)
    fmt = DisplayFormatService.format_value

    def _pct(key: str, display_key: str) -> None:
        if key in out and out.get(key) is not None:
            out[display_key] = fmt(out.get(key), _PCT)

    def _num(key: str, display_key: str, *, currency: bool = False) -> None:
        if key in out and out.get(key) is not None:
            out[display_key] = fmt(out.get(key), _CURRENCY if currency else _NUM)

    if screen_key == "production_oee_overview":
        _pct("oeePct", "oeePctDisplay")
        _pct("targetPct", "targetPctDisplay")
    elif screen_key == "production_otd_summary":
        _pct("otdPct", "otdPctDisplay")
        _pct("targetPct", "targetPctDisplay")
    elif screen_key == "quality_ppm_summary":
        _num("ppmValue", "ppmValueDisplay")
        _pct("targetPct", "targetPctDisplay")
    elif screen_key == "supplies_stock_value":
        _num("stockValue", "stockValueDisplay", currency=True)
    elif screen_key == "supplies_stock_alert":
        items = out.get("items")
        if isinstance(items, list):
            next_items: list[Any] = []
            for item in items:
                if not isinstance(item, dict):
                    next_items.append(item)
                    continue
                next_item = dict(item)
                if next_item.get("stockValue") is not None:
                    next_item["stockValueDisplay"] = fmt(next_item.get("stockValue"), _CURRENCY)
                next_items.append(next_item)
            out["items"] = next_items
    elif screen_key == "strategic_indicators_hero":
        _num("igd", "igdDisplay")

    series = out.get("seriesPoints")
    if isinstance(series, list):
        next_series: list[Any] = []
        for point in series:
            if not isinstance(point, dict):
                next_series.append(point)
                continue
            next_point = dict(point)
            if "value" in next_point and next_point.get("value") is not None:
                next_point["displayValue"] = fmt(next_point.get("value"), _NUM)
            if next_point.get("label") is not None and next_point.get("label") != "":
                next_point["displayLabel"] = str(next_point.get("label"))
            next_series.append(next_point)
        out["seriesPoints"] = next_series

    out["serverDisplayApplied"] = True
    return out
