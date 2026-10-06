"""Deterministic layout quality gates for TV slides (geometry / density / contrast)."""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)

# Owner contrast floor for text over slide background (design audit gate).
# Shared with SafeAutoFixService so detection and correction use the same
# threshold — a single canonical value, never duplicated literals.
CONTRAST_MIN_RATIO = 2.5

# brandThemeKey → designTokens.brand.modes key. Only the alias table is local;
# the colors themselves come from the canonical owner source
# (PresentationRecipeService.designTokens().brand.modes), which mirrors the
# tv-dashboard-presentation delpiBrandTheme.json contract.
_THEME_MODE_ALIASES: dict[str, str] = {
    "delpi-dark": "dark",
    "delpi": "dark",
    "dark": "dark",
    "delpi-light": "light",
    "light": "light",
}

_KPI_TYPES = frozenset({"kpi_view", "data_kpi"})
_DATA_VISUAL_TYPES = frozenset(
    {
        "kpi_view",
        "data_kpi",
        "chart_view",
        "data_chart",
        "table_view",
        "data_table",
    }
)
_DECORATIVE_TYPES = frozenset({"shape", "image", "video"})


def _frame(block: Mapping[str, Any]) -> dict[str, float] | None:
    raw = block.get("frame")
    if not isinstance(raw, dict):
        return None
    try:
        return {
            "x": float(raw.get("x", 0)),
            "y": float(raw.get("y", 0)),
            "w": float(raw.get("w", 0)),
            "h": float(raw.get("h", 0)),
        }
    except (TypeError, ValueError):
        return None


def _invades_safe_area(frame: Mapping[str, float], margin: float) -> bool:
    right_limit = 100.0 - margin
    return (
        frame["x"] < margin - 0.5
        or frame["y"] < margin - 0.5
        or frame["x"] + frame["w"] > right_limit + 0.5
        or frame["y"] + frame["h"] > right_limit + 0.5
    )


def _overlap_area(a: Mapping[str, float], b: Mapping[str, float]) -> float:
    ax2, ay2 = a["x"] + a["w"], a["y"] + a["h"]
    bx2, by2 = b["x"] + b["w"], b["y"] + b["h"]
    ix1, iy1 = max(a["x"], b["x"]), max(a["y"], b["y"])
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    return (ix2 - ix1) * (iy2 - iy1)


def _parse_hex(color: Any) -> tuple[int, int, int] | None:
    if not isinstance(color, str):
        return None
    raw = color.strip().lstrip("#")
    if len(raw) == 3:
        raw = "".join(ch * 2 for ch in raw)
    if len(raw) != 6:
        return None
    try:
        return int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16)
    except ValueError:
        return None


def _luminance(rgb: tuple[int, int, int]) -> float:
    def channel(c: int) -> float:
        x = c / 255.0
        return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(fg: str, bg: str) -> float | None:
    a = _parse_hex(fg)
    b = _parse_hex(bg)
    if not a or not b:
        return None
    l1, l2 = _luminance(a), _luminance(b)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _theme_bg_colors(theme_key: str) -> list[str]:
    """Brand theme → canonical background endpoint colors.

    Resolves the mode via ``designTokens.brand.modes`` (owner source mirroring
    delpiBrandTheme.json). Returns every background endpoint the theme can
    render (gradient ``from``/``to`` + ``bgSolid``); ``[]`` when the theme is
    unknown — callers must NOT guess.
    """
    from tv_app.application.services.data.presentation_recipe_service import (
        PresentationRecipeService,
    )

    mode_key = _THEME_MODE_ALIASES.get(str(theme_key or "").strip().lower())
    if not mode_key:
        return []
    tokens = PresentationRecipeService.document().get("designTokens")
    modes = tokens.get("brand") if isinstance(tokens, dict) else None
    modes = modes.get("modes") if isinstance(modes, dict) else None
    mode = modes.get(mode_key) if isinstance(modes, dict) else None
    if not isinstance(mode, dict):
        return []
    colors: list[str] = []
    for key in ("bgFrom", "bgTo", "bgSolid"):
        value = mode.get(key)
        if isinstance(value, str) and value not in colors:
            colors.append(value)
    return colors


def _slide_bg_colors(cfg: Mapping[str, Any]) -> list[str]:
    """All background endpoint colors a slide may render.

    Explicit background wins over brand theme. Gradients yield BOTH endpoints:
    a contrast check against a single endpoint is unsafe for text overlapping
    the other end. Image/complex/unknown backgrounds yield ``[]`` — detection
    and correction must stay fail-closed rather than guess.
    """
    bg = cfg.get("background")
    if isinstance(bg, dict):
        if bg.get("type") == "color" and isinstance(bg.get("value"), str):
            return [str(bg["value"])]
        if bg.get("type") == "gradient":
            colors = [
                str(bg[key])
                for key in ("from", "to")
                if isinstance(bg.get(key), str)
            ]
            return colors
        return []
    return _theme_bg_colors(str(cfg.get("brandThemeKey") or ""))


def _slide_bg_color(cfg: Mapping[str, Any]) -> str | None:
    colors = _slide_bg_colors(cfg)
    return colors[0] if colors else None


def effective_slide_bg(cfg: Mapping[str, Any]) -> str | None:
    """Representative effective slide background color for contrast checks.

    Explicit background (color/gradient) wins; brand theme keys resolve to
    their canonical endpoint colors. ``None`` means the background cannot
    be determined safely — callers must NOT guess. Multi-endpoint
    backgrounds must use ``_slide_bg_colors`` for the full safety check.
    """
    return _slide_bg_color(cfg)


def _parseable_bg_colors(cfg: Mapping[str, Any]) -> list[str]:
    return [c for c in _slide_bg_colors(cfg) if _parse_hex(c)]


def safe_contrast_color(
    cfg: Mapping[str, Any], *, tokens: Mapping[str, Any] | None = None
) -> str | None:
    """Deterministic compliant text color for the slide's effective bg.

    Picks the ``fg`` of the designTokens.minContrastPairs entry whose ``bg``
    is luminance-closest to the effective background, but only when that fg
    actually satisfies CONTRAST_MIN_RATIO against EVERY background endpoint
    the slide can render (gradient ``from``/``to`` included). ``None`` when
    the background is unknown or no owner-approved pair is provably safe —
    callers must surface the issue instead of guessing.
    """
    colors = _parseable_bg_colors(cfg)
    if not colors:
        return None
    pairs = (tokens or SlideLayoutQualityService.design_tokens()).get(
        "minContrastPairs"
    )
    if not isinstance(pairs, list):
        return None
    bg_lum = sum(_luminance(_parse_hex(c)) for c in colors) / len(colors)

    def _bg_distance(pair: Mapping[str, Any]) -> float:
        rgb = _parse_hex(pair.get("bg"))
        return abs(_luminance(rgb) - bg_lum) if rgb else 1.0

    ordered = sorted(
        (p for p in pairs if isinstance(p, Mapping)),
        key=_bg_distance,
    )
    for pair in ordered:
        fg = str(pair.get("fg") or "")
        ratios = [_contrast_ratio(fg, bg) for bg in colors]
        if ratios and all(
            ratio is not None and ratio >= CONTRAST_MIN_RATIO for ratio in ratios
        ):
            return fg
    return None


def _block_fg(block: Mapping[str, Any]) -> str | None:
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    color = style.get("color")
    return str(color) if isinstance(color, str) else None


class SlideLayoutQualityService:
    """Owner of visual/layout issues that block false VERIFIED."""

    @classmethod
    def design_tokens(cls) -> dict[str, Any]:
        tokens = PresentationRecipeService.document().get("designTokens")
        return tokens if isinstance(tokens, dict) else {}

    @classmethod
    def collect_native_layout_issues(cls, native_config: Mapping[str, Any] | None) -> list[str]:
        if not isinstance(native_config, dict):
            return []
        blocks = native_config.get("blocks")
        if not isinstance(blocks, list):
            return []
        tokens = cls.design_tokens()
        max_signals = int(tokens.get("maxPrimarySignalsPerSlide") or 4)
        overlap_threshold = float(tokens.get("overlapAreaThresholdPct") or 8)
        widescreen = float(tokens.get("widescreenCoverageThresholdPct") or 90)
        safe_margin = float(tokens.get("safeMargin") or 0)
        issues: list[str] = []

        frames: list[tuple[dict[str, Any], dict[str, float]]] = []
        kpi_count = 0
        for block in blocks:
            if not isinstance(block, dict):
                continue
            btype = str(block.get("type") or "")
            if btype in _KPI_TYPES:
                kpi_count += 1
            fr = _frame(block)
            if not fr:
                continue
            if fr["w"] <= 0 or fr["h"] <= 0:
                issues.append(f"block_frame_non_positive:{block.get('id') or btype}")
                continue
            if (
                fr["x"] < -0.5
                or fr["y"] < -0.5
                or fr["x"] + fr["w"] > 100.5
                or fr["y"] + fr["h"] > 100.5
            ):
                issues.append(f"block_frame_overflow:{block.get('id') or btype}")
            if btype not in _DECORATIVE_TYPES:
                frames.append((block, fr))
                if safe_margin > 0 and _invades_safe_area(fr, safe_margin):
                    issues.append(f"safe_area_violation:{block.get('id') or btype}")

        if kpi_count > max_signals:
            issues.append(f"kpi_density_exceeded:{kpi_count}>{max_signals}")

        # Overlap between non-decorative blocks
        for i in range(len(frames)):
            for j in range(i + 1, len(frames)):
                a_block, a = frames[i]
                b_block, b = frames[j]
                area = _overlap_area(a, b)
                if area <= 0:
                    continue
                min_area = min(a["w"] * a["h"], b["w"] * b["h"]) or 1.0
                pct = 100.0 * area / min_area
                if pct >= overlap_threshold:
                    issues.append(
                        "block_overlap:"
                        f"{a_block.get('id') or a_block.get('type')}"
                        f"~{b_block.get('id') or b_block.get('type')}"
                        f":{pct:.0f}pct"
                    )

        # Anti widescreen-only data visual
        data_visuals = [
            (b, fr)
            for b, fr in frames
            if str(b.get("type") or "") in _DATA_VISUAL_TYPES
        ]
        if len(data_visuals) == 1:
            _, fr = data_visuals[0]
            coverage = 100.0 * (fr["w"] * fr["h"]) / 10000.0
            siblings = [
                b
                for b in blocks
                if isinstance(b, dict)
                and str(b.get("type") or "") not in {"data_source"}
                and b is not data_visuals[0][0]
            ]
            if coverage >= widescreen and len(siblings) == 0:
                issues.append("widescreen_single_data_visual")

        # Basic contrast: text/heading vs EVERY slide background endpoint —
        # a gradient is low-contrast when the fg fails against any endpoint.
        bg_colors = _slide_bg_colors(native_config)
        if bg_colors:
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if str(block.get("type") or "") not in {"text", "heading"}:
                    continue
                fg = _block_fg(block)
                if not fg:
                    continue
                ratios = [
                    _contrast_ratio(fg, bg)
                    for bg in bg_colors
                    if _parse_hex(bg)
                ]
                worst = min((r for r in ratios if r is not None), default=None)
                if worst is not None and worst < CONTRAST_MIN_RATIO:
                    issues.append(
                        f"low_contrast:{block.get('id') or block.get('type')}:{worst:.1f}"
                    )

        issues.extend(_collect_part_font_issues(blocks, tokens))
        issues.extend(_collect_hierarchy_issues(blocks))

        # Dedup preserve order
        seen: set[str] = set()
        out: list[str] = []
        for item in issues:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out


def _collect_part_font_issues(
    blocks: list[Any],
    tokens: Mapping[str, Any],
) -> list[str]:
    """Flag KPI/chart/table/input typography below designTokens.partChrome mins."""
    chrome = tokens.get("partChrome")
    if not isinstance(chrome, dict):
        return []
    issues: list[str] = []
    kpi_chrome = chrome.get("kpi") if isinstance(chrome.get("kpi"), dict) else {}
    chart_chrome = chrome.get("chart") if isinstance(chrome.get("chart"), dict) else {}
    table_chrome = chrome.get("table") if isinstance(chrome.get("table"), dict) else {}
    input_chrome = chrome.get("input") if isinstance(chrome.get("input"), dict) else {}

    for block in blocks:
        if not isinstance(block, dict):
            continue
        btype = str(block.get("type") or "")
        bid = str(block.get("id") or btype)

        if btype in _KPI_TYPES and kpi_chrome:
            parts = block.get("kpiParts") if isinstance(block.get("kpiParts"), dict) else {}
            title_fs = _part_font_size(parts, "title")
            title_min = float(kpi_chrome.get("titleMinFontSize") or 18)
            if title_fs is not None and title_fs < title_min:
                issues.append(f"part_font_below_min:{bid}:title:{title_fs}<{title_min}")
            value_fs = _part_font_size(parts, "value")
            density = _kpi_density_for_gate(block.get("frame"))
            value_mins = kpi_chrome.get("valueMinFontSize")
            if not isinstance(value_mins, dict):
                value_mins = {}
            value_min = float(value_mins.get(density) or value_mins.get("row") or 40)
            if value_fs is not None and value_fs < value_min:
                issues.append(f"part_font_below_min:{bid}:value:{value_fs}<{value_min}")
            icon = parts.get("icon") if isinstance(parts.get("icon"), dict) else {}
            icon_style = icon.get("style") if isinstance(icon.get("style"), dict) else {}
            icon_size = icon_style.get("iconSize")
            icon_min = float(kpi_chrome.get("iconMinSize") or 32)
            if isinstance(icon_size, (int, float)) and float(icon_size) < icon_min:
                issues.append(f"part_font_below_min:{bid}:icon:{icon_size}<{icon_min}")

        elif btype in {"chart_view", "data_chart"} and chart_chrome:
            opts = block.get("chartOptions") if isinstance(block.get("chartOptions"), dict) else {}
            title_fs = opts.get("titleFontSize")
            title_min = float(chart_chrome.get("titleMinFontSize") or 18)
            if isinstance(title_fs, (int, float)) and float(title_fs) < title_min:
                issues.append(f"part_font_below_min:{bid}:chart_title:{title_fs}<{title_min}")

        elif btype in {"table_view", "data_table"} and table_chrome:
            opts = block.get("tableOptions") if isinstance(block.get("tableOptions"), dict) else {}
            body_fs = opts.get("bodyFontSize")
            body_min = float(table_chrome.get("bodyMinFontSize") or 14)
            if isinstance(body_fs, (int, float)) and float(body_fs) < body_min:
                issues.append(f"part_font_below_min:{bid}:table_body:{body_fs}<{body_min}")

        elif btype == "input" and input_chrome:
            parts = block.get("inputParts") if isinstance(block.get("inputParts"), dict) else {}
            label_fs = _part_font_size(parts, "label")
            label_min = float(input_chrome.get("labelMinFontSize") or 14)
            if label_fs is not None and label_fs < label_min:
                issues.append(f"part_font_below_min:{bid}:input_label:{label_fs}<{label_min}")

    return issues


def _collect_hierarchy_issues(blocks: list[Any]) -> list[str]:
    issues: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        btype = str(block.get("type") or "")
        bid = str(block.get("id") or btype)
        if btype in _KPI_TYPES:
            parts = block.get("kpiParts") if isinstance(block.get("kpiParts"), dict) else {}
            if not parts:
                parts = block.get("parts") if isinstance(block.get("parts"), dict) else {}
            title_fs = _part_font_size(parts, "title")
            value_fs = _part_font_size(parts, "value")
            if title_fs is not None and value_fs is not None and title_fs >= value_fs:
                issues.append(f"hierarchy_inverted:{bid}:kpi_title>={value_fs}")
        elif btype in {"chart_view", "data_chart"}:
            opts = block.get("chartOptions") if isinstance(block.get("chartOptions"), dict) else {}
            title_fs = opts.get("titleFontSize")
            legend_fs = opts.get("legendFontSize")
            if (
                isinstance(title_fs, (int, float))
                and isinstance(legend_fs, (int, float))
                and float(title_fs) <= float(legend_fs)
            ):
                issues.append(f"hierarchy_inverted:{bid}:chart_title<={legend_fs}")
    return issues


def _part_font_size(parts: Mapping[str, Any], key: str) -> float | None:
    part = parts.get(key)
    if not isinstance(part, dict):
        return None
    style = part.get("style")
    if not isinstance(style, dict):
        return None
    fs = style.get("fontSize")
    if isinstance(fs, (int, float)):
        return float(fs)
    return None


def _kpi_density_for_gate(frame: Any) -> str:
    if not isinstance(frame, dict):
        return "row"
    try:
        area = float(frame.get("w", 0)) * float(frame.get("h", 0))
    except (TypeError, ValueError):
        return "row"
    if area >= 2200:
        return "hero"
    if area <= 900:
        return "grid"
    return "row"
