"""PREPARE de mutação NC — validação + diff sem efeitos colaterais.

Capacidade EVA PREPARE (T5): analisa uma mutação candidata
(create/update), retorna payload normalizado, violações de validação e
diff projetado sobre o estado atual — SEM gravar nada. O resultado é
insumo para confirmação humana; ACT permanece desabilitado.
"""

from __future__ import annotations

import asyncio
from typing import Any

from engineering_app.application.ports.nonconformity_repository import (
    NonconformityRepository,
)
from engineering_app.application.use_cases.nonconformity.write import (
    normalize_nc_payload,
)
from engineering_app.domain.nonconformity.errors import (
    NcNotFoundError,
    NcValidationError,
)
from engineering_app.domain.nonconformity.history_diff import (
    build_nc_history_changes,
)

PREPARE_OPERATIONS = ("create", "update")


class PrepareNonconformityMutationUseCase:
    """Dry-run de mutação NC: valida, normaliza e projeta o diff."""

    def __init__(self, repository: NonconformityRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        *,
        operation: str,
        payload: dict[str, Any],
        record_id: str | None = None,
    ) -> dict[str, Any]:
        op = (operation or "").strip().lower()
        if op not in PREPARE_OPERATIONS:
            raise NcValidationError(
                f"operation inválida: {operation} (use create|update).",
                fields={"operation": str(operation)},
            )

        current: dict[str, Any] | None = None
        if op == "update":
            if not record_id:
                raise NcValidationError(
                    "record_id é obrigatório para operation=update.",
                    fields={"record_id": "required"},
                )
            current = await asyncio.to_thread(
                self._repository.get_record, record_id
            )
            if current is None:
                raise NcNotFoundError(record_id)

        validation_errors: list[dict[str, str]] = []
        normalized: dict[str, Any] | None = None
        try:
            normalized = normalize_nc_payload(
                payload, require_occurrence=(op == "update")
            )
        except NcValidationError as exc:
            validation_errors.append(
                {"message": str(exc), **exc.fields}
            )

        projected_changes: dict[str, Any] = {"fields": []}
        if normalized is not None:
            before = (
                {
                    "status": current.get("status"),
                    "sale_number": current.get("sale_number"),
                    "lmp_number": current.get("lmp_number"),
                    "customer_name": current.get("customer_name"),
                    "occurrence_date": current.get("occurrence_date"),
                    "launch_date": current.get("launch_date"),
                    "last_revision_date": current.get("last_revision_date"),
                    "executed_by": current.get("executed_by"),
                    "released_by": current.get("released_by"),
                    "defect_description": current.get("defect_description"),
                    "corrective_actions": current.get("corrective_actions"),
                    "technical_opinion": current.get("technical_opinion"),
                    "problem_tags": current.get("problem_tags") or [],
                    "products": current.get("products") or [],
                }
                if current
                else None
            )
            projected_changes = build_nc_history_changes(
                before, _snapshot_from_normalized(normalized)
            )

        return {
            "operation": op,
            "record_id": record_id,
            "valid": normalized is not None and not validation_errors,
            "validation_errors": validation_errors,
            "normalized": normalized,
            "current": current,
            "projected_changes": projected_changes,
            "requires_human_confirmation": True,
            "side_effects": "none",
        }


def _snapshot_from_normalized(normalized: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": normalized["status"],
        "sale_number": normalized["sale_number"],
        "lmp_number": normalized["lmp_number"],
        "customer_name": normalized["customer_name"],
        "occurrence_date": normalized["occurrence_date"],
        "launch_date": normalized["launch_date"],
        "last_revision_date": normalized["last_revision_date"],
        "executed_by": normalized["executed_by"],
        "released_by": normalized["released_by"],
        "defect_description": normalized["defect_description"],
        "corrective_actions": normalized["corrective_actions"],
        "technical_opinion": normalized["technical_opinion"],
        "problem_tags": normalized["problem_tags"],
        "products": normalized["products"],
    }
