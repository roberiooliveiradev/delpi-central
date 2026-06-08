from __future__ import annotations

import os

from si_app.application.dto.production.production_request import ProductionRequest
from si_app.domain.entities.production.on_time_delivery import OnTimeDelivery
from si_app.domain.entities.production.overall_equipment_effectiveness import OverallEquipmentEffectiveness
from si_app.domain.ports.production.on_time_delivery_repository_port import OnTimeDeliveryRepositoryPort
from si_app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)
from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient, DelpiApiError

_DEFAULT_BRANCHES = ["01", "02"]


def _known_branches() -> list[str]:
    env = os.getenv("DELPI_KNOWN_BRANCHES", "")
    if env.strip():
        return [b.strip() for b in env.split(",") if b.strip()]
    return list(_DEFAULT_BRANCHES)


def _std_params(
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, str | None]:
    return {"branch": branch, "start_date": start_date, "end_date": end_date}


def _opt_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class DelpiOeeGateway(OverallEquipmentEffectivenessRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_overall_equipment_effectiveness(
        self, request: ProductionRequest
    ) -> OverallEquipmentEffectiveness:
        data = self._client.get_overall_equipment_effectiveness(
            params=_std_params(request.branch, request.start_date, request.end_date),
            authorization=bearer_authorization_from_context(),
        )
        return OverallEquipmentEffectiveness(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            oee_pct=_opt_float(data.get("overall_equipment_effectiveness_pct")),
        )

    def list_overall_equipment_effectiveness_by_branch(
        self, request: ProductionRequest
    ) -> list[dict]:
        auth = bearer_authorization_from_context()
        results: list[dict] = []
        for branch in _known_branches():
            try:
                data = self._client.get_overall_equipment_effectiveness(
                    params=_std_params(branch, request.start_date, request.end_date),
                    authorization=auth,
                )
                oee_pct = _opt_float(data.get("overall_equipment_effectiveness_pct"))
                if oee_pct is not None:
                    results.append({"branch": branch, "oee_pct": oee_pct})
            except DelpiApiError:
                continue
        return results


class DelpiProductionSheetsGateway:
    """MO, custo de produção e depreciação via planilhas na api-delpi."""

    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client
        self._cache: dict[tuple, dict] = {}

    def _fetch_cached(self, key: tuple, fetcher: callable) -> dict:
        if key not in self._cache:
            self._cache[key] = fetcher()
        return self._cache[key]

    def get_direct_labor_cost_pct(self, request: ProductionRequest) -> float | None:
        key = ("direct-labor", request.branch or "", request.start_date or "", request.end_date or "")
        data = self._fetch_cached(
            key,
            lambda: self._client.get_direct_labor_cost_pct(
                params=_std_params(request.branch, request.start_date, request.end_date),
                authorization=bearer_authorization_from_context(),
            ),
        )
        return _opt_float(data.get("direct_labor_cost_pct"))

    def get_production_cost_pct(self, request: ProductionRequest) -> float | None:
        key = ("production-cost", request.branch or "", request.start_date or "", request.end_date or "")
        data = self._fetch_cached(
            key,
            lambda: self._client.get_production_cost_pct(
                params=_std_params(request.branch, request.start_date, request.end_date),
                authorization=bearer_authorization_from_context(),
            ),
        )
        return _opt_float(data.get("production_cost_pct"))

    def get_depreciation_pct(self, request: ProductionRequest) -> float | None:
        key = ("depreciation", request.branch or "", request.start_date or "", request.end_date or "")
        data = self._fetch_cached(
            key,
            lambda: self._client.get_depreciation_pct(
                params=_std_params(request.branch, request.start_date, request.end_date),
                authorization=bearer_authorization_from_context(),
            ),
        )
        return _opt_float(data.get("depreciation_pct"))


class DelpiOtdProductionGateway(OnTimeDeliveryRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_on_time_delivery(self, request: ProductionRequest) -> OnTimeDelivery:
        data = self._client.get_on_time_delivery(
            params=_std_params(request.branch, request.start_date, request.end_date),
            authorization=bearer_authorization_from_context(),
        )
        return OnTimeDelivery(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
            total_ops_finished=int(data.get("total_ops_finished") or 0),
            on_time_ops=int(data.get("on_time_ops") or 0),
            late_ops=int(data.get("late_ops") or 0),
            on_time_delivery_pct=_opt_float(data.get("on_time_delivery_pct")),
        )

    def list_on_time_delivery_by_branch(self, request: ProductionRequest) -> list[dict]:
        auth = bearer_authorization_from_context()
        results: list[dict] = []
        for branch in _known_branches():
            try:
                data = self._client.get_on_time_delivery(
                    params=_std_params(branch, request.start_date, request.end_date),
                    authorization=auth,
                )
                pct = _opt_float(data.get("on_time_delivery_pct"))
                if pct is not None:
                    results.append({"branch": branch, "on_time_delivery_pct": pct})
            except DelpiApiError:
                continue
        return results