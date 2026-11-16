"""Application service: user-parity READs against strategic-indicators-api.

Bounded adapter for the DAVI governed READ surface. The service forwards the
caller's own JWT to the SI API user-facing routes; the internal service token
is never attached, so the SI backend applies the caller's own
``strategic-indicators.*`` permissions (fail-closed).

No caching here: dashboards use service-token caches, but this path is
user-scoped — shared caches across users are not allowed.
"""

from __future__ import annotations

from typing import Any

from strategic_indicators_client import (
    StrategicIndicatorsApiClient,
    StrategicIndicatorsApiError,
)


def _require_authorization(authorization: str | None) -> str:
    token = (authorization or "").strip()
    if not token:
        raise StrategicIndicatorsApiError(
            "Token do usuário ausente para consulta a Strategic Indicators."
        )
    return token


class StrategicIndicatorsUserParityService:
    def __init__(self, client: StrategicIndicatorsApiClient | None = None) -> None:
        self._client = client or StrategicIndicatorsApiClient()

    def get_executive_summary(
        self,
        *,
        authorization: str | None,
        department_id: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_executive_summary(
            authorization=_require_authorization(authorization),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

    def get_departments(
        self,
        *,
        authorization: str | None,
        department_id: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_departments(
            authorization=_require_authorization(authorization),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

    def get_indicators(
        self,
        *,
        authorization: str | None,
        department_id: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_indicators(
            authorization=_require_authorization(authorization),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

    def list_indicator_goals(
        self,
        *,
        authorization: str | None,
        indicator_id: str | None = None,
        goal_year: int | None = None,
        department_id: str | None = None,
        active_only: bool | None = None,
    ) -> dict[str, Any]:
        return self._client.list_user_indicator_goals(
            authorization=_require_authorization(authorization),
            indicator_id=indicator_id,
            goal_year=goal_year,
            department_id=department_id,
            active_only=active_only,
        )

    def list_indicator_goal_history(
        self,
        *,
        authorization: str | None,
        indicator_id: str,
        goal_year: int | None = None,
    ) -> dict[str, Any]:
        return self._client.list_user_indicator_goal_history(
            authorization=_require_authorization(authorization),
            indicator_id=indicator_id,
            goal_year=goal_year,
        )


_si_user_parity_service: StrategicIndicatorsUserParityService | None = None


def get_si_user_parity_service() -> StrategicIndicatorsUserParityService:
    global _si_user_parity_service
    if _si_user_parity_service is None:
        _si_user_parity_service = StrategicIndicatorsUserParityService()
    return _si_user_parity_service
