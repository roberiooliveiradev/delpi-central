"""Inspeções de processo de uma OP+operação no cockpit público.

Fonte: view ``historico_tela`` via api-delpi ``list_inspecoes_processo_operation_inspections``.
Sem linhas de ensaio — só sessões (quem, quando, resultado). Escopo: fila publicada.
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


class PublicOperationProcessInspectionsService:
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
            payload = self._gateway.fetch_process_inspections_for_operation(
                branch=code,
                production_order=order,
                operation=operation,
            )
        except DelpiGatewayError as exc:
            logger.warning("public_operation_process_inspections_unavailable: %s", exc)
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("public_operation_process_inspections_unavailable: %s", exc)
            raise DelpiGatewayError("Não foi possível carregar as inspeções.") from exc

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
            "summary": {"inspection_count": len(items)},
        }


def _public_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "inspector_name": _text(
            row.get("inspector_name") or row.get("nome_ensaiador")
        ),
        "measurement_date": _text(
            row.get("measurement_date") or row.get("data_medicao")
        )
        or None,
        "measurement_time": _text(
            row.get("measurement_time") or row.get("hora_medicao")
        )
        or None,
        "result": _text(row.get("result") or row.get("resultado")) or "REALIZADA",
        "result_code": _text(row.get("result_code") or row.get("resultado_codigo")),
    }


def _text(value: object) -> str:
    return str(value or "").strip()
