from __future__ import annotations

from app.application.dto.production.get_production_oee_request import (
    GetProductionOeeRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.shared.numeric_parsing import to_optional_float
from app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)
from app.domain.services.production.production_operational_quantity_service import (
    ProductionOperationalQuantityService,
)


class GetProductionOeeUseCase:
    def __init__(
        self,
        overall_equipment_effectiveness_repository: OverallEquipmentEffectivenessRepositoryPort,
    ):
        self._repository = overall_equipment_effectiveness_repository

    @staticmethod
    def _has_appointment_scope_filters(request: GetProductionOeeRequest) -> bool:
        def has_value(value: str | None) -> bool:
            return bool(value and str(value).strip())

        return any(
            [
                has_value(request.production_order),
                has_value(request.work_center),
                has_value(request.operator_code),
                has_value(request.product_type),
                has_value(request.efficiency_bands),
                has_value(request.status),
            ]
        )

    def execute(self, request: GetProductionOeeRequest) -> dict:
        production_request = ProductionRequest(
            branch=request.branch,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        appointment_summary, appointments_page = (
            self._repository.get_oee_appointments_bundle(request)
        )
        total_appointments = int(appointment_summary.get("total_appointments") or 0)
        valid_appointments = int(appointment_summary.get("valid_appointments") or 0)
        outlier_appointments = int(
            appointment_summary.get("outlier_appointments") or 0
        )
        outlier_percentage = (
            round(outlier_appointments * 100.0 / total_appointments, 2)
            if total_appointments > 0
            else 0.0
        )

        if self._has_appointment_scope_filters(request):
            oee_pct = to_optional_float(appointment_summary.get("avg_oee_pct"))
        elif request.branch:
            summary_entity = self._repository.get_overall_equipment_effectiveness(
                production_request
            )
            oee_pct = to_optional_float(summary_entity.oee_pct)
        else:
            rows = self._repository.list_overall_equipment_effectiveness_by_branch(
                production_request
            )
            valid_rows = [
                row
                for row in rows
                if row.get("oee_pct") is not None and row.get("branch")
            ]
            if valid_rows:
                oee_pct = round(
                    sum(float(row["oee_pct"]) for row in valid_rows)
                    / len(valid_rows),
                    2,
                )
            else:
                oee_pct = None

        appointments_payload = appointments_page.to_dict()
        appointments_payload["items"] = ProductionOperationalQuantityService.normalize_items(
            appointments_payload.get("items") or []
        )

        return {
            "branch": request.branch or "consolidated",
            "start_date": request.start_date or "",
            "end_date": request.end_date or "",
            "summary": {
                "oee_pct": round(oee_pct, 2) if oee_pct is not None else None,
                "total_appointments": total_appointments,
                "valid_appointments": valid_appointments,
                "outlier_appointments": outlier_appointments,
                "outlier_percentage": outlier_percentage,
            },
            "appointments": appointments_payload,
        }
