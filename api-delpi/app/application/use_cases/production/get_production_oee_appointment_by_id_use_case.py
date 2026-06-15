from __future__ import annotations

from app.application.dto.product.list_product_guide_request import (
    ListProductGuideRequest,
)
from app.application.dto.product.list_product_structured_request import (
    ListProductStructureRequest,
)
from app.application.dto.production.get_production_oee_appointment_by_id_request import (
    GetProductionOeeAppointmentByIdRequest,
)
from app.application.use_cases.product.list_product_guide_use_case import (
    ListProductGuideUseCase,
)
from app.application.use_cases.product.list_product_structure_use_case import (
    ListProductStructureUseCase,
)
from app.domain.production.production_appointment_time_analysis import (
    build_appointment_time_analysis,
)
from app.domain.ports.production.overall_equipment_effectiveness_repository_port import (
    OverallEquipmentEffectivenessRepositoryPort,
)


class GetProductionOeeAppointmentByIdUseCase:
    def __init__(
        self,
        overall_equipment_effectiveness_repository: OverallEquipmentEffectivenessRepositoryPort,
        list_product_guide_use_case: ListProductGuideUseCase,
        list_product_structure_use_case: ListProductStructureUseCase,
    ):
        self._repository = overall_equipment_effectiveness_repository
        self._list_product_guide_use_case = list_product_guide_use_case
        self._list_product_structure_use_case = list_product_structure_use_case

    def execute(self, request: GetProductionOeeAppointmentByIdRequest) -> dict | None:
        appointment_id = int(request.appointment_id)
        if appointment_id <= 0:
            raise ValueError("appointment_id inválido.")

        appointment = self._repository.get_oee_appointment_by_id(
            appointment_id,
            branch=request.branch,
        )
        if not appointment:
            return None

        product_code = str(appointment.get("product_code") or "").strip()
        branch = str(appointment.get("branch") or request.branch or "").strip() or None
        operation = str(appointment.get("operation") or "").strip()

        routing_operations: list[dict] = []
        structure: dict = {
            "root": None,
            "items": [],
            "total": 0,
        }

        if product_code:
            guide = self._list_product_guide_use_case.execute(
                ListProductGuideRequest(
                    code=product_code,
                    branch=branch,
                    max_depth=6,
                )
            )
            routing_operations = self._unique_routing_operations(
                guide.get("items") or [],
                highlight_operation=operation,
            )

            structure = self._list_product_structure_use_case.execute(
                ListProductStructureRequest(
                    code=product_code,
                    page=1,
                    page_size=200,
                    max_depth=6,
                )
            )

        return {
            "appointment": appointment,
            "time_analysis": build_appointment_time_analysis(appointment),
            "routing_operations": routing_operations,
            "structure": structure,
            "related_routes": {
                "production_order": (
                    f"/production/orders/by-op/{appointment.get('production_order')}"
                    if appointment.get("production_order")
                    else None
                ),
                "product_guide": f"/products/{product_code}/guide" if product_code else None,
                "product_structure": (
                    f"/products/{product_code}/structure" if product_code else None
                ),
            },
        }

    @staticmethod
    def _unique_routing_operations(
        items: list,
        *,
        highlight_operation: str,
    ) -> list[dict]:
        seen: set[tuple[str, str]] = set()
        operations: list[dict] = []

        for raw in items:
            row = raw.to_dict() if hasattr(raw, "to_dict") else dict(raw)
            key = (
                str(row.get("product_code") or "").strip(),
                str(row.get("operation_code") or "").strip(),
            )
            if not key[0] or not key[1] or key in seen:
                continue

            seen.add(key)
            operations.append(
                {
                    **row,
                    "is_appointment_operation": key[1] == highlight_operation,
                }
            )

        operations.sort(
            key=lambda item: (
                0 if item.get("is_appointment_operation") else 1,
                int(item.get("bom_level") or 0),
                str(item.get("product_code") or ""),
                str(item.get("operation_code") or ""),
            )
        )
        return operations

