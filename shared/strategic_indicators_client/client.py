from __future__ import annotations

import os
from typing import Any, Mapping, MutableMapping
from urllib.parse import urlencode

import httpx

from delpi_auth.service_token import apply_internal_service_headers


class StrategicIndicatorsApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code


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

    def get_dashboard_indicator_realized(
        self,
        *,
        indicator_id: str,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str | None] = {
            "indicator_id": indicator_id,
            "competence": competence,
            "start_date": start_date,
            "end_date": end_date,
            "branch": branch,
        }
        return self._get(
            "/strategic-indicators/integrations/dashboard-indicator-realized",
            params=params,
            authorization=authorization,
        )

    def get_dashboard_indicator_meta(
        self,
        *,
        indicator_id: str,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
        authorization: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, str | None] = {
            "indicator_id": indicator_id,
            "competence": competence,
            "start_date": start_date,
            "end_date": end_date,
            "branch": branch,
        }
        return self._get(
            "/strategic-indicators/integrations/dashboard-indicator-meta",
            params=params,
            authorization=authorization,
        )

    # -- User-parity reads (DAVI governed surface) -------------------------
    #
    # These methods hit the USER-FACING SI routes (``/strategic-indicators/*``)
    # with the end-user JWT only. They must never attach the internal service
    # token: that token mints a superadmin principal at the SI boundary and
    # would bypass the caller's own ``strategic-indicators.*`` permissions.

    def get_user_executive_summary(
        self,
        *,
        authorization: str,
        department_id: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        return self._get_user_scoped(
            "/strategic-indicators/executive-summary",
            params={
                "department_id": department_id,
                "branch": branch,
                "competence": competence,
                "start_date": start_date,
                "end_date": end_date,
            },
            authorization=authorization,
        )

    def get_user_departments(
        self,
        *,
        authorization: str,
        department_id: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        return self._get_user_scoped(
            "/strategic-indicators/departments",
            params={
                "department_id": department_id,
                "branch": branch,
                "competence": competence,
                "start_date": start_date,
                "end_date": end_date,
            },
            authorization=authorization,
        )

    def get_user_indicators(
        self,
        *,
        authorization: str,
        department_id: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        return self._get_user_scoped(
            "/strategic-indicators/indicators",
            params={
                "department_id": department_id,
                "branch": branch,
                "competence": competence,
                "start_date": start_date,
                "end_date": end_date,
            },
            authorization=authorization,
        )

    def list_user_indicator_goals(
        self,
        *,
        authorization: str,
        indicator_id: str | None = None,
        goal_year: int | None = None,
        department_id: str | None = None,
        active_only: bool | None = None,
    ) -> dict[str, Any]:
        return self._get_user_scoped(
            "/strategic-indicators/indicator-goals",
            params={
                "indicator_id": indicator_id,
                "goal_year": goal_year,
                "department_id": department_id,
                "active_only": active_only,
            },
            authorization=authorization,
        )

    def list_user_indicator_goal_history(
        self,
        *,
        authorization: str,
        indicator_id: str,
        goal_year: int | None = None,
    ) -> dict[str, Any]:
        return self._get_user_scoped(
            "/strategic-indicators/indicator-goals/history",
            params={
                "indicator_id": indicator_id,
                "goal_year": goal_year,
            },
            authorization=authorization,
        )

    # -- User-parity writes (DAVI governed ACT surface) --------------------
    #
    # Same identity contract as the user-parity reads: the caller's own JWT
    # only, never the internal service token. ``expected_*`` arguments carry
    # the optional optimistic-concurrency preconditions enforced atomically
    # by the owner API.

    def create_user_indicator_goal(
        self,
        *,
        authorization: str,
        body: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self._write_user_scoped(
            "POST",
            "/strategic-indicators/indicator-goals",
            json_body=dict(body),
            authorization=authorization,
        )

    def update_user_indicator_goal(
        self,
        *,
        authorization: str,
        goal_id: str,
        body: Mapping[str, Any],
    ) -> dict[str, Any]:
        return self._write_user_scoped(
            "PUT",
            f"/strategic-indicators/indicator-goals/{goal_id}",
            json_body=dict(body),
            authorization=authorization,
        )

    def activate_user_indicator_goal(
        self,
        *,
        authorization: str,
        goal_id: str,
        expected_xmin: str | None = None,
    ) -> dict[str, Any]:
        return self._write_user_scoped(
            "POST",
            f"/strategic-indicators/indicator-goals/{goal_id}/activate",
            params={"expected_xmin": expected_xmin},
            authorization=authorization,
        )

    def deactivate_user_indicator_goal(
        self,
        *,
        authorization: str,
        goal_id: str,
        expected_xmin: str | None = None,
    ) -> dict[str, Any]:
        return self._write_user_scoped(
            "POST",
            f"/strategic-indicators/indicator-goals/{goal_id}/deactivate",
            params={"expected_xmin": expected_xmin},
            authorization=authorization,
        )

    def _write_user_scoped(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        authorization: str | None,
    ) -> dict[str, Any]:
        """Non-GET call on a user-facing SI route carrying only the user JWT.

        Fail-closed: without a user Authorization header there is no
        legitimate identity to evaluate, so the request is refused locally.
        No retries — a timed-out write may have committed; callers reconcile
        via postcondition reads instead of blind resubmission.
        """
        token = (authorization or "").strip()
        if not token:
            raise StrategicIndicatorsApiError(
                "Escrita em Strategic Indicators exige o token do usuário autenticado."
            )
        return self._request(
            method,
            path,
            params=params,
            headers={"Authorization": token},
            json_body=json_body,
        )

    def _get_user_scoped(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        """GET on a user-facing SI route carrying only the end-user JWT.

        Fail-closed: without a user Authorization header there is no
        legitimate identity to evaluate, so the request is refused locally.
        """
        token = (authorization or "").strip()
        if not token:
            raise StrategicIndicatorsApiError(
                "Consulta a Strategic Indicators exige o token do usuário autenticado."
            )
        return self._request(
            "GET",
            path,
            params=params,
            headers={"Authorization": token},
        )

    def _get(
        self,
        path: str,
        *,
        params: Mapping[str, str | None] | None,
        authorization: str | None,
    ) -> dict[str, Any]:
        headers: MutableMapping[str, str] = {}
        if authorization:
            headers["Authorization"] = authorization
        apply_internal_service_headers(headers)
        return self._request("GET", path, params=params, headers=headers)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None,
        headers: Mapping[str, str],
        json_body: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        query = ""
        if params:
            filtered = {
                k: str(v).lower() if isinstance(v, bool) else v
                for k, v in params.items()
                if v is not None and v != ""
            }
            if filtered:
                query = f"?{urlencode(filtered)}"

        url = f"{self._base_url}{path}{query}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.request(
                    method,
                    url,
                    headers=dict(headers),
                    json=dict(json_body) if json_body is not None else None,
                )
        except httpx.HTTPError as exc:
            raise StrategicIndicatorsApiError(
                f"Falha de rede ao consultar Strategic Indicators API: {exc}"
            ) from exc

        if response.status_code >= 400:
            raise StrategicIndicatorsApiError(
                f"Strategic Indicators API retornou {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        payload = response.json()
        if not isinstance(payload, dict):
            raise StrategicIndicatorsApiError(
                "Resposta inválida da Strategic Indicators API (esperado objeto JSON)."
            )
        return payload
