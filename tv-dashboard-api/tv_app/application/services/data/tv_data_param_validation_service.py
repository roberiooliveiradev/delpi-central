from __future__ import annotations

from typing import Any

from tv_app.application.services.data.tv_data_param_defaults_service import (
    apply_catalog_param_defaults,
)
from tv_app.application.services.data.tv_data_presentation_modes_service import (
    validate_block_type_for_binding,
    validate_display_mode,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    INTERNAL_PARAM_KEYS,
    PERIOD_DAYS_KEY,
    find_date_range_keys,
)


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
    *,
    fixed_query_params: dict[str, Any] | None = None,
    route: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Valida e normaliza params do bloco/filtro conforme paramSchema do catálogo.

    `fixedQueryParams` do catálogo satisfaz parâmetros obrigatórios (não pedem valor na UI).
    Valor vazio no bloco usa `default` do schema / convenções / `defaultParams` da rota.
    Par de datas obrigatório é aceito via `dateRangePreset` / `periodDays` (expansão no gateway).
    """
    schema = param_schema if isinstance(param_schema, dict) else {}
    fixed = fixed_query_params if isinstance(fixed_query_params, dict) else {}
    seeded = apply_catalog_param_defaults(params, route if route is not None else {"paramSchema": schema})
    raw = params if isinstance(params, dict) else {}
    # Mantém preset/periodDays originais para isentar datas obrigatórias.
    for key in (DATE_RANGE_PRESET_KEY, PERIOD_DAYS_KEY):
        if key in raw and raw[key] not in (None, ""):
            seeded[key] = raw[key]

    date_pair = find_date_range_keys(schema)
    has_period_intent = (
        seeded.get(DATE_RANGE_PRESET_KEY) not in (None, "")
        or seeded.get(PERIOD_DAYS_KEY) not in (None, "")
    )
    date_keys_covered_by_preset = set(date_pair) if date_pair and has_period_intent else set()

    normalized: dict[str, Any] = {}

    for key, spec in schema.items():
        if not isinstance(spec, dict):
            continue
        if key in fixed and fixed.get(key) not in (None, ""):
            continue
        if key in date_keys_covered_by_preset:
            continue
        raw_value = seeded.get(key) if key in seeded else None
        empty = raw_value is None or raw_value == ""
        if empty:
            if spec.get("default") is not None:
                normalized[key] = spec.get("default")
            elif not spec.get("optional", False):
                seeded_value = seeded.get(key)
                if seeded_value not in (None, ""):
                    normalized[key] = _coerce_param_value(str(spec.get("type") or "string"), seeded_value)
                else:
                    raise ValueError(message("dataParamRequired", f"Parâmetro obrigatório: {key}"))
            continue
        value = _coerce_param_value(str(spec.get("type") or "string"), raw_value)
        if value is None or value == "":
            if spec.get("default") is not None:
                normalized[key] = spec.get("default")
            elif not spec.get("optional", False):
                seeded_value = seeded.get(key)
                if seeded_value not in (None, ""):
                    normalized[key] = _coerce_param_value(str(spec.get("type") or "string"), seeded_value)
                else:
                    raise ValueError(message("dataParamRequired", f"Parâmetro obrigatório: {key}"))
            continue
        normalized[key] = value

    for key, value in raw.items():
        if key in normalized or value is None or value == "":
            continue
        if key in fixed:
            continue
        # dateRangePreset / periodDays (quando só auxilia preset) — não vão no OpenAPI.
        if key in INTERNAL_PARAM_KEYS or key == PERIOD_DAYS_KEY:
            continue
        if key not in schema:
            # Alinhado ao fetch: strip silencioso (hydrate pré-save também remove).
            continue
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
    validate_params_against_schema(
        params,
        route.get("paramSchema"),
        fixed_query_params=route.get("fixedQueryParams")
        if isinstance(route.get("fixedQueryParams"), dict)
        else None,
        route=route,
    )

    max_rows = binding.get("maxRows")
    if max_rows is not None:
        limit = int(route.get("tvConstraints", {}).get("maxRows") or 90)
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
