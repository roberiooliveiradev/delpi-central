"""Auditoria de Consumo OP × operação (GLPI #1353) — detalhe read-only C2.

Serves the supplies-api BFF via the individual S2S credential
(``supplies-api`` client, escopo ``consumption-audit.read``) e o caminho de
usuário direto via permissão supplies. Token compartilhado legado nunca
autoriza esta superfície.

A resposta expõe fontes separadas (SC2/SG1/SD4/SD3/SH6/HZA/SH8) com
proveniência — diferenças aritméticas nunca viram acusação de irregularidade;
o que não é comprovável sai como ``unknown``/``null``/``partial``.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.application.dto.supplies.get_consumption_audit_order_request import (
    GetConsumptionAuditOrderRequest,
)
from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.composition.consumption_audit_composer import (
    build_get_consumption_audit_order_use_case,
)
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.s2s_service_access import require_s2s_or_any_permission
from app.utils.logger import log_error

router = APIRouter(
    prefix="/supplies/consumption-audit",
    tags=["Supplies — Consumption Audit"],
)

_SUPPLIES_BFF_CLIENTS = ("supplies-api",)
_CONSUMPTION_AUDIT_READ_SCOPE = ("consumption-audit.read",)


@router.get(
    "/orders/{production_order}",
    summary="Auditoria de consumo de uma OP (Suprimentos)",
    description=(
        "Detalhe read-only OP × operação × componente: ordem (SC2), estrutura "
        "histórica (SG1 na data de emissão), empenhos e consumo derivado "
        "(SD4), movimentos classificados/excluídos (SD3) e evidências de "
        "execução separadas (SH6/HZA/SH8). Filial obrigatória 01|02; chave da "
        "OP de 11 posições preservada."
    ),
    operation_id="get_consumption_audit_order",
)
@require_s2s_or_any_permission(
    KPI_SUPPLIES_ACCESS,
    required_scopes=_CONSUMPTION_AUDIT_READ_SCOPE,
    allowed_clients=_SUPPLIES_BFF_CLIENTS,
)
def get_consumption_audit_order(
    production_order: str,
    branch: str = Query(
        ..., description="Filial operacional obrigatória: 01 ou 02."
    ),
):
    """operationId: get_consumption_audit_order."""
    try:
        dto = GetConsumptionAuditOrderRequest(
            production_order=production_order,
            branch=branch,
        )
    except ValueError as exc:
        return error_response(
            str(exc),
            status_code=400,
            code="INVALID_REQUEST",
        )

    try:
        result = build_get_consumption_audit_order_use_case().execute(dto)
    except ValueError as exc:
        return error_response(
            str(exc),
            status_code=400,
            code="INVALID_PRODUCTION_ORDER",
        )
    except Exception as exc:
        log_error(f"Erro na auditoria de consumo da OP {production_order}: {exc}")
        return error_response(
            "Erro interno ao auditar consumo da ordem de produção.",
            status_code=500,
        )

    if result is None:
        return error_response(
            f"Ordem de produção {production_order} não encontrada na filial "
            f"{dto.branch}.",
            status_code=404,
            code="PRODUCTION_ORDER_NOT_FOUND",
            recoverable=False,
        )

    return api_delpi_success(
        result,
        operation_id="get_consumption_audit_order",
        message="Auditoria de consumo da OP gerada com sucesso.",
    )
