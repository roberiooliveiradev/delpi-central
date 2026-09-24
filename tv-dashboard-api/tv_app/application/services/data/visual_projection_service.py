"""Projeção automática KPI/chart/table a partir do catálogo de rota."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from tv_app.application.services.data.display_format_hints_service import (
    DisplayFormatHintsService,
)
from tv_app.application.services.data.ready_slide_quality_service import (
    ReadySlideQualityService,
)
from tv_app.application.services.data.table_view_projection_authority import (
    has_explicit_table_columns,
    normalize_block_table_projection,
)


class VisualProjectionService:
    """Owner de *Projection tipada pós-bind (não depende só do GPT)."""

    @classmethod
    def value_fields(cls, route: Mapping[str, Any] | None) -> list[str]:
        if not isinstance(route, dict):
            return []
        raw = route.get("valueFields")
        if isinstance(raw, list):
            return [str(item).strip() for item in raw if str(item).strip()]
        return []

    @classmethod
    def value_field_types(cls, route: Mapping[str, Any] | None) -> dict[str, str]:
        if not isinstance(route, dict):
            return {}
        raw = route.get("valueFieldTypes")
        if not isinstance(raw, dict):
            return {}
        return {str(k): str(v) for k, v in raw.items() if str(k).strip()}

    @classmethod
    def primary_value_field(cls, route: Mapping[str, Any] | None) -> str | None:
        fields = cls.value_fields(route)
        if not fields:
            return None
        preferred = ("value", "ppm", "ppmValue", "pct", "rate", "oee", "otd")
        lower_map = {f.lower(): f for f in fields}
        for key in preferred:
            if key in lower_map:
                return lower_map[key]
        return fields[0]

    @classmethod
    def format_for_field(
        cls, route: Mapping[str, Any] | None, field: str
    ) -> dict[str, Any] | None:
        types = cls.value_field_types(route)
        hint = DisplayFormatHintsService.resolve(
            field_key=field,
            field_type=str(types.get(field) or ""),
        )
        return hint.to_dict() if hint else None

    @classmethod
    def kpi_projection(cls, route: Mapping[str, Any] | None) -> dict[str, Any]:
        field = cls.primary_value_field(route)
        if not field:
            return {}
        metric: dict[str, Any] = {"field": field, "label": field}
        fmt = cls.format_for_field(route, field)
        if fmt:
            metric["format"] = fmt.get("valueFormat") or "number"
            if fmt.get("decimalPlaces") is not None:
                metric["decimalPlaces"] = fmt["decimalPlaces"]
        return {"metrics": [metric], "valueField": field}

    @classmethod
    def kpi_options(cls, route: Mapping[str, Any] | None) -> dict[str, Any]:
        field = cls.primary_value_field(route)
        if not field:
            return {}
        fmt = cls.format_for_field(route, field)
        if not fmt:
            return {"valueFormat": "number"}
        out: dict[str, Any] = {"valueFormat": fmt.get("valueFormat") or "number"}
        if fmt.get("currency"):
            out["currency"] = fmt["currency"]
        return out

    @classmethod
    def chart_projection(cls, route: Mapping[str, Any] | None) -> dict[str, Any]:
        fields = cls.value_fields(route)
        y_field = cls.primary_value_field(route)
        if not y_field:
            return {}
        x_candidates = ("period", "periodo", "date", "data", "week", "month", "label", "name")
        x_field = None
        lower_map = {f.lower(): f for f in fields}
        for key in x_candidates:
            if key in lower_map and lower_map[key] != y_field:
                x_field = lower_map[key]
                break
        if x_field is None:
            for f in fields:
                if f != y_field:
                    x_field = f
                    break
        proj: dict[str, Any] = {"yField": y_field}
        if x_field:
            proj["xField"] = x_field
        return proj

    @classmethod
    def table_projection(cls, route: Mapping[str, Any] | None) -> dict[str, Any]:
        fields = cls.value_fields(route)
        if not fields:
            return {}
        columns: list[dict[str, Any]] = []
        for field in fields[:8]:
            # ``key`` is authoritative for MFE/runtime; ``field`` kept as GPT alias.
            col: dict[str, Any] = {"key": field, "field": field, "label": field}
            fmt = cls.format_for_field(route, field)
            if fmt and fmt.get("valueFormat"):
                col["valueFormat"] = fmt["valueFormat"]
            columns.append(col)
        return {"columns": columns}

    @classmethod
    def patch_for_visual(
        cls,
        *,
        block_type: str,
        route: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        token = str(block_type or "").strip()
        if token in {"kpi_view", "data_kpi"}:
            patch: dict[str, Any] = {}
            proj = cls.kpi_projection(route)
            opts = cls.kpi_options(route)
            if proj:
                patch["kpiProjection"] = proj
            if opts:
                patch["kpiOptions"] = opts
            return patch
        if token in {"chart_view", "data_chart"}:
            proj = cls.chart_projection(route)
            return {"chartProjection": proj} if proj else {}
        if token in {"table_view", "data_table"}:
            proj = cls.table_projection(route)
            return {"tableProjection": proj} if proj else {}
        return {}

    @classmethod
    def apply_to_block(
        cls,
        block: dict[str, Any],
        route: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        # Explicit visual projection is authoritative — never replace with inference.
        if has_explicit_table_columns(block):
            return normalize_block_table_projection(dict(block))
        patch = cls.patch_for_visual(block_type=str(block.get("type") or ""), route=route)
        if not patch:
            return block
        next_block = dict(block)
        for key, value in patch.items():
            existing = next_block.get(key)
            if isinstance(existing, dict) and existing:
                probe = dict(block)
                probe[key] = existing
                if not ReadySlideQualityService.projection_is_empty(probe):
                    continue
            next_block[key] = value
        return next_block
