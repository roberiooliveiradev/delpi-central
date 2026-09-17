"""Materiais SD4 de uma OP+operação no cockpit público.

Fonte: ``SD4010`` via api-delpi ``list_production_order_operation_materials``.
Sem fallback SG1. O link anônimo só vê OP/operação da fila publicada.
"""

from __future__ import annotations

import logging
from typing import Any

from production_control_app.application.services.machine_load_service import MachineLoadService
from production_control_app.application.services.public_cockpit_access_service import (
    PublicCockpitAccessService,
)
from production_control_app.domain.errors import DelpiGatewayError, PublicAccessDenied
from production_control_app.domain.services.branch_access_service import BranchAccessService

logger = logging.getLogger(__name__)


class PublicOperationMaterialsService:
    def __init__(
        self,
        gateway: Any,
        *,
        access: PublicCockpitAccessService,
        machine_load: MachineLoadService,
        branch_access: BranchAccessService,
    ) -> None:
        self._gateway = gateway
        self._access = access
        self._machine_load = machine_load
        self._branch_access = branch_access

    def list_for_operation(
        self,
        *,
        token: str,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any]:
        if not self._access.is_valid_token(token):
            raise PublicAccessDenied(
                self._access.message("invalidToken", "Link do cockpit inválido ou desativado.")
            )
        code = self._branch_access.assert_valid_branch(branch)
        order = str(production_order or "").strip()
        operation = str(operation_code or "").strip()
        if not order or not operation:
            raise ValueError("Informe a ordem de produção e o código da operação.")

        if not self._machine_load.public_snapshot_contains_operation(
            branch=code,
            production_order=order,
            operation_code=operation,
        ):
            raise ValueError(
                "Esta operação não está na fila publicada desta filial."
            )

        try:
            payload = self._gateway.fetch_production_order_operation_materials(
                branch=code,
                production_order=order,
                operation=operation,
            )
        except DelpiGatewayError as exc:
            logger.warning("public_operation_materials_unavailable: %s", exc)
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("public_operation_materials_unavailable: %s", exc)
            raise DelpiGatewayError("Não foi possível carregar os materiais.") from exc

        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            data = payload if isinstance(payload, dict) else {}
        raw_items = data.get("items") if isinstance(data.get("items"), list) else []
        items = [_public_item(row) for row in raw_items if isinstance(row, dict)]
        return {
            "branch": code,
            "production_order": order,
            "operation_code": operation,
            "items": items,
            "summary": {
                "material_count": len(items),
                "commitment_count": sum(item["commitment_count"] for item in items),
            },
        }


def _public_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_code": _text(row.get("product_code")),
        "description": _text(row.get("description")),
        "unit": _text(row.get("unit")),
        "original_qty": _float(row.get("original_qty")),
        "open_qty": _float(row.get("open_qty")),
        "consumed_qty": _float(row.get("consumed_qty")),
        "commitment_count": int(row.get("commitment_count") or 0),
    }


def _text(value: object) -> str:
    return str(value or "").strip()


def _float(value: object) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0
