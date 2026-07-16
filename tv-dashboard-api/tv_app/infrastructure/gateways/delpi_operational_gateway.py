from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Mapping

from delpi_api_client import DelpiApiClient
from delpi_auth.service_token import internal_service_authorization

from tv_app.application.services.data.tv_data_param_defaults_service import (
    apply_catalog_param_defaults,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.application.services.tv_date_range_preset_service import (
    PERIOD_DAYS_KEY,
    apply_date_range_preset,
    date_alias_keys,
    read_date_range_values,
    resolve_output_date_range_keys,
)


def _build_query_params(
    route: dict[str, Any],
    params: Mapping[str, Any],
) -> dict[str, str]:
    strategy = str(route.get("paramStrategy") or "direct")
    schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
    date_range_keys = route.get("dateRangeKeys")
    with_defaults = apply_catalog_param_defaults(params, route)
    merged = apply_date_range_preset(
        with_defaults,
        schema_keys=schema,
        date_range_keys=date_range_keys,
        strategy=strategy,
    )
    query: dict[str, str] = {}

    fixed = route.get("fixedQueryParams")
    if isinstance(fixed, dict):
        for key, value in fixed.items():
            if value is not None and value != "":
                query[str(key)] = str(value)

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
        if not start or not end:
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
        branch = merged.get("branch")
        if branch:
            query["branch"] = str(branch).strip()
        drop_aliases = date_alias_keys(keep=(start_key, end_key))
        for key, value in merged.items():
            if key in {PERIOD_DAYS_KEY, "branch"} | drop_aliases:
                continue
            if value is None or value == "":
                continue
            query[str(key)] = str(value)
        return _filter_query_to_route_schema(query, schema=schema, fixed=fixed, always_allow={start_key, end_key, "branch"})

    # direct: emite schema + extras, mas se há par de datas canônico, remove aliases
    pair = resolve_output_date_range_keys(
        schema_keys=schema,
        date_range_keys=date_range_keys,
        strategy=None,
    )
    drop_aliases: set[str] = set()
    always_allow: set[str] = set()
    if pair:
        start_key, end_key = pair
        start, end = read_date_range_values(merged, start_key, end_key)
        if start:
            merged[start_key] = start
        if end:
            merged[end_key] = end
        drop_aliases = set(date_alias_keys(keep=(start_key, end_key))) - {start_key, end_key}
        always_allow = {start_key, end_key}

    for key, value in merged.items():
        if key == PERIOD_DAYS_KEY and key not in schema:
            continue
        if key in drop_aliases:
            continue
        if value is None or value == "":
            continue
        query[str(key)] = str(value)
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
    return {key: value for key, value in query.items() if key in allowed}


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
        if not path.startswith("/"):
            raise ValueError(f"Path inválido para {operation_id}")

        query = _build_query_params(route, params or {})
        envelope = self._client.get_path(
            path,
            params=query,
            authorization=self._auth(authorization),
        )
        return {
            "operationId": operation_id,
            "meta": {
                "operationId": operation_id,
                "entity": route.get("metaShape") or "scalar",
                "shape": route.get("metaShape") or "scalar",
                "fields": route.get("paramSchema") or {},
            },
            "data": envelope,
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
