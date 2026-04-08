from __future__ import annotations

from app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from app.application.dto.commercial.new_clients_average_request import NewClientsAverageRequest
from app.application.dto.commercial.new_clients_rol_pct_request import NewClientsRolPctRequest
from app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
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
from app.domain.ports.strategic_indicators.commercial_indicators_snapshot_port import (
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
)


class CommercialIndicatorsSnapshotProvider(
    StrategicIndicatorsCommercialIndicatorsSnapshotPort,
):
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

    def get_commercial_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        self._collect_indicator(
            builder=lambda: self._build_head_office_rol_target_measurement(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_head_office_rol_target",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_branch_rol_target_measurement(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_branch_rol_target",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_sales_conversion_rate_measurement(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_sales_conversion_rate",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_new_clients_average_measurement(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_new_clients_average",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_new_clients_rol_pct_measurement(
                start_date=start_date,
                end_date=end_date,
            ),
            department_id="commercial",
            source="commercial_new_clients_rol_pct",
            items=items,
            errors=errors,
        )

        return {
            "items": items,
            "errors": errors,
        }

    def _collect_indicator(
        self,
        *,
        builder,
        department_id: str,
        source: str,
        items: list[dict],
        errors: list[dict],
    ) -> None:
        try:
            items.append(builder())
        except Exception as exc:
            errors.append(
                {
                    "department_id": department_id,
                    "source": source,
                    "message": str(exc),
                }
            )

    def _build_head_office_rol_target_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = CommercialTargetRequest(
            branch="01",
            start_date=start_date,
            end_date=end_date,
        )

        result = self._head_office_rol_target_use_case.execute(request)
        value = self._to_float(result.get("rol_target_pct")) or 0.0

        return {
            "department_id": "commercial",
            "indicator_id": "commercial-rol-matrix",
            "value": value,
            "source": "commercial_head_office_rol_target",
            "unit_values": {
                "matrix": value,
            },
        }

    def _build_branch_rol_target_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = CommercialTargetRequest(
            branch="02",
            start_date=start_date,
            end_date=end_date,
        )

        result = self._branch_rol_target_use_case.execute(request)
        value = self._to_float(result.get("rol_target_pct")) or 0.0

        return {
            "department_id": "commercial",
            "indicator_id": "commercial-rol-branch",
            "value": value,
            "source": "commercial_branch_rol_target",
            "unit_values": {
                "branch": value,
            },
        }

    def _build_sales_conversion_rate_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = SalesConversionRateRequest(
            branch=None,
            start_date=start_date,
            end_date=end_date,
        )

        result = self._sales_conversion_rate_use_case.execute(request)
        value = self._to_float(result.get("sales_conversion_rate_pct")) or 0.0

        return {
            "department_id": "commercial",
            "indicator_id": "commercial-closing-rate",
            "value": value,
            "source": "commercial_sales_conversion_rate",
            "unit_values": {
                "consolidated": value,
            },
        }

    def _build_new_clients_average_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = NewClientsAverageRequest(
            branch=None,
            start_date=start_date,
            end_date=end_date,
        )

        result = self._new_clients_average_use_case.execute(request)
        value = self._to_float(result.get("monthly_average")) or 0.0

        return {
            "department_id": "commercial",
            "indicator_id": "commercial-new-clients",
            "value": value,
            "source": "commercial_new_clients_average",
            "unit_values": {
                "consolidated": value,
            },
        }

    def _build_new_clients_rol_pct_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
    ) -> dict:
        request = NewClientsRolPctRequest(
            branch=None,
            start_date=start_date,
            end_date=end_date,
        )

        result = self._new_clients_rol_pct_use_case.execute(request)
        value = self._to_float(result.get("new_clients_rol_pct")) or 0.0

        return {
            "department_id": "commercial",
            "indicator_id": "commercial-new-rol",
            "value": value,
            "source": "commercial_new_clients_rol_pct",
            "unit_values": {
                "consolidated": value,
            },
        }

    def _to_float(self, value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None