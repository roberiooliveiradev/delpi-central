from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Mapping

from delpi_api_client import DelpiApiClient
from delpi_auth.service_token import internal_service_authorization

from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def _date_range(period_days: int) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=max(int(period_days or 1), 1))
    return start.isoformat(), end.isoformat()


def _build_query_params(
    route: dict[str, Any],
    params: Mapping[str, Any],
) -> dict[str, str]:
    strategy = str(route.get("paramStrategy") or "direct")
    merged = dict(params)
    query: dict[str, str] = {}

    if strategy == "date_range":
        period_days = int(merged.get("periodDays") or route.get("defaultParams", {}).get("periodDays") or 7)
        start, end = _date_range(period_days)
        query["start_date"] = start
        query["end_date"] = end
        branch = merged.get("branch")
        if branch:
            query["branch"] = str(branch).strip()
        return query

    for key, value in merged.items():
        if key == "periodDays":
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
            raise ValueError(f"Rota não permitida na TV: {operation_id}")

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
                "seriesField": route.get("seriesField"),
                "tableFields": route.get("tableFields"),
                "tvConstraints": route.get("tvConstraints") or {},
            },
        }
