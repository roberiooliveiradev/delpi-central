from __future__ import annotations

import os
from typing import Any, Mapping, MutableMapping
from urllib.parse import urlencode

import httpx

from delpi_auth.service_token import apply_internal_service_headers


class StrategicIndicatorsApiError(RuntimeError):
    pass


class StrategicIndicatorsApiClient:
    """Cliente HTTP server-to-server para strategic-indicators-api."""

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        raw = (
            base_url
            or os.getenv("STRATEGIC_INDICATORS_API_BASE_URL")
            or "http://strategic-indicators-api:8000"
        )
        self._base_url = raw.rstrip("/")
        self._timeout = timeout_seconds

    def list_dashboard_goals(
        self,
        *,
        source_keys: list[str],
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        department_id: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str | None] = {
            "source_keys": ",".join(source_keys),
            "competence": competence,
            "start_date": start_date,
            "end_date": end_date,
            "branch": branch,
            "department_id": department_id,
        }
        return self._get(
            "/strategic-indicators/integrations/dashboard-goals",
            params=params,
            authorization=authorization,
        )

    def get_tv_dashboard_hero(
        self,
        *,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str | None] = {
            "branch": branch,
            "competence": competence,
            "start_date": start_date,
            "end_date": end_date,
        }
        return self._get(
            "/strategic-indicators/integrations/tv-dashboard-hero",
            params=params,
            authorization=authorization,
        )

    def get_dashboard_department_score(
        self,
        *,
        department_id: str,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str | None] = {
            "department_id": department_id,
            "competence": competence,
            "start_date": start_date,
            "end_date": end_date,
            "branch": branch,
        }
        return self._get(
            "/strategic-indicators/integrations/dashboard-department-score",
            params=params,
            authorization=authorization,
        )

    def get_dashboard_department_indicators(
        self,
        *,
        department_id: str,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str | None] = {
            "department_id": department_id,
            "competence": competence,
            "start_date": start_date,
            "end_date": end_date,
            "branch": branch,
        }
        return self._get(
            "/strategic-indicators/integrations/dashboard-department-indicators",
            params=params,
            authorization=authorization,
        )

    def list_dashboard_departments_indicators(
        self,
        *,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        department_id: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str | None] = {
            "competence": competence,
            "start_date": start_date,
            "end_date": end_date,
            "branch": branch,
            "department_id": department_id,
        }
        return self._get(
            "/strategic-indicators/integrations/dashboard-departments-indicators",
            params=params,
            authorization=authorization,
        )

    def _get(
        self,
        path: str,
        *,
        params: Mapping[str, str | None] | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        query = ""
        if params:
            filtered = {k: v for k, v in params.items() if v is not None and v != ""}
            if filtered:
                query = f"?{urlencode(filtered)}"

        headers: MutableMapping[str, str] = {}
        if authorization:
            headers["Authorization"] = authorization
        apply_internal_service_headers(headers)

        url = f"{self._base_url}{path}{query}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            raise StrategicIndicatorsApiError(
                f"Falha de rede ao consultar Strategic Indicators API: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise StrategicIndicatorsApiError(
                f"Strategic Indicators API retornou {response.status_code}: {response.text}"
            )

        payload = response.json()
        if not isinstance(payload, dict):
            raise StrategicIndicatorsApiError(
                "Resposta inválida da Strategic Indicators API (esperado objeto JSON)."
            )
        return payload
