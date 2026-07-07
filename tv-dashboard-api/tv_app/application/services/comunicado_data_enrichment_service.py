from __future__ import annotations

import json
from typing import Any

from tv_app.application.services.branch_access_scope_service import BranchAccessScopeService
from tv_app.application.services.comunicado_data_params_service import merge_data_params
from tv_app.application.services.native_screen_cache_service import (
    native_data_cache_ttl_seconds,
)
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.application.services.tv_data_route_catalog_service import (
    DATA_BLOCK_TYPES,
    TvDataRouteCatalogService,
)
from tv_app.infrastructure.cache.ttl_cache import TtlCache
from tv_app.infrastructure.gateways.delpi_operational_gateway import DelpiOperationalGateway

_data_block_cache = TtlCache[dict[str, Any]](ttl_seconds=native_data_cache_ttl_seconds())


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


def _extract_scalar_value(data: Any, value_fields: list[Any]) -> Any:
    if not isinstance(data, dict):
        return None
    summary = data.get("summary")
    if isinstance(summary, dict):
        for field in value_fields:
            key = str(field)
            if key in summary and summary[key] is not None:
                return summary[key]
    for field in value_fields:
        key = str(field)
        if key in data and data[key] is not None:
            return data[key]
    return None


def _extract_series(
    data: Any,
    series_field: str | None,
    *,
    branch: str | None = None,
) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    key = series_field or "points"
    raw = data.get(key)
    if not isinstance(raw, list):
        raw = data.get("series")
    if not isinstance(raw, list):
        return []
    branch_code = str(branch).strip() if branch else ""
    points: list[dict[str, Any]] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        label = row.get("label") or row.get("bucket") or row.get("periodo") or row.get("date")
        value = row.get("value")
        if value is None and branch_code:
            branch_key = branch_code.zfill(2)
            value = (
                row.get(f"oee_filial_{branch_key}")
                or row.get(f"otd_filial_{branch_key}")
                or row.get(f"oee_pct_filial_{branch_key}")
            )
        if value is None:
            for field_key, field_value in row.items():
                if not isinstance(field_key, str) or field_value is None:
                    continue
                if field_key.startswith(("oee_", "otd_")) and field_key not in {"oee_pct", "otd_pct"}:
                    value = field_value
                    break
        points.append({"label": label, "value": value})
    return points


def _extract_table_rows(data: Any, table_field: str | None, max_rows: int) -> list[dict[str, Any]]:
    if not isinstance(data, dict):
        return []
    key = table_field or "items"
    raw = data.get(key)
    if not isinstance(raw, list):
        raw = data.get("top_products")
    if not isinstance(raw, list):
        return []
    rows: list[dict[str, Any]] = []
    for row in raw[:max_rows]:
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "productCode": row.get("product_code") or row.get("productCode"),
                "description": row.get("product_description") or row.get("description"),
                "stockValue": row.get("total_stock_value") or row.get("stockValue") or row.get("value"),
                "stockQuantity": row.get("total_stock_quantity") or row.get("stockQuantity"),
            }
        )
    return rows


class ComunicadoDataEnrichmentService:
    """Resolve blocos data_* via api-delpi (allowlist + merge de filtros)."""

    def __init__(
        self,
        catalog: TvDataRouteCatalogService | None = None,
        gateway: DelpiOperationalGateway | None = None,
        branch_scope: BranchAccessScopeService | None = None,
    ) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()
        self._gateway = gateway or DelpiOperationalGateway(catalog=self._catalog)
        self._branch_scope = branch_scope or BranchAccessScopeService()

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
        scope = self._branch_scope.resolve(user) if user is not None else None
        enriched: list[dict[str, Any]] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            if block_type not in DATA_BLOCK_TYPES:
                enriched.append(block)
                continue
            enriched.append(
                self._enrich_data_block(
                    block,
                    slide_filters=slide_filters,
                    playlist_defaults=playlist_defaults,
                    authorization=authorization,
                    scope=scope,
                )
            )
        return enriched

    def _enrich_data_block(
        self,
        block: dict[str, Any],
        *,
        slide_filters: dict[str, Any],
        playlist_defaults: dict[str, Any] | None,
        authorization: str | None,
        scope: Any | None,
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
        if scope is not None:
            try:
                self._branch_scope.assert_branch_allowed(scope, str(branch).strip() if branch else None)
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
        display_mode = str(binding.get("displayMode") or "auto")
        block_type = str(block.get("type") or "")

        resolved: dict[str, Any] = {
            "meta": payload.get("meta") or {},
            "data": data,
            "error": None,
            "displayMode": display_mode,
            "label": binding.get("label") or route_info.get("label"),
        }

        value_fields = route_info.get("valueFields") or []
        if block_type == "data_kpi" or display_mode == "kpi":
            resolved["kpi"] = {
                "value": _extract_scalar_value(data, value_fields),
                "label": resolved.get("label"),
            }
        elif block_type == "data_chart" or display_mode in {"line_chart", "bar_chart", "chart"}:
            branch = merged_params.get("branch")
            resolved["chart"] = {
                "points": _extract_series(
                    data,
                    route_info.get("seriesField"),
                    branch=str(branch).strip() if branch else None,
                ),
            }
        elif block_type == "data_table" or display_mode == "table":
            max_rows = int(binding.get("maxRows") or route_info.get("tvConstraints", {}).get("maxRows") or 5)
            resolved["table"] = {
                "rows": _extract_table_rows(data, route_info.get("tableFields"), max_rows),
            }

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
