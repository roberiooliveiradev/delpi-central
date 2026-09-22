"""Deterministic layout quality gates for TV slides (geometry / density / contrast)."""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)

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


def _slide_bg_color(cfg: Mapping[str, Any]) -> str | None:
    bg = cfg.get("background")
    if not isinstance(bg, dict):
        return None
    if bg.get("type") == "color" and isinstance(bg.get("value"), str):
        return str(bg["value"])
    if bg.get("type") == "gradient":
        for key in ("to", "from"):
            if isinstance(bg.get(key), str):
                return str(bg[key])
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

        # Basic contrast: text/heading vs slide background
        bg = _slide_bg_color(native_config)
        if bg:
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if str(block.get("type") or "") not in {"text", "heading"}:
                    continue
                fg = _block_fg(block)
                if not fg:
                    continue
                ratio = _contrast_ratio(fg, bg)
                if ratio is not None and ratio < 2.5:
                    issues.append(
                        f"low_contrast:{block.get('id') or block.get('type')}:{ratio:.1f}"
                    )

        # Dedup preserve order
        seen: set[str] = set()
        out: list[str] = []
        for item in issues:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out
