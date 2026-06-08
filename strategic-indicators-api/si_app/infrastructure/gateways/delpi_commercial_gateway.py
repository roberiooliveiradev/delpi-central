from __future__ import annotations

from si_app.application.dto.commercial.new_business_rol_pct_request import NewBusinessRolPctRequest
from si_app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from si_app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest

from si_app.domain.entities.commercial.new_business_rol_pct import NewBusinessRolPct
from si_app.domain.entities.commercial.sales_conversion_rate import SalesConversionRate
from si_app.domain.entities.commercial.sales_order_otd import SalesOrderOtd

from si_app.domain.ports.commercial.new_business_rol_pct_repository_port import NewBusinessRolPctRepositoryPort
from si_app.domain.ports.commercial.sales_conversion_rate_repository_port import SalesConversionRateRepositoryPort
from si_app.domain.ports.commercial.sales_order_otd_repository_port import SalesOrderOtdRepositoryPort

from si_app.infrastructure.http.auth_header import bearer_authorization_from_context
from delpi_api_client import DelpiApiClient


def _std_params(
    branch: str | None,
    start_date: str | None,
    end_date: str | None,
) -> dict[str, str | None]:
    return {"branch": branch, "start_date": start_date, "end_date": end_date}


class DelpiNewBusinessRolPctGateway(NewBusinessRolPctRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_new_business_rol_pct(self, request: NewBusinessRolPctRequest) -> NewBusinessRolPct:
        data = self._client.get_new_business_rol_pct(
            params=_std_params(request.branch, request.start_date, request.end_date),
            authorization=bearer_authorization_from_context(),
        )
        return NewBusinessRolPct(
            branch=data.get("branch"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            total_rol=float(data.get("total_rol") or 0),
            new_business_rol=float(data.get("new_business_rol") or 0),
            weg_rol=float(data.get("weg_rol") or 0),
            new_business_rol_pct=_opt_float(data.get("new_business_rol_pct")),
        )


class DelpiSalesConversionRateGateway(SalesConversionRateRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_sales_conversion_rate(self, request: SalesConversionRateRequest) -> SalesConversionRate:
        data = self._client.get_sales_conversion_rate(
            params=_std_params(request.branch, request.start_date, request.end_date),
            authorization=bearer_authorization_from_context(),
        )
        return SalesConversionRate(
            branch=data.get("branch"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            qtd_proposals=int(data.get("qtd_proposals") or 0),
            qtd_won=int(data.get("qtd_won") or 0),
            sales_conversion_rate_pct=_opt_float(data.get("sales_conversion_rate_pct")),
        )


class DelpiSalesOrderOtdGateway(SalesOrderOtdRepositoryPort):
    def __init__(self, client: DelpiApiClient) -> None:
        self._client = client

    def get_sales_order_otd(self, request: SalesOrderOtdRequest) -> SalesOrderOtd:
        data = self._client.get_sales_order_otd(
            params=_std_params(request.branch, request.start_date, request.end_date),
            authorization=bearer_authorization_from_context(),
        )
        return SalesOrderOtd(
            branch=data.get("branch"),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            total_lines=int(data.get("total_lines") or 0),
            on_time_lines=int(data.get("on_time_lines") or 0),
            late_lines=int(data.get("late_lines") or 0),
            sales_order_otd_pct=_opt_float(data.get("sales_order_otd_pct")),
        )


def _opt_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
