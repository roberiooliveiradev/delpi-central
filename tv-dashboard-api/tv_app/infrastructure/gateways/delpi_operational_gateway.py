from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Mapping

from delpi_api_client import DelpiApiClient
from delpi_auth.service_token import internal_service_authorization

from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.application.services.tv_date_range_preset_service import (
    PERIOD_DAYS_KEY,
    apply_date_range_preset,
)


def _build_query_params(
    route: dict[str, Any],
    params: Mapping[str, Any],
) -> dict[str, str]:
    strategy = str(route.get("paramStrategy") or "direct")
    schema = route.get("paramSchema") if isinstance(route.get("paramSchema"), dict) else {}
    merged = apply_date_range_preset(dict(params), schema_keys=schema)
    query: dict[str, str] = {}

    fixed = route.get("fixedQueryParams")
    if isinstance(fixed, dict):
        for key, value in fixed.items():
            if value is not None and value != "":
                query[str(key)] = str(value)

    if strategy == "date_range":
        start = merged.get("start_date")
        end = merged.get("end_date")
        if not start or not end:
            period_days = int(
                merged.get(PERIOD_DAYS_KEY)
                or route.get("defaultParams", {}).get(PERIOD_DAYS_KEY)
                or 7
            )
            end_d = date.today()
            start_d = end_d - timedelta(days=max(period_days, 1) - 1)
            start, end = start_d.isoformat(), end_d.isoformat()
        query["start_date"] = str(start)
        query["end_date"] = str(end)
        branch = merged.get("branch")
        if branch:
            query["branch"] = str(branch).strip()
        for key, value in merged.items():
            if key in {PERIOD_DAYS_KEY, "start_date", "end_date", "branch", "date_start", "date_end"}:
                continue
            if value is None or value == "":
                continue
            query[str(key)] = str(value)
        return query

    for key, value in merged.items():
        if key == PERIOD_DAYS_KEY and key not in schema:
            continue
        if value is None or value == "":
            continue
        query[str(key)] = str(value)
    return query


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
                "seriesField": route.get("seriesField"),
                "tableFields": route.get("tableFields"),
                "tvConstraints": route.get("tvConstraints") or {},
            },
        }
