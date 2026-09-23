"""Compact spatial digest of a TV slide for VISTA layout perception (no pixels)."""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)

_KPI_TYPES = frozenset({"kpi_view", "data_kpi"})
_CHART_TYPES = frozenset({"chart_view", "data_chart"})
_TABLE_TYPES = frozenset({"table_view", "data_table"})
_TEXT_BOUND = frozenset({"heading", "text", "shape"})
_PRIMARY_TYPES = _KPI_TYPES | _CHART_TYPES | _TABLE_TYPES


def _frame(block: Mapping[str, Any]) -> dict[str, float] | None:
    raw = block.get("frame")
    if not isinstance(raw, dict):
        return None
    try:
        return {
            "x": round(float(raw.get("x", 0)), 2),
            "y": round(float(raw.get("y", 0)), 2),
            "w": round(float(raw.get("w", 0)), 2),
            "h": round(float(raw.get("h", 0)), 2),
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


def _z_index(block: Mapping[str, Any]) -> int | None:
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    raw = style.get("zIndex", block.get("zIndex"))
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _block_signals(block: Mapping[str, Any]) -> dict[str, Any]:
    btype = str(block.get("type") or "")
    signals: dict[str, Any] = {}
    if btype in _CHART_TYPES:
        chart_type = block.get("chartType") or (
            (block.get("chart") or {}).get("type")
            if isinstance(block.get("chart"), dict)
            else None
        )
        if chart_type:
            signals["chartType"] = str(chart_type)
    if btype in _TABLE_TYPES:
        preset = block.get("tablePreset")
        if preset:
            signals["tablePreset"] = str(preset)
    if btype in _TEXT_BOUND:
        tp = block.get("textProjection")
        signals["hasTextProjection"] = isinstance(tp, dict) and bool(tp.get("field"))
        if block.get("dataSourceId"):
            signals["hasDataSource"] = True
    if btype in _KPI_TYPES:
        parts = block.get("parts") if isinstance(block.get("parts"), dict) else {}
        value = parts.get("value") if isinstance(parts.get("value"), dict) else {}
        title = parts.get("title") if isinstance(parts.get("title"), dict) else {}
        icon = parts.get("icon") if isinstance(parts.get("icon"), dict) else {}
        if value.get("fontSize") is not None:
            try:
                signals["kpiValueFontSize"] = float(value["fontSize"])
            except (TypeError, ValueError):
                pass
        if title.get("fontSize") is not None:
            try:
                signals["kpiTitleFontSize"] = float(title["fontSize"])
            except (TypeError, ValueError):
                pass
        if icon.get("iconSize") is not None:
            try:
                signals["kpiIconSize"] = float(icon["iconSize"])
            except (TypeError, ValueError):
                pass
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    if style.get("fontSize") is not None and btype in {"heading", "text"}:
        try:
            signals["fontSize"] = float(style["fontSize"])
        except (TypeError, ValueError):
            pass
    if block.get("groupId"):
        signals["groupId"] = str(block["groupId"])
    return signals


def _layout_hints(
    blocks: list[dict[str, Any]],
    frames: list[tuple[dict[str, Any], dict[str, float]]],
) -> dict[str, Any]:
    tokens = PresentationRecipeService.document().get("designTokens") or {}
    max_signals = int(tokens.get("maxPrimarySignalsPerSlide") or 4)
    overlap_threshold = float(tokens.get("overlapAreaThresholdPct") or 8)

    primary = sum(1 for b in blocks if str(b.get("type") or "") in _PRIMARY_TYPES)
    kpi_count = sum(1 for b in blocks if str(b.get("type") or "") in _KPI_TYPES)

    overlaps: list[dict[str, Any]] = []
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
                overlaps.append(
                    {
                        "a": str(a_block.get("id") or a_block.get("type")),
                        "b": str(b_block.get("id") or b_block.get("type")),
                        "overlapPct": round(pct, 1),
                    }
                )

    coverage = 0.0
    for _, fr in frames:
        coverage += fr["w"] * fr["h"]
    density = "sparse"
    if coverage >= 6500:
        density = "dense"
    elif coverage >= 3500:
        density = "moderate"

    return {
        "blockCount": len(blocks),
        "primarySignalCount": primary,
        "kpiCount": kpi_count,
        "maxPrimarySignals": max_signals,
        "density": density,
        "approxCoveragePct": round(min(100.0, coverage / 100.0), 1),
        "coarseOverlaps": overlaps[:12],
        "hasCoarseOverlap": bool(overlaps),
    }


class LayoutDigestService:
    """Projects INFORMED geometry from persisted native_config (no raster)."""

    @classmethod
    def digest_native_config(
        cls,
        native_config: Mapping[str, Any] | None,
        *,
        slide_id: str | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        cfg = native_config if isinstance(native_config, dict) else {}
        raw_blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
        blocks: list[dict[str, Any]] = [b for b in raw_blocks if isinstance(b, dict)]
        # Exclude pure data_source nodes from spatial digest
        spatial = [b for b in blocks if str(b.get("type") or "") != "data_source"]

        projected: list[dict[str, Any]] = []
        frames: list[tuple[dict[str, Any], dict[str, float]]] = []
        for block in spatial:
            fr = _frame(block)
            entry: dict[str, Any] = {
                "id": str(block.get("id") or ""),
                "type": str(block.get("type") or ""),
            }
            if fr:
                entry["frame"] = fr
                frames.append((block, fr))
            z = _z_index(block)
            if z is not None:
                entry["zIndex"] = z
            signals = _block_signals(block)
            if signals:
                entry["signals"] = signals
            projected.append(entry)

        return {
            "slideId": slide_id,
            "title": title,
            "blockCount": len(spatial),
            "blocks": projected,
            "layoutHints": _layout_hints(spatial, frames),
        }

    @classmethod
    def digest_slide(cls, slide: Mapping[str, Any] | None) -> dict[str, Any]:
        if not isinstance(slide, dict):
            return cls.digest_native_config(None)
        return cls.digest_native_config(
            slide.get("nativeConfig") if isinstance(slide.get("nativeConfig"), dict) else {},
            slide_id=str(slide.get("id") or "") or None,
            title=str(slide.get("title") or "") or None,
        )

    @classmethod
    def digest_slides(cls, slides: list[Any] | None) -> list[dict[str, Any]]:
        if not isinstance(slides, list):
            return []
        return [cls.digest_slide(s) for s in slides if isinstance(s, dict)]
