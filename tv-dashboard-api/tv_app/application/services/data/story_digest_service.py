"""Compact playlist story index for VISTA context. Not a second nativeConfig."""

from __future__ import annotations

from typing import Any, Mapping

_CHART_TYPES = frozenset({"chart_view", "data_chart"})
_KPI_TYPES = frozenset({"kpi_view", "data_kpi"})
_TABLE_TYPES = frozenset({"table_view", "data_table", "canvas_table"})


class StoryDigestService:
    @classmethod
    def digest(cls, slides: list[Any] | None) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        distribution: dict[str, int] = {}
        total_duration = 0
        for slide in slides or []:
            if not isinstance(slide, Mapping):
                continue
            native = slide.get("nativeConfig") if isinstance(slide.get("nativeConfig"), dict) else {}
            family = _visual_family(native)
            distribution[family] = distribution.get(family, 0) + 1
            try:
                total_duration += int(slide.get("durationSec") or 0)
            except (TypeError, ValueError):
                pass
            rows.append(
                {
                    "slideId": str(slide.get("id") or ""),
                    "purpose": str(slide.get("title") or slide.get("name") or ""),
                    "visualFamily": family,
                    "primaryMetric": _primary_metric(native),
                }
            )
        repetitive = _repetitive(distribution, len(rows))
        warnings: list[str] = []
        if repetitive:
            warnings.append(
                "visual family repeats across recent slides: " + ", ".join(repetitive)
            )
        return {
            "slides": rows,
            "repetitiveLayouts": repetitive,
            "visualFamilyDistribution": distribution,
            "totalDurationSec": total_duration,
            "warnings": warnings,
        }

    @classmethod
    def dominant_family(cls, story: Mapping[str, Any] | None) -> str | None:
        if not isinstance(story, Mapping):
            return None
        repetitive = story.get("repetitiveLayouts")
        if isinstance(repetitive, list) and repetitive:
            family = str(repetitive[0] or "").strip()
            return family or None
        return None


def _visual_family(native: Mapping[str, Any]) -> str:
    blocks = native.get("blocks") if isinstance(native.get("blocks"), list) else []
    chart_type = None
    has_kpi = False
    has_table = False
    for block in blocks:
        if not isinstance(block, Mapping):
            continue
        btype = str(block.get("type") or "")
        if btype in _CHART_TYPES:
            chart_type = str(block.get("chartType") or "chart")
        elif btype in _KPI_TYPES:
            has_kpi = True
        elif btype in _TABLE_TYPES:
            has_table = True
    if chart_type and has_kpi:
        return f"kpi_{chart_type}"
    if chart_type:
        return chart_type
    if has_table and has_kpi:
        return "kpi_table"
    if has_table:
        return "table"
    if has_kpi:
        return "kpi"
    return "other"


def _primary_metric(native: Mapping[str, Any]) -> str | None:
    blocks = native.get("blocks") if isinstance(native.get("blocks"), list) else []
    for block in blocks:
        if not isinstance(block, Mapping):
            continue
        if str(block.get("type") or "") not in _KPI_TYPES | _CHART_TYPES:
            continue
        for key in ("kpiProjection", "chartProjection"):
            projection = block.get(key)
            if isinstance(projection, dict):
                field = projection.get("field") or projection.get("valueField")
                if field:
                    return str(field)
        label = block.get("label") or block.get("title")
        if label:
            return str(label)
    return None


def _repetitive(distribution: Mapping[str, int], count: int) -> list[str]:
    if count < 2:
        return []
    threshold = max(2, (count + 1) // 2)
    return [family for family, total in distribution.items() if family != "other" and total >= threshold]
