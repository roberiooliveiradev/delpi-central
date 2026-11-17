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


def _project_top_level(
    payload: dict[str, Any], include: str | None
) -> dict[str, Any]:
    """BFF-side section projection for owner routes that take no query params.

    ``include`` is a comma-separated allowlist of top-level response keys; the
    owner payload stays authoritative — the BFF only narrows the projection.
    """
    if include is None or not isinstance(payload, dict):
        return payload
    requested = {part.strip() for part in include.split(",") if part.strip()}
    return {key: value for key, value in payload.items() if key in requested}


def _paginate_items(
    payload: dict[str, Any],
    *,
    limit: int | None,
    offset: int | None,
) -> dict[str, Any]:
    """BFF-side pagination over an owner ``items`` list (no owner params)."""
    if limit is None and offset is None:
        return payload
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return payload
    start = max(int(offset or 0), 0)
    page = items[start:] if limit is None else items[start : start + int(limit)]
    out = dict(payload)
    out["items"] = page
    out["total"] = len(items)
    out["limit"] = limit
    out["offset"] = start
    return out


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

    def get_department_details(
        self,
        *,
        authorization: str | None,
        department_id: str,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_department_details(
            authorization=_require_authorization(authorization),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

    def get_departments_tree(
        self,
        *,
        authorization: str | None,
        view_mode: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        months: int | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_departments_tree(
            authorization=_require_authorization(authorization),
            view_mode=view_mode,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            months=months,
        )

    def get_departments_tree_snapshot(
        self,
        *,
        authorization: str | None,
        view_mode: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_departments_tree_snapshot(
            authorization=_require_authorization(authorization),
            view_mode=view_mode,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

    def get_departments_tree_trends(
        self,
        *,
        authorization: str | None,
        view_mode: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        months: int | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_departments_tree_trends(
            authorization=_require_authorization(authorization),
            view_mode=view_mode,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            months=months,
        )

    def get_alerts(
        self,
        *,
        authorization: str | None,
        department_id: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_alerts(
            authorization=_require_authorization(authorization),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
        )

    def get_trends(
        self,
        *,
        authorization: str | None,
        department_id: str | None = None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        months: int | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_trends(
            authorization=_require_authorization(authorization),
            department_id=department_id,
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            months=months,
        )

    def get_presentation(
        self,
        *,
        authorization: str | None,
        branch: str | None = None,
        competence: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        months: int | None = None,
        include: str | None = None,
    ) -> dict[str, Any]:
        return self._client.get_user_presentation(
            authorization=_require_authorization(authorization),
            branch=branch,
            competence=competence,
            start_date=start_date,
            end_date=end_date,
            months=months,
            include=include,
        )

    def get_cache_refresh_status(
        self,
        *,
        authorization: str | None,
        include: str | None = None,
    ) -> dict[str, Any]:
        payload = self._client.get_user_cache_refresh_status(
            authorization=_require_authorization(authorization),
        )
        return _project_top_level(payload, include)

    def get_job_status(
        self,
        *,
        authorization: str | None,
        job_id: str,
    ) -> dict[str, Any]:
        return self._client.get_user_job_status(
            authorization=_require_authorization(authorization),
            job_id=job_id,
        )

    def get_settings(
        self,
        *,
        authorization: str | None,
        include: str | None = None,
    ) -> dict[str, Any]:
        payload = self._client.get_user_settings(
            authorization=_require_authorization(authorization),
        )
        return _project_top_level(payload, include)

    def list_settings_audit(
        self,
        *,
        authorization: str | None,
        limit: int | None = None,
        entity_key: str | None = None,
    ) -> dict[str, Any]:
        return self._client.list_user_settings_audit(
            authorization=_require_authorization(authorization),
            limit=limit,
            entity_key=entity_key,
        )

    def list_change_requests(
        self,
        *,
        authorization: str | None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        return self._client.list_user_change_requests(
            authorization=_require_authorization(authorization),
            limit=limit,
            offset=offset,
        )

    def list_admin_departments(
        self,
        *,
        authorization: str | None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        payload = self._client.list_user_admin_departments(
            authorization=_require_authorization(authorization),
        )
        return _paginate_items(payload, limit=limit, offset=offset)

    def list_admin_department_indicators(
        self,
        *,
        authorization: str | None,
        department_id: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        payload = self._client.list_user_admin_department_indicators(
            authorization=_require_authorization(authorization),
            department_id=department_id,
        )
        return _paginate_items(payload, limit=limit, offset=offset)

    def list_goal_years_overview(
        self,
        *,
        authorization: str | None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict[str, Any]:
        payload = self._client.list_user_goal_years_overview(
            authorization=_require_authorization(authorization),
        )
        return _paginate_items(payload, limit=limit, offset=offset)

    def export_admin_config(
        self,
        *,
        authorization: str | None,
        include: str | None = None,
    ) -> dict[str, Any]:
        payload = self._client.export_user_admin_config(
            authorization=_require_authorization(authorization),
        )
        return _project_top_level(payload, include)


_si_user_parity_service: StrategicIndicatorsUserParityService | None = None


def get_si_user_parity_service() -> StrategicIndicatorsUserParityService:
    global _si_user_parity_service
    if _si_user_parity_service is None:
        _si_user_parity_service = StrategicIndicatorsUserParityService()
    return _si_user_parity_service
