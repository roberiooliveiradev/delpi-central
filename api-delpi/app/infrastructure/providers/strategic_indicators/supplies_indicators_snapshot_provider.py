from __future__ import annotations

from app.application.dto.supplies.get_cpv_request import GetCPVRequest
from app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)
from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.use_cases.supplies.get_cpv_use_case import GetCPVUseCase
from app.application.use_cases.supplies.get_inventory_turnover_use_case import (
    GetInventoryTurnoverUseCase,
)
from app.application.use_cases.supplies.get_otd_use_case import GetOTDUseCase
from app.application.use_cases.supplies.get_stock_value_use_case import (
    GetStockValueUseCase,
)
from app.domain.ports.strategic_indicators.supplies_indicators_snapshot_port import (
    StrategicIndicatorsSuppliesIndicatorsSnapshotPort,
)


class SuppliesIndicatorsSnapshotProvider(
    StrategicIndicatorsSuppliesIndicatorsSnapshotPort,
):
    def __init__(
        self,
        *,
        get_cpv_use_case: GetCPVUseCase,
        get_inventory_turnover_use_case: GetInventoryTurnoverUseCase,
        get_otd_use_case: GetOTDUseCase,
        get_stock_value_use_case: GetStockValueUseCase,
    ) -> None:
        self._get_cpv_use_case = get_cpv_use_case
        self._get_inventory_turnover_use_case = get_inventory_turnover_use_case
        self._get_otd_use_case = get_otd_use_case
        self._get_stock_value_use_case = get_stock_value_use_case

    def get_supplies_indicators_snapshot(
        self,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        branch: str | None = None,
    ) -> dict:
        items: list[dict] = []
        errors: list[dict] = []

        self._collect_indicator(
            builder=lambda: self._build_cpv_measurement(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            ),
            department_id="supplies",
            source="supplies_cpv",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_inventory_turnover_measurement(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            ),
            department_id="supplies",
            source="supplies_inventory_turnover",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_otd_measurement(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            ),
            department_id="supplies",
            source="supplies_otd",
            items=items,
            errors=errors,
        )

        self._collect_indicator(
            builder=lambda: self._build_stock_value_measurement(
                branch=branch,
            ),
            department_id="supplies",
            source="supplies_stock_value",
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

    def _extract_payload(self, result):
        return result.to_dict() if hasattr(result, "to_dict") else result

    def _extract_data(self, payload: dict) -> dict:
        return payload.get("data", payload)

    def _build_cpv_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict:
        request = GetCPVRequest(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        result = self._get_cpv_use_case.execute(request)
        payload = self._extract_payload(result)

        data = self._extract_data(payload)
        summary = data.get("summary", {})
        value = float(summary.get("cpv_percentage") or 0.0)
        unit_key = branch or "consolidated"

        return {
            "department_id": "supplies",
            "indicator_id": "supplies-cpv",
            "value": value,
            "source": "supplies_cpv",
            "unit_values": {unit_key: value},
        }

    def _build_inventory_turnover_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict:
        request = GetInventoryTurnoverRequest(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            strict_idd_period=False,
        )
        result = self._get_inventory_turnover_use_case.execute(request)
        payload = self._extract_payload(result)

        data = self._extract_data(payload)
        summary = data.get("summary", {})
        value = float(summary.get("inventory_turnover_months") or 0.0)
        unit_key = branch or "consolidated"

        return {
            "department_id": "supplies",
            "indicator_id": "supplies-stock-turnover",
            "value": value,
            "source": "supplies_inventory_turnover",
            "unit_values": {unit_key: value},
        }

    def _build_otd_measurement(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
    ) -> dict:
        request = GetOTDRequest(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )
        result = self._get_otd_use_case.execute(request)
        payload = self._extract_payload(result)

        data = self._extract_data(payload)
        summary = data.get("summary", {})
        value = float(summary.get("otd_percentage") or 0.0)
        unit_key = branch or "consolidated"

        return {
            "department_id": "supplies",
            "indicator_id": "supplies-otd",
            "value": value,
            "source": "supplies_otd",
            "unit_values": {unit_key: value},
        }

    def _build_stock_value_measurement(
        self,
        *,
        branch: str | None,
    ) -> dict:
        request = GetStockValueRequest(
            branch=branch,
        )
        result = self._get_stock_value_use_case.execute(request)
        payload = self._extract_payload(result)

        data = self._extract_data(payload)
        summary = data.get("summary", {})
        value = float(summary.get("total_stock_value") or 0.0)
        unit_key = branch or "consolidated"

        return {
            "department_id": "supplies",
            "indicator_id": "supplies-stock-value",
            "value": value,
            "source": "supplies_stock_value",
            "unit_values": {unit_key: value},
        }