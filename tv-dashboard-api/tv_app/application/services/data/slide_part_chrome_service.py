"""Apply designTokens.partChrome defaults + hierarchy rebalance on TV slides.

Fills missing / below-min typography and card chrome for KPI, chart, table, input.
Rebalances internal parts when a primary size (value/title/body/control/frame)
was scaled without dependents — for every typed component family, including
composed groupId clusters (shape+heading+text).

Defaults fill still skips INFORMED block ids; hierarchy rebalance always runs.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Mapping

from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)

_KPI_TYPES = frozenset({"kpi_view", "data_kpi"})
_CHART_TYPES = frozenset({"chart_view", "data_chart"})
_TABLE_TYPES = frozenset({"table_view", "data_table", "canvas_table"})
_INPUT_TYPES = frozenset({"input"})
_TEXT_BOUND_TYPES = frozenset({"heading", "text", "shape"})


def _tokens() -> dict[str, Any]:
    raw = PresentationRecipeService.document().get("designTokens")
    return raw if isinstance(raw, dict) else {}


def _part_chrome() -> dict[str, Any]:
    chrome = _tokens().get("partChrome")
    return chrome if isinstance(chrome, dict) else {}


def _type_scale() -> dict[str, Any]:
    raw = _tokens().get("typeScale")
    return raw if isinstance(raw, dict) else {}


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


def _frame_area(frame: Any) -> float:
    if not isinstance(frame, dict):
        return 0.0
    try:
        return max(0.0, float(frame.get("w", 0)) * float(frame.get("h", 0)))
    except (TypeError, ValueError):
        return 0.0


def _frame_scale(frame: Any, *, ref_area: float = 1080.0) -> float:
    """≥1 scale from frame area vs reference row card (~30×36). Caps at 2.5."""
    area = _frame_area(frame)
    if area <= 0 or ref_area <= 0:
        return 1.0
    scale = (area / ref_area) ** 0.5
    if scale < 1.0:
        return 1.0
    return min(2.5, scale)


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


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _density_map_int(raw: Any, density: str, fallback: int) -> int:
    if isinstance(raw, dict):
        try:
            return int(raw.get(density) or raw.get("row") or fallback)
        except (TypeError, ValueError):
            return fallback
    try:
        return int(raw) if raw is not None else fallback
    except (TypeError, ValueError):
        return fallback


def _bump_to_at_least(container: dict[str, Any], key: str, target: int) -> bool:
    """Raise numeric container[key] to target when missing or below. Never shrinks."""
    if target <= 0:
        return False
    cur = _as_float(container.get(key))
    if cur is None:
        container[key] = target
        return True
    if cur + 0.5 < float(target):
        container[key] = target
        return True
    return False


def _target_from_primary(
    primary: float,
    *,
    ratio: float,
    absolute_min: float,
    density_default: int = 0,
    cap_ratio: float | None = None,
    frame_scale: float = 1.0,
) -> int:
    scaled_default = int(round(density_default * max(1.0, frame_scale))) if density_default else 0
    target = max(int(absolute_min), scaled_default, int(round(primary * ratio)))
    if cap_ratio is not None and cap_ratio > 0:
        target = min(target, max(int(absolute_min), int(round(primary * cap_ratio))))
    return target


def _nested_font(parts: dict[str, Any], part_key: str) -> float | None:
    part = parts.get(part_key)
    if not isinstance(part, dict):
        return None
    style = part.get("style")
    if not isinstance(style, dict):
        return None
    return _as_float(style.get("fontSize"))


def _kpi_value_font_size(block: dict[str, Any]) -> float | None:
    parts = block.get("kpiParts") if isinstance(block.get("kpiParts"), dict) else {}
    size = _nested_font(parts, "value")
    if size is not None:
        return size
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    return _as_float(style.get("fontSize"))


def _rebalance_kpi_hierarchy(block: dict[str, Any], chrome: dict[str, Any]) -> bool:
    kpi = chrome.get("kpi") if isinstance(chrome.get("kpi"), dict) else {}
    if not kpi:
        return False
    existing_parts = block.get("kpiParts")
    value_fs = _kpi_value_font_size(block)
    # Do not invent kpiParts on empty INFORMED blocks — only rebalance when something exists.
    if value_fs is None and not isinstance(existing_parts, dict):
        return False
    frame = block.get("frame") if isinstance(block.get("frame"), dict) else None
    density = _kpi_density(frame)
    fscale = _frame_scale(frame)

    if value_fs is None or value_fs <= 0:
        value_defaults = kpi.get("defaultValueFontSize")
        if not isinstance(value_defaults, dict):
            value_defaults = {}
        value_fs = float(value_defaults.get(density) or value_defaults.get("row") or 56) * fscale

    title_by_density = _density_map_int(
        kpi.get("defaultTitleFontSizeByDensity") or kpi.get("defaultTitleFontSize"),
        density,
        22,
    )
    icon_by_density = _density_map_int(
        kpi.get("defaultIconSizeByDensity") or kpi.get("defaultIconSize"),
        density,
        36,
    )

    target_title = _target_from_primary(
        value_fs,
        ratio=float(kpi.get("titleToValueMinRatio") or 0.35),
        absolute_min=float(kpi.get("titleMinFontSize") or 18),
        density_default=title_by_density,
        cap_ratio=0.5,
        frame_scale=fscale,
    )
    target_icon = _target_from_primary(
        value_fs,
        ratio=float(kpi.get("iconToValueMinRatio") or 0.55),
        absolute_min=float(kpi.get("iconMinSize") or 32),
        density_default=icon_by_density,
        frame_scale=fscale,
    )
    target_unit = _target_from_primary(
        value_fs,
        ratio=float(kpi.get("unitToValueMinRatio") or 0.22),
        absolute_min=float(kpi.get("unitMinFontSize") or 16),
        frame_scale=fscale,
    )

    parts = _ensure_dict(block, "kpiParts")
    changed = False
    title_style = _ensure_nested_style(parts, "title")
    if _bump_to_at_least(title_style, "fontSize", target_title):
        changed = True
    if title_style.get("color") in (None, ""):
        title_style["color"] = kpi.get("titleColor") or "#475569"
        changed = True

    icon_style = _ensure_nested_style(parts, "icon")
    if _bump_to_at_least(icon_style, "iconSize", target_icon):
        changed = True
    if icon_style.get("color") in (None, ""):
        icon_style["color"] = kpi.get("iconColor") or "#089bdb"
        changed = True

    if isinstance(parts.get("unit"), dict) or "unit" in parts:
        unit_style = _ensure_nested_style(parts, "unit")
        if _bump_to_at_least(unit_style, "fontSize", target_unit):
            changed = True

    return changed


def _chart_title_font_size(block: dict[str, Any]) -> float | None:
    opts = block.get("chartOptions") if isinstance(block.get("chartOptions"), dict) else {}
    size = _as_float(opts.get("titleFontSize"))
    if size is not None:
        return size
    parts = block.get("chartParts") if isinstance(block.get("chartParts"), dict) else {}
    title = parts.get("title") if isinstance(parts.get("title"), dict) else {}
    style = title.get("style") if isinstance(title.get("style"), dict) else {}
    return _as_float(style.get("fontSize"))


def _rebalance_chart_hierarchy(block: dict[str, Any], chrome: dict[str, Any]) -> bool:
    chart = chrome.get("chart") if isinstance(chrome.get("chart"), dict) else {}
    if not chart:
        return False
    opts_existing = block.get("chartOptions")
    parts_existing = block.get("chartParts")
    title_fs = _chart_title_font_size(block)
    if title_fs is None and not isinstance(opts_existing, dict) and not isinstance(parts_existing, dict):
        return False
    frame = block.get("frame") if isinstance(block.get("frame"), dict) else None
    fscale = _frame_scale(frame, ref_area=2400.0)
    if title_fs is None or title_fs <= 0:
        title_fs = float(chart.get("defaultTitleFontSize") or 22) * fscale

    legend_min = float(chart.get("legendMinFontSize") or 14)
    axis_min = float(chart.get("axisMinFontSize") or 12)
    target_legend = _target_from_primary(
        title_fs,
        ratio=float(chart.get("legendToTitleMinRatio") or 0.7),
        absolute_min=legend_min,
        density_default=int(legend_min),
        frame_scale=fscale,
    )
    target_axis = _target_from_primary(
        title_fs,
        ratio=float(chart.get("axisToTitleMinRatio") or 0.6),
        absolute_min=axis_min,
        density_default=int(axis_min),
        frame_scale=fscale,
    )
    target_title = _target_from_primary(
        title_fs,
        ratio=1.0,
        absolute_min=float(chart.get("titleMinFontSize") or 18),
        density_default=int(chart.get("defaultTitleFontSize") or 22),
        frame_scale=fscale,
    )

    changed = False
    opts = _ensure_dict(block, "chartOptions")
    if _bump_to_at_least(opts, "titleFontSize", target_title):
        changed = True
    if _bump_to_at_least(opts, "legendFontSize", target_legend):
        changed = True
    if _bump_to_at_least(opts, "axisFontSize", target_axis):
        changed = True

    # Keep chartParts.* in sync when present (editor chrome path).
    parts = block.get("chartParts")
    if isinstance(parts, dict):
        for part_key, target, size_key in (
            ("title", target_title, "fontSize"),
            ("legend", target_legend, "fontSize"),
            ("xAxis", target_axis, "fontSize"),
            ("yAxis", target_axis, "fontSize"),
        ):
            if part_key not in parts and part_key not in ("title", "legend"):
                continue
            style = _ensure_nested_style(parts, part_key)
            if _bump_to_at_least(style, size_key, target):
                changed = True

    return changed


def _rebalance_table_hierarchy(block: dict[str, Any], chrome: dict[str, Any]) -> bool:
    table = chrome.get("table") if isinstance(chrome.get("table"), dict) else {}
    if not table:
        return False
    frame = block.get("frame") if isinstance(block.get("frame"), dict) else None
    fscale = _frame_scale(frame, ref_area=2400.0)
    opts = _ensure_dict(block, "tableOptions")
    body_fs = _as_float(opts.get("bodyFontSize")) or _as_float(opts.get("fontSize"))
    header_fs = _as_float(opts.get("headerFontSize"))
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    if body_fs is None:
        body_fs = _as_float(style.get("fontSize"))
    if body_fs is None or body_fs <= 0:
        body_fs = float(table.get("defaultBodyFontSize") or 16) * fscale
    if header_fs is None or header_fs <= 0:
        header_fs = float(table.get("defaultHeaderFontSize") or 18) * fscale

    # Primary = max(body, header) so either bump drives the other.
    primary = max(body_fs, header_fs)
    body_ratio = float(table.get("bodyToHeaderMinRatio") or 0.85)
    header_ratio = float(table.get("headerToBodyMinRatio") or 1.12)

    target_body = _target_from_primary(
        primary if primary == header_fs else body_fs,
        ratio=body_ratio if primary == header_fs else 1.0,
        absolute_min=float(table.get("bodyMinFontSize") or 14),
        density_default=int(table.get("defaultBodyFontSize") or 16),
        frame_scale=fscale,
    )
    target_header = _target_from_primary(
        primary if primary == body_fs else header_fs,
        ratio=header_ratio if primary == body_fs else 1.0,
        absolute_min=float(table.get("headerMinFontSize") or 16),
        density_default=int(table.get("defaultHeaderFontSize") or 18),
        frame_scale=fscale,
    )
    # Ensure header ≥ body when both set from same primary.
    target_header = max(target_header, target_body)

    changed = False
    if _bump_to_at_least(opts, "bodyFontSize", target_body):
        changed = True
    if _bump_to_at_least(opts, "headerFontSize", target_header):
        changed = True
    if _as_float(opts.get("fontSize")) is not None:
        if _bump_to_at_least(opts, "fontSize", target_body):
            changed = True

    # tableParts header/body text when present
    parts = block.get("tableParts")
    if isinstance(parts, dict):
        for part_key, target in (("header", target_header), ("body", target_body), ("cell", target_body)):
            if part_key not in parts:
                continue
            style_p = _ensure_nested_style(parts, part_key)
            if _bump_to_at_least(style_p, "fontSize", target):
                changed = True

    return changed


def _rebalance_input_hierarchy(block: dict[str, Any], chrome: dict[str, Any]) -> bool:
    inp = chrome.get("input") if isinstance(chrome.get("input"), dict) else {}
    if not inp:
        return False
    frame = block.get("frame") if isinstance(block.get("frame"), dict) else None
    fscale = _frame_scale(frame, ref_area=600.0)
    parts = _ensure_dict(block, "inputParts")
    control_fs = _nested_font(parts, "control")
    label_fs = _nested_font(parts, "label")
    if control_fs is None or control_fs <= 0:
        control_fs = float(inp.get("defaultControlFontSize") or 18) * fscale
    if label_fs is None or label_fs <= 0:
        label_fs = float(inp.get("defaultLabelFontSize") or 16) * fscale

    primary = max(control_fs, label_fs)
    target_control = _target_from_primary(
        primary,
        ratio=float(inp.get("controlToLabelMinRatio") or 1.1) if primary == label_fs else 1.0,
        absolute_min=float(inp.get("controlMinFontSize") or 16),
        density_default=int(inp.get("defaultControlFontSize") or 18),
        frame_scale=fscale,
    )
    target_label = _target_from_primary(
        primary,
        ratio=float(inp.get("labelToControlMinRatio") or 0.85) if primary == control_fs else 1.0,
        absolute_min=float(inp.get("labelMinFontSize") or 14),
        density_default=int(inp.get("defaultLabelFontSize") or 16),
        frame_scale=fscale,
    )
    target_icon = _target_from_primary(
        target_control,
        ratio=float(inp.get("iconToControlMinRatio") or 1.15),
        absolute_min=float(inp.get("iconMinSize") or 18),
        density_default=int(inp.get("defaultIconSize") or 22),
        frame_scale=fscale,
    )

    changed = False
    control_style = _ensure_nested_style(parts, "control")
    if _bump_to_at_least(control_style, "fontSize", target_control):
        changed = True
    label_style = _ensure_nested_style(parts, "label")
    if _bump_to_at_least(label_style, "fontSize", target_label):
        changed = True
    if isinstance(parts.get("icon"), dict) or "icon" in parts:
        icon_style = _ensure_nested_style(parts, "icon")
        if _bump_to_at_least(icon_style, "iconSize", target_icon):
            changed = True
        elif _bump_to_at_least(icon_style, "fontSize", target_icon):
            changed = True

    return changed


def _rebalance_text_bound_hierarchy(block: dict[str, Any], chrome: dict[str, Any]) -> bool:
    """heading/text/shape: absolute floor always; density/frame floor when data-bound."""
    text_chrome = chrome.get("textBound") if isinstance(chrome.get("textBound"), dict) else {}
    scale = _type_scale()
    style = _ensure_dict(block, "style")
    absolute_min = int(text_chrome.get("absoluteMinFontSize") or 16)
    cur = _as_float(style.get("fontSize"))
    has_data = bool(block.get("textProjection") or block.get("dataSourceId"))

    if not has_data:
        # Decorative / static copy: only rescue illegible sizes — never force hero scale.
        if cur is None:
            btype = str(block.get("type") or "")
            if btype == "heading":
                fallback = int(scale.get("title") or 28)
            elif btype == "shape":
                fallback = int(text_chrome.get("shapeMinFontSize") or scale.get("body") or 22)
            else:
                fallback = int(scale.get("body") or 22)
            return _bump_to_at_least(style, "fontSize", max(absolute_min, fallback))
        return _bump_to_at_least(style, "fontSize", absolute_min)

    btype = str(block.get("type") or "")
    frame = block.get("frame") if isinstance(block.get("frame"), dict) else None
    density = _kpi_density(frame)
    fscale = _frame_scale(frame)
    if btype == "heading":
        base = int(scale.get("title") or text_chrome.get("headingMinFontSize") or 28)
    elif btype == "shape":
        base = int(text_chrome.get("shapeMinFontSize") or scale.get("display") or 36)
    else:
        base = int(scale.get("body") or text_chrome.get("textMinFontSize") or 22)
    density_boost = {"hero": 1.25, "row": 1.0, "grid": 0.9}.get(density, 1.0)
    target = max(absolute_min, int(round(base * density_boost * max(1.0, fscale))))
    return _bump_to_at_least(style, "fontSize", target)


def _block_display_font(block: dict[str, Any]) -> float | None:
    btype = str(block.get("type") or "")
    if btype in _KPI_TYPES:
        return _kpi_value_font_size(block)
    if btype in _CHART_TYPES:
        return _chart_title_font_size(block)
    if btype in _TABLE_TYPES:
        opts = block.get("tableOptions") if isinstance(block.get("tableOptions"), dict) else {}
        return _as_float(opts.get("bodyFontSize")) or _as_float(opts.get("headerFontSize"))
    if btype in _INPUT_TYPES:
        parts = block.get("inputParts") if isinstance(block.get("inputParts"), dict) else {}
        return _nested_font(parts, "control") or _nested_font(parts, "label")
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    return _as_float(style.get("fontSize"))


def _rebalance_composed_groups(
    blocks: list[Any],
    chrome: dict[str, Any],
) -> bool:
    """Within the same groupId, primary font drives sibling heading/text/shape sizes."""
    composed = chrome.get("composed") if isinstance(chrome.get("composed"), dict) else {}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for block in blocks:
        if not isinstance(block, dict):
            continue
        gid = str(block.get("groupId") or "").strip()
        if not gid:
            continue
        groups[gid].append(block)
    if not groups:
        return False

    sibling_ratio = float(composed.get("siblingToPrimaryMinRatio") or 0.4)
    heading_ratio = float(composed.get("headingToPrimaryMinRatio") or 0.45)
    label_ratio = float(composed.get("labelToPrimaryMinRatio") or 0.28)
    absolute_min = float(composed.get("absoluteMinFontSize") or 16)

    changed_any = False
    for members in groups.values():
        primary = 0.0
        for block in members:
            size = _block_display_font(block)
            if size is not None and size > primary:
                primary = size
        if primary <= 0:
            continue
        for block in members:
            btype = str(block.get("type") or "")
            if btype not in _TEXT_BOUND_TYPES:
                continue
            if btype == "heading":
                ratio = heading_ratio
            elif btype == "text" and not block.get("textProjection"):
                ratio = label_ratio
            else:
                ratio = sibling_ratio
            # textProjection / shape value should stay closer to primary
            if block.get("textProjection") or (
                btype == "shape" and _as_float((block.get("style") or {}).get("fontSize"))
            ):
                if btype != "heading":
                    ratio = max(ratio, float(composed.get("valueSiblingMinRatio") or 0.85))
            target = max(int(absolute_min), int(round(primary * ratio)))
            # Don't enlarge the primary itself beyond itself
            cur = _block_display_font(block)
            if cur is not None and cur + 0.5 >= primary:
                continue
            style = _ensure_dict(block, "style")
            if _bump_to_at_least(style, "fontSize", target):
                changed_any = True
    return changed_any


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
    title_def = _density_map_int(
        kpi.get("defaultTitleFontSizeByDensity") or kpi.get("defaultTitleFontSize"),
        density,
        22,
    )
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
    if value_style.get("typographyMode") in (None, ""):
        value_style["typographyMode"] = "auto"
        changed = True

    if isinstance(parts.get("unit"), dict) or "unit" in parts:
        ustyle = _ensure_nested_style(parts, "unit")
        unit_min = float(kpi.get("unitMinFontSize") or 16)
        if _set_if_missing_or_below(ustyle, "fontSize", int(unit_min), min_value=unit_min):
            changed = True

    icon_style = _ensure_nested_style(parts, "icon")
    icon_min = float(kpi.get("iconMinSize") or 32)
    icon_def = _density_map_int(
        kpi.get("defaultIconSizeByDensity") or kpi.get("defaultIconSize"),
        density,
        36,
    )
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
    if str(block.get("type") or "") == "canvas_table":
        # canvas_table uses cell runs; hierarchy rebalance covers options when present.
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


_EMPHASIS_SCALE = {"low": 0.85, "medium": 1.0, "high": 1.15}
_DENSITY_PADDING = {"compact": 8, "regular": None, "comfortable": 20}


def _apply_semantic_role(block: dict[str, Any], tokens: Mapping[str, Any] | dict[str, Any]) -> bool:
    """Resolve role/variant/surface/emphasis/density onto token chrome. Ignores free CSS."""
    role = str(block.get("role") or "").strip()
    profiles = tokens.get("roles") if isinstance(tokens.get("roles"), dict) else {}
    profile = profiles.get(role) if isinstance(profiles, dict) else None
    if not isinstance(profile, dict):
        return False
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    block["style"] = style
    changed = False
    font_size = profile.get("fontSize")
    variant = str(block.get("variant") or "").strip()
    if variant == "hero":
        scale = tokens.get("typeScale") if isinstance(tokens.get("typeScale"), dict) else {}
        hero = scale.get("kpiHero")
        if isinstance(hero, (int, float)):
            font_size = hero
    emphasis = str(block.get("emphasis") or "medium").strip() or "medium"
    if isinstance(font_size, (int, float)) and "fontSize" not in style:
        scaled = float(font_size) * _EMPHASIS_SCALE.get(emphasis, 1.0)
        style["fontSize"] = int(round(scaled))
        changed = True
    surface = str(block.get("surface") or "card").strip() or "card"
    if "backgroundColor" not in style and profile.get("fill"):
        style["backgroundColor"] = "#0f172a" if surface == "inverse" else profile["fill"]
        changed = True
    if "borderRadius" not in style and profile.get("radius") is not None:
        style["borderRadius"] = profile["radius"]
        changed = True
    density = str(block.get("density") or "regular").strip() or "regular"
    padding = _DENSITY_PADDING.get(density, None)
    if padding is None:
        padding = profile.get("padding")
    if "padding" not in style and padding is not None:
        style["padding"] = padding
        changed = True
    return changed


class SlidePartChromeService:
    """Owner of missing part chrome / typography hierarchy on TV slides."""

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
        tokens = _tokens()
        for block in blocks:
            if not isinstance(block, dict):
                continue
            bid = str(block.get("id") or "")
            if not (bid and bid in informed):
                changed_any = _apply_semantic_role(block, tokens) or changed_any
            if not isinstance(block, dict):
                continue
            bid = str(block.get("id") or "")
            skip_fill = bool(bid and bid in informed)
            btype = str(block.get("type") or "")
            if btype in _KPI_TYPES:
                if not skip_fill:
                    changed_any = _apply_kpi(block, chrome) or changed_any
                changed_any = _rebalance_kpi_hierarchy(block, chrome) or changed_any
            elif btype in _CHART_TYPES:
                if not skip_fill:
                    changed_any = _apply_chart(block, chrome) or changed_any
                changed_any = _rebalance_chart_hierarchy(block, chrome) or changed_any
            elif btype in _TABLE_TYPES:
                if not skip_fill:
                    changed_any = _apply_table(block, chrome) or changed_any
                changed_any = _rebalance_table_hierarchy(block, chrome) or changed_any
            elif btype in _INPUT_TYPES:
                if not skip_fill:
                    changed_any = _apply_input(block, chrome) or changed_any
                changed_any = _rebalance_input_hierarchy(block, chrome) or changed_any
            elif btype in _TEXT_BOUND_TYPES:
                changed_any = _rebalance_text_bound_hierarchy(block, chrome) or changed_any

        changed_any = _rebalance_composed_groups(blocks, chrome) or changed_any
        return changed_any
