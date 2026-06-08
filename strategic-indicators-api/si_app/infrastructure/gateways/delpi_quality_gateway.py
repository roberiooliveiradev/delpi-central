from __future__ import annotations

from typing import Any, Callable

from si_app.application.dto.auditoria_5s.audit_5s_summary_request import (
    Audit5SSummaryRequest,
)
from si_app.application.dto.auditoria_5s.audit_5s_summary_response import (
    Audit5SSummaryResponse,
)
from si_app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from si_app.application.dto.kaizen.kaizen_summary_response import KaizenSummaryResponse
from si_app.domain.entities.audit_5s.audit_5s import Audit5S
from si_app.domain.entities.kaizen.kaizen import Kaizen
from si_app.domain.entities.ppm.ppm_summary import PpmSummary
from si_app.domain.ports.audit_5s.audit_5s_query_port import Audit5SQueryRepositoryPort
from si_app.domain.ports.kaizen.kaizen_query_port import KaizenQueryRepositoryPort
from si_app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort

from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


def _cache_key(*parts: str | None) -> tuple:
    return tuple(part or "" for part in parts)


class _CachedFetch:
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client
        self._cache: dict[tuple, dict[str, Any]] = {}

    def _fetch_cached(self, key: tuple, fetcher: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        if key not in self._cache:
            self._cache[key] = fetcher()
        return self._cache[key]


def _opt_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class DelpiPpmGateway(PpmQueryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_summary(self, request) -> PpmSummary:
        data = self._client.get_ppm_summary(
            request.type,
            params={
                "branch": getattr(request, "branch", None),
                "date_start": getattr(request, "date_start", None),
                "date_end": getattr(request, "date_end", None),
            },
            authorization=bearer_authorization_from_context(),
        )
        return PpmSummary(
            type=request.type,
            branch=data.get("branch") or getattr(request, "branch", None),
            date_start=data.get("date_start") or getattr(request, "date_start", None),
            date_end=data.get("date_end") or getattr(request, "date_end", None),
            total_devolvido_un=float(data.get("total_devolvido_un") or 0),
            total_produzido_milheiro=float(data.get("total_produzido_milheiro") or 0),
            total_produzido_un=float(data.get("total_produzido_un") or 0),
            ppm=float(data.get("ppm") or 0),
        )

    def list_branches(
        self,
        *,
        ppm_type: str,
        date_start: str | None,
        date_end: str | None,
    ) -> list[str]:
        data = self._client.list_quality_branches(
            params={"date_start": date_start, "date_end": date_end},
            authorization=bearer_authorization_from_context(),
        )
        branches = data.get("branches") or data.get("items") or []
        if isinstance(branches, list) and all(isinstance(b, str) for b in branches):
            return branches
        return [str(b) for b in branches if b]


def _opt_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _map_kaizen_summary(data: dict[str, Any]) -> KaizenSummaryResponse:
    items = [
        Kaizen(
            id=str(it.get("id") or ""),
            title=str(it.get("title") or ""),
            date_implemented=_opt_str(it.get("date_implemented")),
            status=_opt_str(it.get("status")),
            accountable=_opt_str(it.get("accountable")),
            sector=_opt_str(it.get("sector")),
            investment=_opt_float(it.get("investment")),
            daily_savings=_opt_float(it.get("daily_savings")),
            branch=_opt_str(it.get("branch")),
        )
        for it in (data.get("list_kaizen") or [])
    ]
    return KaizenSummaryResponse(
        date_start=_opt_str(data.get("date_start")),
        date_end=_opt_str(data.get("date_end")),
        total_kaizens=int(data.get("total_kaizens") or 0),
        total_savings=float(data.get("total_savings") or 0),
        list_kaizen=items,
    )


def _map_audit_5s_summary(data: dict[str, Any]) -> Audit5SSummaryResponse:
    items = [
        Audit5S(
            id=str(it.get("id") or ""),
            date=_opt_str(it.get("date")),
            average_line_score=_opt_float(it.get("average_line_score")),
            evaluated_area=_opt_str(it.get("evaluated_area")),
            auditor=_opt_str(it.get("auditor")),
            audited=_opt_str(it.get("audited")),
            inspection_number=_opt_str(it.get("inspection_number")),
            shift=_opt_str(it.get("shift")),
            branch=_opt_str(it.get("branch")),
        )
        for it in (data.get("list_audits") or [])
    ]
    return Audit5SSummaryResponse(
        start_date=_opt_str(data.get("start_date")),
        end_date=_opt_str(data.get("end_date")),
        average_score=float(data.get("average_score") or 0),
        list_audits=items,
    )


class DelpiKaizenGateway(_CachedFetch, KaizenQueryRepositoryPort):
    def get_kaizen_summary(self, request: KaizenSummaryRequest) -> KaizenSummaryResponse:
        key = _cache_key(
            "kaizen",
            request.branch,
            request.date_start,
            request.date_end,
            request.title,
            request.status,
        )
        data = self._fetch_cached(
            key,
            lambda: self._client.get_kaizen_summary(
                params={
                    "branch": request.branch,
                    "date_start": request.date_start,
                    "date_end": request.date_end,
                    "title": request.title,
                    "status": request.status,
                },
                authorization=bearer_authorization_from_context(),
            ),
        )
        return _map_kaizen_summary(data)


class DelpiAudit5SGateway(_CachedFetch, Audit5SQueryRepositoryPort):
    def get_audit_summary(self, request: Audit5SSummaryRequest) -> Audit5SSummaryResponse:
        key = _cache_key(
            "audit-5s",
            request.branch,
            request.start_date,
            request.end_date,
        )
        data = self._fetch_cached(
            key,
            lambda: self._client.get_audit_5s_summary(
                params={
                    "branch": request.branch,
                    "start_date": request.start_date,
                    "end_date": request.end_date,
                },
                authorization=bearer_authorization_from_context(),
            ),
        )
        return _map_audit_5s_summary(data)