from __future__ import annotations

from typing import Any, Protocol


class LmpNonconformityCreateRepository(Protocol):
    def create_record(
        self,
        *,
        registered_at: str,
        status: str = "open",
        sale_number: str | None = None,
        branch_code: str | None = None,
        material_code: str | None = None,
        supplier_name: str | None = None,
        purchase_order: str | None = None,
        invoice_number: str | None = None,
        qty_received: float | None = None,
        qty_accepted: float | None = None,
        qty_rejected: float | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        product_codes: list[str] | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]: ...


class CreateLmpNonconformityUseCase:
    def __init__(self, repository: LmpNonconformityCreateRepository) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        registered_at: str,
        status: str = "open",
        sale_number: str | None = None,
        branch_code: str | None = None,
        material_code: str | None = None,
        supplier_name: str | None = None,
        purchase_order: str | None = None,
        invoice_number: str | None = None,
        qty_received: float | None = None,
        qty_accepted: float | None = None,
        qty_rejected: float | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        product_codes: list[str] | None = None,
        created_by: str | None = None,
    ) -> dict[str, Any]:
        return self._repository.create_record(
            registered_at=registered_at,
            status=status,
            sale_number=sale_number,
            branch_code=branch_code,
            material_code=material_code,
            supplier_name=supplier_name,
            purchase_order=purchase_order,
            invoice_number=invoice_number,
            qty_received=qty_received,
            qty_accepted=qty_accepted,
            qty_rejected=qty_rejected,
            defect_description=defect_description,
            corrective_actions=corrective_actions,
            technical_opinion=technical_opinion,
            product_codes=product_codes,
            created_by=created_by,
        )
