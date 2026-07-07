from __future__ import annotations

from typing import Any

from tv_app.application.services.data.tv_data_presentation_modes_service import (
    validate_block_type_for_binding,
    validate_display_mode,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.application.services.tv_dashboard_content_service import message


def _coerce_param_value(field_type: str, raw: Any) -> Any:
    if raw is None or raw == "":
        return None
    if field_type == "integer":
        return int(raw)
    if field_type == "number":
        return float(raw)
    if field_type == "boolean":
        if isinstance(raw, bool):
            return raw
        token = str(raw).strip().lower()
        return token in {"1", "true", "yes", "on"}
    return str(raw).strip()


def validate_params_against_schema(
    params: dict[str, Any] | None,
    param_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    """Valida e normaliza params do bloco/filtro conforme paramSchema do catálogo."""
    schema = param_schema if isinstance(param_schema, dict) else {}
    raw = params if isinstance(params, dict) else {}
    normalized: dict[str, Any] = {}

    for key, spec in schema.items():
        if not isinstance(spec, dict):
            continue
        if key not in raw:
            if spec.get("default") is not None:
                normalized[key] = spec.get("default")
            elif not spec.get("optional", False):
                raise ValueError(message("dataParamRequired", f"Parâmetro obrigatório: {key}"))
            continue
        value = _coerce_param_value(str(spec.get("type") or "string"), raw.get(key))
        if value is None or value == "":
            if not spec.get("optional", False):
                raise ValueError(message("dataParamRequired", f"Parâmetro obrigatório: {key}"))
            continue
        normalized[key] = value

    for key, value in raw.items():
        if key in normalized or value is None or value == "":
            continue
        if key not in schema:
            raise ValueError(message("dataParamUnknown", f"Parâmetro não permitido: {key}"))
    return normalized


def validate_data_binding(
    binding: dict[str, Any] | None,
    *,
    block_type: str,
    route: dict[str, Any] | None,
) -> None:
    if not isinstance(binding, dict):
        raise ValueError(message("dataSourceUnavailable", "Fonte de dados indisponível."))
    operation_id = str(binding.get("operationId") or "").strip()
    if not route:
        raise ValueError(message("dataSourceUnavailable", "Fonte de dados indisponível."))
    if str(route.get("httpMethod") or "GET").upper() != "GET":
        raise ValueError(message("dataRouteMethodNotAllowed", "Somente rotas GET são permitidas na TV."))

    display_mode = binding.get("displayMode")
    validate_display_mode(
        str(display_mode) if display_mode is not None else "auto",
        allowed_display_modes=route.get("allowedDisplayModes"),
    )
    validate_block_type_for_binding(block_type, str(display_mode) if display_mode is not None else "auto")

    params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
    validate_params_against_schema(params, route.get("paramSchema"))

    max_rows = binding.get("maxRows")
    if max_rows is not None:
        limit = int(route.get("tvConstraints", {}).get("maxRows") or 6)
        if int(max_rows) > limit:
            raise ValueError(message("dataRowsLimitExceeded", "Limite de linhas excedido para esta rota."))


def validate_data_filters(
    filters: dict[str, Any] | None,
    *,
    routes: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(filters, dict) or not filters:
        return {}
    merged_schema: dict[str, Any] = {}
    for route in routes:
        schema = route.get("paramSchema")
        if isinstance(schema, dict):
            merged_schema.update(schema)
    return validate_params_against_schema(filters, merged_schema or None)
