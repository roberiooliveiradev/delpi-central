from __future__ import annotations

import json
from typing import Any

from tv_app.application.services.branch_policy_service import validate_native_branch
from tv_app.application.services.comunicado_data_params_service import merge_data_params
from tv_app.application.services.data.tv_data_presentation_modes_service import normalize_display_mode
from tv_app.application.services.native_screen_cache_service import (
    native_data_cache_ttl_seconds,
)
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.application.services.tv_data_route_catalog_service import (
    DATA_BLOCK_TYPES,
    DATA_VIEW_BLOCK_TYPES,
    TvDataRouteCatalogService,
)
from tv_app.infrastructure.cache.ttl_cache import TtlCache
from tv_app.infrastructure.gateways.delpi_operational_gateway import DelpiOperationalGateway
from tv_app.application.services.series_points_extractor import extract_series_points

_data_block_cache = TtlCache[dict[str, Any]](ttl_seconds=native_data_cache_ttl_seconds())

# Sem maxRows explícito: série diária (~3 meses) cabe no scroll do bloco; não truncar em 5
# (gráfico recebe a série inteira — tabela deve acompanhar).
_DEFAULT_TABLE_MAX_ROWS = 90


def _resolve_table_max_rows(binding: dict[str, Any], route_info: dict[str, Any]) -> int:
    if binding.get("maxRows") is not None:
        return max(1, int(binding["maxRows"]))
    constraints = route_info.get("tvConstraints")
    if isinstance(constraints, dict) and constraints.get("maxRows") is not None:
        return max(1, int(constraints["maxRows"]))
    return _DEFAULT_TABLE_MAX_ROWS


def _build_data_cache_key(
    *,
    operation_id: str,
    params: dict[str, Any],
    authorization: str | None,
) -> str:
    auth_scope = "user" if authorization else "service"
    return json.dumps(
        {"operationId": operation_id, "params": params, "authScope": auth_scope},
        sort_keys=True,
        default=str,
    )


def _value_fields_for_binding(route_info: dict[str, Any], binding: dict[str, Any]) -> list[str]:
    override = binding.get("valueField")
    if override is not None and str(override).strip():
        return [str(override).strip()]
    raw = route_info.get("valueFields") or []
    return [str(field).strip() for field in raw if str(field).strip()]


def _iter_scalar_candidate_keys(value_fields: list[Any]) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for field in value_fields:
        key = str(field).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        keys.append(key)
    for fallback in ("value", "total", "pct", "percentage"):
        if fallback not in seen:
            seen.add(fallback)
            keys.append(fallback)
    return keys


def _first_numeric_like_field(payload: dict[str, Any]) -> Any:
    """Fallback quando o catálogo não declara valueFields (ex.: campos *_pct no payload)."""
    preferred: list[tuple[int, str, Any]] = []
    for key, value in payload.items():
        if value is None or isinstance(value, (dict, list, bool)):
            continue
        if not isinstance(key, str):
            continue
        key_l = key.lower()
        rank = 3
        if key_l.endswith("_pct") or key_l.endswith("_percentage") or key_l.endswith("pct"):
            rank = 0
        elif key_l in {"value", "total"}:
            rank = 1
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            rank = 2
        else:
            continue
        preferred.append((rank, key, value))
    if not preferred:
        return None
    preferred.sort(key=lambda item: (item[0], item[1]))
    return preferred[0][2]


def _extract_scalar_value(data: Any, value_fields: list[Any]) -> Any:
    if not isinstance(data, dict):
        return None
    keys = _iter_scalar_candidate_keys(value_fields)
    summary = data.get("summary")
    if isinstance(summary, dict):
        for key in keys:
            if key in summary and summary[key] is not None:
                return summary[key]
        if not value_fields:
            fallback = _first_numeric_like_field(summary)
            if fallback is not None:
                return fallback
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    if not value_fields:
        return _first_numeric_like_field(data)
    return None


def _extract_series(
    data: Any,
    series_field: str | None,
    *,
    branch: str | None = None,
) -> list[dict[str, Any]]:
    return extract_series_points(data, series_field, branch=branch)

def _list_from_data(data: Any, table_field: str | None) -> list[Any]:
    if not isinstance(data, dict):
        return []
    key = table_field or "items"
    raw = data.get(key)
    if isinstance(raw, list):
        return raw
    raw = data.get("top_products")
    if isinstance(raw, list):
        return raw
    return []


def _build_table_columns(meta: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    fields = meta.get("fields")
    if isinstance(fields, list):
        columns: list[dict[str, str]] = []
        for field in fields:
            if not isinstance(field, dict):
                continue
            key = str(field.get("key") or field.get("name") or "").strip()
            if not key:
                continue
            columns.append(
                {
                    "key": key,
                    "label": str(field.get("label") or field.get("title") or key),
                }
            )
        if columns:
            return columns
    if rows:
        return [{"key": str(key), "label": str(key)} for key in rows[0].keys()]
    return []


def _series_to_table_rows(
    data: Any,
    series_field: str | None,
    *,
    branch: str | None = None,
    max_rows: int,
    value_label: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Converte pontos de série temporal em linhas tabulares (ex.: OTD/OEE)."""
    points = _extract_series(data, series_field, branch=branch)
    rows: list[dict[str, Any]] = []
    for point in points[:max_rows]:
        label = point.get("label")
        rows.append(
            {
                "label": label,
                "periodo": label,
                "value": point.get("value"),
            }
        )
    if not rows:
        return [], []
    columns = [
        {"key": "periodo", "label": "Período"},
        {"key": "value", "label": value_label or "Valor"},
    ]
    return rows, columns


def _extract_table_rows(
    data: Any,
    table_field: str | None,
    max_rows: int,
    *,
    meta: dict[str, Any] | None = None,
    series_field: str | None = None,
    branch: str | None = None,
    value_label: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    raw_rows = _list_from_data(data, table_field)
    rows: list[dict[str, Any]] = []
    for row in raw_rows[:max_rows]:
        if isinstance(row, dict):
            rows.append(dict(row))
    columns = _build_table_columns(meta or {}, rows)
    if rows:
        return rows, columns

    series_rows, series_columns = _series_to_table_rows(
        data,
        series_field,
        branch=branch,
        max_rows=max_rows,
        value_label=value_label,
    )
    if series_rows:
        return series_rows, series_columns

    return rows, columns


def _scalar_as_chart_points(value: Any, label: str | None = None) -> list[dict[str, Any]]:
    if value is None:
        return []
    return [{"label": label, "value": value}]


def _infer_auto_display_mode(
    data: Any,
    route_info: dict[str, Any],
    meta: dict[str, Any],
) -> str:
    shape = str(meta.get("shape") or route_info.get("metaShape") or "scalar")
    if shape == "paged_list" or route_info.get("tableFields"):
        return "table"
    if route_info.get("seriesField") or shape in {"playbook_report", "composite_analysis"}:
        points = _extract_series(data, route_info.get("seriesField"))
        if points:
            return "line_chart"
    return "kpi"


class ComunicadoDataEnrichmentService:
    """Resolve blocos data_* via api-delpi (allowlist + merge de filtros)."""

    def __init__(
        self,
        catalog: TvDataRouteCatalogService | None = None,
        gateway: DelpiOperationalGateway | None = None,
    ) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()
        self._gateway = gateway or DelpiOperationalGateway(catalog=self._catalog)

    def enrich_blocks(
        self,
        blocks: list[dict[str, Any]],
        *,
        cfg: dict[str, Any],
        authorization: str | None = None,
        playlist_defaults: dict[str, Any] | None = None,
        user: Any | None = None,
    ) -> list[dict[str, Any]]:
        slide_filters = cfg.get("dataFilters") if isinstance(cfg.get("dataFilters"), dict) else {}
        enriched: list[dict[str, Any]] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            if block_type in DATA_BLOCK_TYPES:
                enriched.append(
                    self._enrich_data_block(
                        block,
                        slide_filters=slide_filters,
                        playlist_defaults=playlist_defaults,
                        authorization=authorization,
                        user=user,
                    )
                )
                continue
            if block_type in DATA_VIEW_BLOCK_TYPES:
                enriched.append(dict(block))
                continue
            enriched.append(block)
        return self._link_view_blocks_to_sources(enriched)

    @staticmethod
    def _link_view_blocks_to_sources(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        source_resolved: dict[str, dict[str, Any]] = {}
        for block in blocks:
            if str(block.get("type") or "") == "data_source":
                resolved = block.get("resolved")
                if isinstance(resolved, dict):
                    source_resolved[str(block.get("id") or "")] = resolved
        if not source_resolved:
            return blocks
        linked: list[dict[str, Any]] = []
        for block in blocks:
            block_type = str(block.get("type") or "")
            if block_type not in DATA_VIEW_BLOCK_TYPES:
                linked.append(block)
                continue
            source_id = str(block.get("dataSourceId") or "").strip()
            if not source_id or source_id not in source_resolved:
                linked.append(block)
                continue
            merged = dict(block)
            merged["resolved"] = source_resolved[source_id]
            linked.append(merged)
        return linked

    def _resolve_presentation(
        self,
        *,
        display_mode: str,
        data: Any,
        route_info: dict[str, Any],
        meta: dict[str, Any],
        binding: dict[str, Any],
        merged_params: dict[str, Any],
        label: str | None,
    ) -> dict[str, Any]:
        mode = normalize_display_mode(display_mode)
        if mode == "auto":
            mode = _infer_auto_display_mode(data, route_info, meta)

        value_fields = _value_fields_for_binding(route_info, binding)
        branch = merged_params.get("branch")
        branch_str = str(branch).strip() if branch else None
        max_rows = _resolve_table_max_rows(binding, route_info)

        if mode == "kpi":
            scalar = _extract_scalar_value(data, value_fields)
            if scalar is None:
                points = _extract_series(data, route_info.get("seriesField"), branch=branch_str)
                if points:
                    scalar = points[-1].get("value")
            return {"kpi": {"value": scalar, "label": label}}

        if mode in {"line_chart", "bar_chart"}:
            points = _extract_series(data, route_info.get("seriesField"), branch=branch_str)
            if not points:
                scalar = _extract_scalar_value(data, value_fields)
                points = _scalar_as_chart_points(scalar, label)
            chart_type = "bar" if mode == "bar_chart" else "line"
            return {"chart": {"points": points, "chartType": chart_type}}

        rows, columns = _extract_table_rows(
            data,
            route_info.get("tableFields"),
            max_rows,
            meta=meta,
            series_field=route_info.get("seriesField"),
            branch=branch_str,
            value_label=label,
        )
        if not rows:
            scalar = _extract_scalar_value(data, value_fields)
            if scalar is not None:
                row: dict[str, Any] = {}
                field_key = value_fields[0] if value_fields else "value"
                row[field_key] = scalar
                if label:
                    row["label"] = label
                rows = [row]
                columns = _build_table_columns(meta, rows)
        return {"table": {"rows": rows, "columns": columns}}

    def _enrich_data_block(
        self,
        block: dict[str, Any],
        *,
        slide_filters: dict[str, Any],
        playlist_defaults: dict[str, Any] | None,
        authorization: str | None,
        user: Any | None,
    ) -> dict[str, Any]:
        result = dict(block)
        binding = block.get("dataBinding")
        if not isinstance(binding, dict):
            result["resolved"] = {"error": message("dataIndicatorUnavailable", "Indicador indisponível")}
            return result

        operation_id = str(binding.get("operationId") or "").strip()
        if not self._catalog.is_allowed(operation_id):
            result["resolved"] = {"error": message("dataIndicatorUnavailable", "Indicador indisponível")}
            return result

        block_params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
        merged_params = merge_data_params(
            playlist_defaults=playlist_defaults,
            slide_filters=slide_filters,
            block_params=block_params,
        )

        branch = merged_params.get("branch")
        try:
            validate_native_branch({"branch": branch}, user=user)
        except ValueError as exc:
            result["resolved"] = {"error": str(exc)}
            return result

        try:
            payload = self._fetch_cached(operation_id, merged_params, authorization)
        except Exception as exc:  # noqa: BLE001
            result["resolved"] = {
                "error": message("nativeDataUnavailable"),
                "detail": str(exc),
            }
            return result

        route_info = payload.get("route") or {}
        data = payload.get("data")
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        display_mode = str(binding.get("displayMode") or "kpi")
        block_type = str(block.get("type") or "")

        resolved: dict[str, Any] = {
            "meta": meta,
            "data": data,
            "error": None,
            "displayMode": normalize_display_mode(display_mode),
            "label": binding.get("label") or route_info.get("label"),
        }

        if block_type == "data_source":
            for mode in ("kpi", "line_chart", "table"):
                resolved.update(
                    self._resolve_presentation(
                        display_mode=mode,
                        data=data,
                        route_info=route_info,
                        meta=meta,
                        binding=binding,
                        merged_params=merged_params,
                        label=resolved.get("label"),
                    )
                )
        else:
            resolved.update(
                self._resolve_presentation(
                    display_mode=display_mode,
                    data=data,
                    route_info=route_info,
                    meta=meta,
                    binding=binding,
                    merged_params=merged_params,
                    label=resolved.get("label"),
                )
            )

        result["resolved"] = resolved
        return result

    def _fetch_cached(
        self,
        operation_id: str,
        params: dict[str, Any],
        authorization: str | None,
    ) -> dict[str, Any]:
        cache_key = _build_data_cache_key(
            operation_id=operation_id,
            params=params,
            authorization=authorization,
        )
        cached = _data_block_cache.get(cache_key)
        if cached is not None:
            return cached
        payload = self._gateway.fetch_by_operation_id(
            operation_id,
            params=params,
            authorization=authorization,
        )
        if not payload.get("error"):
            _data_block_cache.set(cache_key, payload)
        return payload


def reset_comunicado_data_block_cache() -> None:
    _data_block_cache.invalidate_all()
