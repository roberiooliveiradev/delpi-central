"""Apply designTokens.partChrome defaults to TV slide blocks on commit.

Fills missing / below-min typography and card chrome for KPI, chart, table, input.
Never overwrites INFORMED block ids (same contract as SlideAutoLayoutService).
"""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)

_KPI_TYPES = frozenset({"kpi_view", "data_kpi"})
_CHART_TYPES = frozenset({"chart_view", "data_chart"})
_TABLE_TYPES = frozenset({"table_view", "data_table"})
_INPUT_TYPES = frozenset({"input"})


def _tokens() -> dict[str, Any]:
    raw = PresentationRecipeService.document().get("designTokens")
    return raw if isinstance(raw, dict) else {}


def _part_chrome() -> dict[str, Any]:
    chrome = _tokens().get("partChrome")
    return chrome if isinstance(chrome, dict) else {}


def _kpi_density(frame: dict[str, Any] | None) -> str:
    """hero | row | grid from frame area (approx)."""
    if not isinstance(frame, dict):
        return "row"
    try:
        w, h = float(frame.get("w", 0)), float(frame.get("h", 0))
    except (TypeError, ValueError):
        return "row"
    area = w * h
    if area >= 2200:
        return "hero"
    if area <= 900:
        return "grid"
    return "row"


def _ensure_dict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    cur = parent.get(key)
    if not isinstance(cur, dict):
        cur = {}
        parent[key] = cur
    return cur


def _ensure_nested_style(parts: dict[str, Any], part_key: str) -> dict[str, Any]:
    part = _ensure_dict(parts, part_key)
    return _ensure_dict(part, "style")


def _set_if_missing_or_below(
    style: dict[str, Any],
    key: str,
    value: Any,
    *,
    min_value: float | None = None,
) -> bool:
    """Set style[key] when absent or numeric value below min. Returns True if changed."""
    cur = style.get(key)
    if cur is None or cur == "":
        style[key] = value
        return True
    if min_value is not None and isinstance(cur, (int, float)) and float(cur) < min_value:
        style[key] = value
        return True
    return False


def _apply_kpi(block: dict[str, Any], chrome: dict[str, Any]) -> bool:
    kpi = chrome.get("kpi") if isinstance(chrome.get("kpi"), dict) else {}
    if not kpi:
        return False
    changed = False
    density = _kpi_density(block.get("frame") if isinstance(block.get("frame"), dict) else None)
    value_defaults = kpi.get("defaultValueFontSize")
    value_mins = kpi.get("valueMinFontSize")
    if not isinstance(value_defaults, dict):
        value_defaults = {}
    if not isinstance(value_mins, dict):
        value_mins = {}

    style = _ensure_dict(block, "style")
    card_fill = kpi.get("cardFill") or "#ffffff"
    if style.get("backgroundColor") in (None, ""):
        style["backgroundColor"] = card_fill
        changed = True
    on_card = kpi.get("valueColor") or "#0f172a"
    if style.get("color") in (None, ""):
        style["color"] = on_card
        changed = True

    parts = _ensure_dict(block, "kpiParts")
    card_style = _ensure_nested_style(parts, "card")
    if _set_if_missing_or_below(card_style, "fill", card_fill):
        changed = True
    if _set_if_missing_or_below(card_style, "backgroundColor", card_fill):
        changed = True
    card_style.setdefault("borderRadius", 16)

    title_style = _ensure_nested_style(parts, "title")
    title_min = float(kpi.get("titleMinFontSize") or 18)
    title_def = int(kpi.get("defaultTitleFontSize") or 22)
    if _set_if_missing_or_below(title_style, "fontSize", title_def, min_value=title_min):
        changed = True
    if title_style.get("color") in (None, ""):
        title_style["color"] = kpi.get("titleColor") or "#475569"
        changed = True

    value_style = _ensure_nested_style(parts, "value")
    value_def = int(value_defaults.get(density) or value_defaults.get("row") or 56)
    value_min = float(value_mins.get(density) or value_mins.get("row") or 40)
    if _set_if_missing_or_below(value_style, "fontSize", value_def, min_value=value_min):
        changed = True
    if value_style.get("color") in (None, ""):
        value_style["color"] = on_card
        changed = True
    # Prefer FitText when frame exists and no explicit typographyMode
    if value_style.get("typographyMode") in (None, ""):
        value_style["typographyMode"] = "auto"
        changed = True

    unit_style = parts.get("unit")
    if isinstance(unit_style, dict) or "unit" in parts:
        ustyle = _ensure_nested_style(parts, "unit")
        unit_min = float(kpi.get("unitMinFontSize") or 16)
        if _set_if_missing_or_below(ustyle, "fontSize", int(unit_min), min_value=unit_min):
            changed = True

    icon_style = _ensure_nested_style(parts, "icon")
    icon_min = float(kpi.get("iconMinSize") or 32)
    icon_def = int(kpi.get("defaultIconSize") or 36)
    if _set_if_missing_or_below(icon_style, "iconSize", icon_def, min_value=icon_min):
        changed = True
    if icon_style.get("color") in (None, ""):
        icon_style["color"] = kpi.get("iconColor") or "#089bdb"
        changed = True

    return changed


def _apply_chart(block: dict[str, Any], chrome: dict[str, Any]) -> bool:
    chart = chrome.get("chart") if isinstance(chrome.get("chart"), dict) else {}
    if not chart:
        return False
    changed = False
    style = _ensure_dict(block, "style")
    fill = chart.get("cardFill") or "#ffffff"
    if style.get("backgroundColor") in (None, ""):
        style["backgroundColor"] = fill
        changed = True
    if style.get("color") in (None, ""):
        style["color"] = chart.get("fg") or "#0f172a"
        changed = True
    opts = _ensure_dict(block, "chartOptions")
    title_min = float(chart.get("titleMinFontSize") or 18)
    title_def = int(chart.get("defaultTitleFontSize") or 22)
    if _set_if_missing_or_below(opts, "titleFontSize", title_def, min_value=title_min):
        changed = True
    legend_min = float(chart.get("legendMinFontSize") or 14)
    if _set_if_missing_or_below(opts, "legendFontSize", int(legend_min), min_value=legend_min):
        changed = True
    axis_min = float(chart.get("axisMinFontSize") or 12)
    if _set_if_missing_or_below(opts, "axisFontSize", int(axis_min), min_value=axis_min):
        changed = True
    return changed


def _apply_table(block: dict[str, Any], chrome: dict[str, Any]) -> bool:
    table = chrome.get("table") if isinstance(chrome.get("table"), dict) else {}
    if not table:
        return False
    changed = False
    style = _ensure_dict(block, "style")
    fill = table.get("cardFill") or "#ffffff"
    if style.get("backgroundColor") in (None, ""):
        style["backgroundColor"] = fill
        changed = True
    if style.get("color") in (None, ""):
        style["color"] = table.get("fg") or "#0f172a"
        changed = True
    opts = _ensure_dict(block, "tableOptions")
    header_min = float(table.get("headerMinFontSize") or 16)
    header_def = int(table.get("defaultHeaderFontSize") or 18)
    if _set_if_missing_or_below(opts, "headerFontSize", header_def, min_value=header_min):
        changed = True
    body_min = float(table.get("bodyMinFontSize") or 14)
    body_def = int(table.get("defaultBodyFontSize") or 16)
    if _set_if_missing_or_below(opts, "bodyFontSize", body_def, min_value=body_min):
        changed = True
    return changed


def _apply_input(block: dict[str, Any], chrome: dict[str, Any]) -> bool:
    inp = chrome.get("input") if isinstance(chrome.get("input"), dict) else {}
    if not inp:
        return False
    changed = False
    style = _ensure_dict(block, "style")
    fill = inp.get("cardFill") or "#ffffff"
    if style.get("backgroundColor") in (None, ""):
        style["backgroundColor"] = fill
        changed = True
    if style.get("color") in (None, ""):
        style["color"] = inp.get("fg") or "#0f172a"
        changed = True
    parts = _ensure_dict(block, "inputParts")
    label_style = _ensure_nested_style(parts, "label")
    label_min = float(inp.get("labelMinFontSize") or 14)
    label_def = int(inp.get("defaultLabelFontSize") or 16)
    if _set_if_missing_or_below(label_style, "fontSize", label_def, min_value=label_min):
        changed = True
    control_style = _ensure_nested_style(parts, "control")
    control_min = float(inp.get("controlMinFontSize") or 16)
    control_def = int(inp.get("defaultControlFontSize") or 18)
    if _set_if_missing_or_below(control_style, "fontSize", control_def, min_value=control_min):
        changed = True
    return changed


class SlidePartChromeService:
    """Owner of missing part chrome / typography defaults on TV slides."""

    @classmethod
    def apply_missing_defaults(
        cls,
        native_config: dict[str, Any],
        *,
        informed_block_ids: set[str] | None = None,
    ) -> bool:
        """Mutate cfg in place. Returns True if any block changed."""
        blocks = native_config.get("blocks")
        if not isinstance(blocks, list):
            return False
        informed = informed_block_ids or set()
        chrome = _part_chrome()
        if not chrome:
            return False
        changed_any = False
        for block in blocks:
            if not isinstance(block, dict):
                continue
            bid = str(block.get("id") or "")
            if bid and bid in informed:
                continue
            btype = str(block.get("type") or "")
            if btype in _KPI_TYPES:
                changed_any = _apply_kpi(block, chrome) or changed_any
            elif btype in _CHART_TYPES:
                changed_any = _apply_chart(block, chrome) or changed_any
            elif btype in _TABLE_TYPES:
                changed_any = _apply_table(block, chrome) or changed_any
            elif btype in _INPUT_TYPES:
                changed_any = _apply_input(block, chrome) or changed_any
        return changed_any
