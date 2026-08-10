from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Mapping

from delpi_api_client import DelpiApiClient
from delpi_auth.service_token import internal_service_authorization

from tv_app.application.services.comunicado_data_params_service import (
    BRANCH_PARAM_KEYS,
    canonical_branch_wire_value,
    project_branch_params_onto_route_schema,
    schema_branch_param_keys,
)
from tv_app.application.services.data.tv_data_param_defaults_service import (
    apply_catalog_param_defaults,
)
from tv_app.application.services.data.tv_data_param_validation_service import (
    assert_closed_date_range_has_period,
    assert_merged_route_params,
)
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.application.services.series_points_extractor import (
    envelope_meta,
    response_fields_from_meta,
    unwrap_operational_data,
)
from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    EXCLUDE_WEEKENDS_KEY,
    PERIOD_DAYS_KEY,
    apply_date_range_preset,
    date_alias_keys,
    read_date_range_values,
    resolve_output_date_range_keys,
)

# dateRangePreset / excludeWeekends nunca vão na query; periodDays só se estiver no schema.
_VISUAL_ONLY_QUERY_KEYS = frozenset({DATE_RANGE_PRESET_KEY, EXCLUDE_WEEKENDS_KEY})

_PATH_PARAM_RE = re.compile(r"\{([^{}]+)\}")


def path_param_names(path: str) -> list[str]:
    """Nomes dos placeholders `{name}` no path OpenAPI/TV."""
    return [match.group(1).strip() for match in _PATH_PARAM_RE.finditer(path) if match.group(1).strip()]


def resolve_route_path(
    path: str,
    params: Mapping[str, Any],
    *,
    schema: Mapping[str, Any] | None = None,
) -> str:
    """Substitui `{name}` no path pelos valores de params (ou default do schema).

    Levanta ValueError se faltar path param obrigatório — evita 422 opaco da api-delpi
    com placeholder literal.
    """
    names = path_param_names(path)
    if not names:
        return path
    resolved = path
    schema_map = schema if isinstance(schema, Mapping) else {}
    missing: list[str] = []
    for name in names:
        raw = params.get(name)
        if raw is None or raw == "":
            field = schema_map.get(name) if isinstance(schema_map.get(name), Mapping) else {}
            raw = field.get("default") if isinstance(field, Mapping) else None
        if name in BRANCH_PARAM_KEYS:
            raw = canonical_branch_wire_value(raw)
        if raw is None or raw == "":
            missing.append(name)
            continue
        resolved = resolved.replace("{" + name + "}", str(raw).strip())
    if missing:
        preview = ", ".join(missing[:6])
        extra = f" (+{len(missing) - 6})" if len(missing) > 6 else ""
        raise ValueError(
            message(
                "dataRouteMissingPathParams",
                f"Parâmetros de path obrigatórios ausentes: {preview}{extra}.",
                params=f"{preview}{extra}",
            )
        )
    if "{" in resolved and "}" in resolved:
        raise ValueError(
            message(
                "dataRouteUnresolvedPath",
                "Path da rota ainda contém placeholders não resolvidos.",
            )
        )
    return resolved


def _build_query_params(
    route: dict[str, Any],
    params: Mapping[str, Any],
) -> dict[str, str]:
    strategy = str(route.get("paramStrategy") or "direct")
    schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
    date_range_keys = route.get("dateRangeKeys")
    with_defaults = apply_catalog_param_defaults(params, route)
    open_ended = bool(route.get("openEndedDateRange"))
    # Pós-merge: params obrigatórios + período fechado (não no binding isolado).
    assert_merged_route_params(route, with_defaults)
    merged = apply_date_range_preset(
        with_defaults,
        schema_keys=schema,
        date_range_keys=date_range_keys,
        strategy=strategy,
    )
    # Filial: qualquer alias (branch/filial/…) → chave(s) do schema da rota.
    merged = project_branch_params_onto_route_schema(merged, schema)
    query: dict[str, str] = {}

    fixed = route.get("fixedQueryParams")
    if isinstance(fixed, dict):
        for key, value in fixed.items():
            if value is not None and value != "":
                query[str(key)] = str(value)

    schema_branch_keys = set(schema_branch_param_keys(schema))

    if strategy == "date_range":
        # Nomes HTTP só do schema/catálogo — nunca dos valores do usuário (evita date_start em rota start_date).
        pair = resolve_output_date_range_keys(
            schema_keys=schema,
            date_range_keys=date_range_keys,
            strategy=strategy,
        )
        assert pair is not None  # strategy date_range sempre resolve
        start_key, end_key = pair
        start, end = read_date_range_values(merged, start_key, end_key)
        has_period_days = merged.get(PERIOD_DAYS_KEY) not in (None, "")
        # Sem datas e sem periodDays → omite o par (histórico completo na API / openEnded).
        # periodDays / datas parciais / preset resolvido ainda preenchem o intervalo.
        omit_date_range = not start and not end and not has_period_days
        if omit_date_range and not open_ended:
            # Defesa: assert acima já cobre; reforço se preset expandiu para vazio.
            assert_closed_date_range_has_period(route, merged)
        if not omit_date_range and (not start or not end):
            if open_ended and not has_period_days:
                # Rota aberta: envia só a ponta informada (não inventa janela de 7 dias).
                if start:
                    query[start_key] = str(start)
                if end:
                    query[end_key] = str(end)
            else:
                # Respeita data parcial do filtro/input (ex.: só end_date) em vez de
                # forçar fim=hoje e apagar o valor do usuário.
                period_days = int(
                    merged.get(PERIOD_DAYS_KEY)
                    or route.get("defaultParams", {}).get(PERIOD_DAYS_KEY)
                    or 7
                )
                try:
                    end_d = date.fromisoformat(str(end)[:10]) if end else date.today()
                except ValueError:
                    end_d = date.today()
                try:
                    start_d = (
                        date.fromisoformat(str(start)[:10])
                        if start
                        else end_d - timedelta(days=max(period_days, 1) - 1)
                    )
                except ValueError:
                    start_d = end_d - timedelta(days=max(period_days, 1) - 1)
                start, end = start_d.isoformat(), end_d.isoformat()
                query[start_key] = str(start)
                query[end_key] = str(end)
        elif not omit_date_range:
            query[start_key] = str(start)
            query[end_key] = str(end)
        drop_aliases = date_alias_keys(keep=(start_key, end_key))
        for key, value in merged.items():
            if key in {PERIOD_DAYS_KEY} | _VISUAL_ONLY_QUERY_KEYS | drop_aliases:
                continue
            if value is None or value == "":
                continue
            key_str = str(key)
            if key_str in BRANCH_PARAM_KEYS:
                canon = canonical_branch_wire_value(value)
                if canon:
                    query[key_str] = canon
                continue
            query[key_str] = str(value)
        always_allow = {start_key, end_key} if not omit_date_range else set()
        always_allow |= schema_branch_keys
        return _filter_query_to_route_schema(
            query, schema=schema, fixed=fixed, always_allow=always_allow
        )

    # direct: emite schema + extras, mas se há par de datas canônico, remove aliases
    pair = resolve_output_date_range_keys(
        schema_keys=schema,
        date_range_keys=date_range_keys,
        strategy=None,
    )
    drop_aliases: set[str] = set()
    always_allow: set[str] = set(schema_branch_keys)
    if pair:
        start_key, end_key = pair
        start, end = read_date_range_values(merged, start_key, end_key)
        if start:
            merged[start_key] = start
        if end:
            merged[end_key] = end
        drop_aliases = set(date_alias_keys(keep=(start_key, end_key))) - {start_key, end_key}
        always_allow |= {start_key, end_key}

    for key, value in merged.items():
        if key == PERIOD_DAYS_KEY and key not in schema:
            continue
        if key in _VISUAL_ONLY_QUERY_KEYS:
            continue
        if key in drop_aliases:
            continue
        if value is None or value == "":
            continue
        key_str = str(key)
        if key_str in BRANCH_PARAM_KEYS:
            canon = canonical_branch_wire_value(value)
            if canon:
                query[key_str] = canon
            continue
        query[key_str] = str(value)
    return _filter_query_to_route_schema(query, schema=schema, fixed=fixed, always_allow=always_allow)

def _filter_query_to_route_schema(
    query: dict[str, str],
    *,
    schema: Mapping[str, Any],
    fixed: Mapping[str, Any] | None,
    always_allow: set[str] | None = None,
) -> dict[str, str]:
    """Evita 422 da api-delpi por params de período/UI ausentes no OpenAPI da rota."""
    if not schema:
        return query
    allowed = set(schema.keys())
    if isinstance(fixed, Mapping):
        allowed |= {str(key) for key in fixed.keys()}
    if always_allow:
        allowed |= always_allow
    # Path params vão no path — nunca na query.
    for key, field in schema.items():
        if isinstance(field, Mapping) and str(field.get("in") or "").lower() == "path":
            allowed.discard(str(key))
    return {key: value for key, value in query.items() if key in allowed}


def _strip_path_params_from_query(
    query: dict[str, str],
    *,
    path: str,
) -> dict[str, str]:
    names = set(path_param_names(path))
    if not names:
        return query
    return {key: value for key, value in query.items() if key not in names}


class DelpiOperationalGateway:
    """HTTP genérico para rotas allowlist da TV (por operationId + path)."""

    def __init__(
        self,
        client: DelpiApiClient | None = None,
        catalog: TvDataRouteCatalogService | None = None,
    ) -> None:
        self._client = client or DelpiApiClient(caller_app="tv-dashboard-api")
        self._catalog = catalog or TvDataRouteCatalogService()

    def _auth(self, authorization: str | None) -> str | None:
        return authorization or internal_service_authorization()

    def fetch_by_operation_id(
        self,
        operation_id: str,
        *,
        params: Mapping[str, Any] | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        route = self._catalog.get_route(operation_id)
        if not route:
            raise ValueError(message("dataSourceUnavailable", "Fonte de dados indisponível."))

        http_method = str(route.get("httpMethod") or "GET").upper()
        if http_method != "GET":
            raise ValueError(message("dataRouteMethodNotAllowed", "Somente rotas GET são permitidas na TV."))

        path = str(route.get("path") or "").strip()
        canonical_operation_id = str(route.get("operationId") or operation_id).strip()
        if not path.startswith("/"):
            raise ValueError(f"Path inválido para {canonical_operation_id}")

        schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
        with_defaults = apply_catalog_param_defaults(params or {}, route)
        resolved_path = resolve_route_path(path, with_defaults, schema=schema)
        query = _build_query_params(route, params or {})
        query = _strip_path_params_from_query(query, path=path)
        envelope = self._client.get_path(
            resolved_path,
            params=query,
            authorization=self._auth(authorization),
        )
        api_meta = envelope_meta(envelope)
        business_data = unwrap_operational_data(envelope)
        response_fields = response_fields_from_meta(api_meta)
        # Nunca cair em paramSchema: é schema de query, não rótulos de campos do payload.
        return {
            "operationId": canonical_operation_id,
            "meta": {
                "operationId": canonical_operation_id,
                "entity": api_meta.get("entity") or route.get("metaShape") or "scalar",
                "shape": api_meta.get("shape") or route.get("metaShape") or "scalar",
                "fields": response_fields or {},
            },
            "data": business_data,
            "route": {
                "label": route.get("label"),
                "category": route.get("category"),
                "valueFields": route.get("valueFields") or [],
                "valueFieldLabels": route.get("valueFieldLabels") or {},
                "valueFieldTypes": route.get("valueFieldTypes") or {},
                "seriesField": route.get("seriesField"),
                "tableFields": route.get("tableFields"),
                "tvConstraints": route.get("tvConstraints") or {},
            },
        }
