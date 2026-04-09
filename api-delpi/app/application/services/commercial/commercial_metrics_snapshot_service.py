from __future__ import annotations

from dataclasses import dataclass

from app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from app.application.dto.commercial.new_clients_average_request import (
    NewClientsAverageRequest,
)
from app.application.dto.commercial.new_clients_rol_pct_request import (
    NewClientsRolPctRequest,
)
from app.application.dto.commercial.sales_conversion_rate_request import (
    SalesConversionRateRequest,
)
from app.application.use_cases.commercial.get_new_clients_average_use_case import (
    GetNewClientsAverageUseCase,
)
from app.application.use_cases.commercial.get_new_clients_rol_pct_use_case import (
    GetNewClientsRolPctUseCase,
)
from app.application.use_cases.commercial.get_rol_target_pct_use_case import (
    GetRolTargetPctUseCase,
)
from app.application.use_cases.commercial.get_sales_conversion_rate_use_case import (
    GetSalesConversionRateUseCase,
)


@dataclass(frozen=True)
class CommercialMetricsSnapshot:
    start_date: str | None
    end_date: str | None
    matrix_rol_target_pct: float
    branch_rol_target_pct: float
    sales_conversion_rate_pct: float
    monthly_average_new_clients: float
    new_clients_rol_pct: float


class CommercialMetricsSnapshotService:
    def __init__(
        self,
        *,
        head_office_rol_target_use_case: GetRolTargetPctUseCase,
        branch_rol_target_use_case: GetRolTargetPctUseCase,
        sales_conversion_rate_use_case: GetSalesConversionRateUseCase,
        new_clients_average_use_case: GetNewClientsAverageUseCase,
        new_clients_rol_pct_use_case: GetNewClientsRolPctUseCase,
    ) -> None:
        self._head_office_rol_target_use_case = head_office_rol_target_use_case
        self._branch_rol_target_use_case = branch_rol_target_use_case
        self._sales_conversion_rate_use_case = sales_conversion_rate_use_case
        self._new_clients_average_use_case = new_clients_average_use_case
        self._new_clients_rol_pct_use_case = new_clients_rol_pct_use_case
        self._cache: dict[tuple[str | None, str | None], CommercialMetricsSnapshot] = {}

    def get_snapshot(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> CommercialMetricsSnapshot:
        key = (start_date, end_date)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        matrix_target_result = self._head_office_rol_target_use_case.execute(
            CommercialTargetRequest(
                branch="01",
                start_date=start_date,
                end_date=end_date,
            )
        )
        branch_target_result = self._branch_rol_target_use_case.execute(
            CommercialTargetRequest(
                branch="02",
                start_date=start_date,
                end_date=end_date,
            )
        )
        sales_conversion_result = self._sales_conversion_rate_use_case.execute(
            SalesConversionRateRequest(
                branch=None,
                start_date=start_date,
                end_date=end_date,
            )
        )
        new_clients_average_result = self._new_clients_average_use_case.execute(
            NewClientsAverageRequest(
                branch=None,
                start_date=start_date,
                end_date=end_date,
            )
        )
        new_clients_rol_result = self._new_clients_rol_pct_use_case.execute(
            NewClientsRolPctRequest(
                branch=None,
                start_date=start_date,
                end_date=end_date,
            )
        )

        snapshot = CommercialMetricsSnapshot(
            start_date=start_date,
            end_date=end_date,
            matrix_rol_target_pct=self._extract_number(
                matrix_target_result,
                ["rol_target_pct"],
            ) or 0.0,
            branch_rol_target_pct=self._extract_number(
                branch_target_result,
                ["rol_target_pct"],
            ) or 0.0,
            sales_conversion_rate_pct=self._extract_number(
                sales_conversion_result,
                ["sales_conversion_rate_pct"],
            ) or 0.0,
            monthly_average_new_clients=self._extract_number(
                new_clients_average_result,
                ["monthly_average"],
            ) or 0.0,
            new_clients_rol_pct=self._extract_number(
                new_clients_rol_result,
                ["new_clients_rol_pct"],
            ) or 0.0,
        )
        self._cache[key] = snapshot
        return snapshot

    def _extract_number(self, payload, candidate_keys: list[str]) -> float | None:
        if payload is None:
            return None

        if isinstance(payload, dict):
            for key in candidate_keys:
                value = payload.get(key)
                number = self._to_float(value)
                if number is not None:
                    return number

        return None

    def _to_float(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None