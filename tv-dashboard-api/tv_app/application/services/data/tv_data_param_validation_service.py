from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.data.tv_data_param_defaults_service import (
    apply_catalog_param_defaults,
    should_apply_schema_default,
)
from tv_app.application.services.data.tv_data_presentation_modes_service import (
    validate_block_type_for_binding,
    validate_display_mode,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.application.services.tv_dashboard_content_service import filter_label, message
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


def _is_param_optional(spec: Mapping[str, Any]) -> bool:
    """Alinhado ao MFE (`isParamFieldOptional`): sem flag = opcional."""
    if isinstance(spec.get("required"), bool):
        return not bool(spec.get("required"))
    if "optional" in spec:
        return bool(spec.get("optional"))
    return True


def _param_display_name(key: str, spec: Mapping[str, Any]) -> str:
    label = str(spec.get("label") or "").strip()
    return label or key


def _required_param_error(key: str, spec: Mapping[str, Any]) -> ValueError:
    param = _param_display_name(key, spec)
    return ValueError(
        message("dataParamRequired", f"Parâmetro obrigatório: {param}.", param=param)
    )


def _has_period_intent(params: Mapping[str, Any]) -> bool:
    if params.get(PERIOD_DAYS_KEY) not in (None, ""):
        return True
    if str(params.get(DATE_RANGE_PRESET_KEY) or "").strip():
        return True
    pair = find_date_range_keys(list(params.keys()))
    if pair:
        start_key, end_key = pair
        if params.get(start_key) not in (None, "") or params.get(end_key) not in (None, ""):
            return True
    # Aliases soltos (params podem ter só um nome canônico).
    for key in ("start_date", "end_date", "date_start", "date_end"):
        if params.get(key) not in (None, ""):
            return True
    return False


def closed_date_range_missing_filter_labels(
    route: Mapping[str, Any] | None,
    *,
    schema: Mapping[str, Any] | None = None,
) -> list[str]:
    """Rótulos dos filtros a indicar quando falta período em rota date_range fechada."""
    if not isinstance(route, Mapping):
        return []
    if str(route.get("paramStrategy") or "").strip() != "date_range":
        return []
    if bool(route.get("openEndedDateRange")):
        return []
    schema_map = schema if isinstance(schema, Mapping) else route.get("paramSchema")
    if not isinstance(schema_map, Mapping):
        schema_map = {}
    labels = [filter_label("period", "Período")]
    pair = find_date_range_keys(schema_map) or find_date_range_keys(route.get("dateRangeKeys"))
    if pair:
        start_key, end_key = pair
        start_spec = schema_map.get(start_key) if isinstance(schema_map.get(start_key), Mapping) else {}
        end_spec = schema_map.get(end_key) if isinstance(schema_map.get(end_key), Mapping) else {}
        labels.append(
            _param_display_name(start_key, start_spec)
            if start_spec
            else filter_label("startDate", "Data início")
        )
        labels.append(
            _param_display_name(end_key, end_spec)
            if end_spec
            else filter_label("endDate", "Data fim")
        )
    else:
        labels.append(filter_label("startDate", "Data início"))
        labels.append(filter_label("endDate", "Data fim"))
    return labels


def assert_closed_date_range_has_period(
    route: Mapping[str, Any] | None,
    params: Mapping[str, Any] | None,
) -> None:
    """Rotas date_range fechadas exigem Período ou datas — sem default mágico no gateway."""
    labels = closed_date_range_missing_filter_labels(route)
    if not labels:
        return
    if _has_period_intent(params or {}):
        return
    params_text = ", ".join(labels)
    raise ValueError(
        message(
            "dataDateRangeRequired",
            f"Informe o período nos filtros: {params_text}.",
            params=params_text,
        )
    )


def validate_params_against_schema(
    params: dict[str, Any] | None,
    param_schema: dict[str, Any] | None,
    *,
    fixed_query_params: dict[str, Any] | None = None,
    route: dict[str, Any] | None = None,
    enforce_required: bool = True,
) -> dict[str, Any]:
    """Valida e normaliza params do bloco/filtro conforme paramSchema do catálogo.

    `fixedQueryParams` do catálogo satisfaz parâmetros obrigatórios (não pedem valor na UI).
    Valor vazio no bloco usa `default` do schema / convenções / `defaultParams` da rota.
    Par de datas obrigatório é aceito via `dateRangePreset` / `periodDays` (expansão no gateway).

    Params obrigatórios (departamento, filial required, etc.) e período em rotas
    `date_range` fechadas **não** devem ser exigidos em camadas parciais (binding,
    `dataFilters`, `dataDefaults`): herdam via `merge_data_params`
    (programação → tela → fonte → input). Use `enforce_required=False` nesses
    contextos; o assert completo vive no boundary pós-merge
    (`assert_merged_route_params` / `_build_query_params` / enrichment).
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
            if should_apply_schema_default(key, spec):
                normalized[key] = spec.get("default")
            elif enforce_required and not _is_param_optional(spec):
                seeded_value = seeded.get(key)
                if seeded_value not in (None, ""):
                    normalized[key] = _coerce_param_value(str(spec.get("type") or "string"), seeded_value)
                else:
                    raise _required_param_error(key, spec)
            continue
        value = _coerce_param_value(str(spec.get("type") or "string"), raw_value)
        if value is None or value == "":
            if should_apply_schema_default(key, spec):
                normalized[key] = spec.get("default")
            elif enforce_required and not _is_param_optional(spec):
                seeded_value = seeded.get(key)
                if seeded_value not in (None, ""):
                    normalized[key] = _coerce_param_value(str(spec.get("type") or "string"), seeded_value)
                else:
                    raise _required_param_error(key, spec)
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


def assert_merged_route_params(
    route: Mapping[str, Any] | None,
    params: Mapping[str, Any] | None,
) -> None:
    """Boundary pós-`merge_data_params`: obrigatoriedade de schema + período fechado.

    Única fonte de verdade para «falta Departamento / Filial / …» em runtime —
    não validar isso no binding isolado nem em dataFilters/dataDefaults parciais.
    """
    if not isinstance(route, Mapping):
        return
    schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), Mapping) else {}
    fixed = (
        route.get("fixedQueryParams")
        if isinstance(route.get("fixedQueryParams"), Mapping)
        else None
    )
    validate_params_against_schema(
        dict(params) if isinstance(params, Mapping) else {},
        dict(schema) if isinstance(schema, Mapping) else {},
        fixed_query_params=dict(fixed) if isinstance(fixed, Mapping) else None,
        route=dict(route),
        enforce_required=True,
    )
    assert_closed_date_range_has_period(route, params)


def validate_data_binding(
    binding: dict[str, Any] | None,
    *,
    block_type: str,
    route: dict[str, Any] | None,
) -> None:
    """Validação estrutural do binding (rota, modo, tipos).

    Não exige query params obrigatórios: programação/tela/fonte/input entram
    só depois de `merge_data_params` (`assert_merged_route_params`).
    """
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
        enforce_required=False,
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
    """Camada parcial (tela/programação): tipa/normaliza; não exige obrigatórios."""
    if not isinstance(filters, dict) or not filters:
        return {}
    merged_schema: dict[str, Any] = {}
    for route in routes:
        schema = route.get("paramSchema")
        if isinstance(schema, dict):
            merged_schema.update(schema)
    return validate_params_against_schema(
        filters,
        merged_schema or None,
        enforce_required=False,
    )
