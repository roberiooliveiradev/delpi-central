"""Use case — tempo padrão canônico de uma operação de OP (leitura MES/S2S)."""

from __future__ import annotations

from typing import Any

from app.domain.ports.production.production_standard_time_repository_port import (
    ProductionStandardTimeRepositoryPort,
)
from app.domain.production.production_fabril_appointment_scope import (
    DEFAULT_PRODUCTION_BRANCHES,
)
from app.domain.production.production_standard_time import (
    compute_operation_standard_time,
)
from app.domain.services.production.production_operational_quantity_service import (
    ProductionOperationalQuantityService,
)


class GetProductionOperationStandardTimeUseCase:
    def __init__(
        self, repository: ProductionStandardTimeRepositoryPort
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any]:
        branch = str(branch or "").strip()
        if branch not in DEFAULT_PRODUCTION_BRANCHES:
            raise ValueError("Filial inválida.")

        row = self._repository.get_operation_standard_time_context(
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
        )
        if row is None:
            raise LookupError("Ordem de produção não encontrada.")
        if not int(row.get("operation_exists") or 0):
            raise LookupError(
                "Operação não encontrada na ordem de produção."
            )

        unit = str(row.get("unit") or "").strip() or None
        profile = ProductionOperationalQuantityService.resolve(unit)
        standard = compute_operation_standard_time(
            hy_tempad=row.get("hy_tempad"),
            hy_tempom=row.get("hy_tempom"),
            hy_quant=row.get("hy_quant"),
            g2_tempad=row.get("g2_tempad"),
            hy_setup=row.get("hy_setup"),
            g2_setup=row.get("g2_setup"),
            pieces_conversion_factor=profile.pieces_factor,
        )

        return {
            "branch": str(row.get("branch") or branch).strip(),
            "production_order": str(
                row.get("production_order") or production_order
            ).strip(),
            "operation_code": operation_code,
            "product_code": str(row.get("product_code") or "").strip() or None,
            "unit": unit,
            "pieces_conversion_factor": standard.pieces_conversion_factor,
            "standard_time_unit_hours": standard.standard_time_unit_hours,
            "ideal_cycle_seconds": standard.ideal_cycle_seconds,
            "setup_seconds": standard.setup_seconds,
            "standard_time_source": standard.standard_time_source,
            "data_quality": standard.data_quality,
        }
