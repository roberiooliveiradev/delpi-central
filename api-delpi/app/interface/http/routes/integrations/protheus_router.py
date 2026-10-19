"""HTTP routes — Protheus REST integration (status + supplier read)."""

from __future__ import annotations

from fastapi import APIRouter, Path

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    PROTHEUS_INTEGRATION_READ_PERMISSIONS,
)
from app.composition.protheus_rest_composer import (
    build_get_protheus_integration_status_use_case,
    build_get_protheus_rest_supplier_use_case,
)
from app.core.responses import error_response, not_found_response
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/integrations/protheus",
    tags=["Integrations — Protheus REST"],
)


@router.get("/status", operation_id="get_protheus_integration_status")
@require_any_permission(PROTHEUS_INTEGRATION_READ_PERMISSIONS)
def get_protheus_integration_status_route():
    try:
        data = build_get_protheus_integration_status_use_case().execute()
        return api_delpi_success(
            data,
            operation_id="get_protheus_integration_status",
            message="Diagnóstico da integração Protheus concluído.",
        )
    except ProtheusRestError as exc:
        return error_response(
            exc.message,
            status_code=exc.status_code,
            code=exc.code,
            recoverable=exc.recoverable,
        )
    except Exception as exc:
        log_error(f"Erro inesperado no status Protheus: {type(exc).__name__}")
        return error_response(
            "Erro interno ao diagnosticar a integração Protheus.",
            status_code=500,
            code="PROTHEUS_INTERNAL_ERROR",
            recoverable=True,
        )


@router.get(
    "/suppliers/{supplier_id}",
    operation_id="get_protheus_rest_supplier",
)
@require_any_permission(PROTHEUS_INTEGRATION_READ_PERMISSIONS)
def get_protheus_rest_supplier_route(
    supplier_id: str = Path(
        ...,
        min_length=8,
        max_length=8,
        pattern=r"^[0-9]{8}$",
        description="Eight digits: six-digit supplier code + two-digit store",
    ),
):
    try:
        data = build_get_protheus_rest_supplier_use_case().execute(supplier_id)
        return api_delpi_success(
            data,
            operation_id="get_protheus_rest_supplier",
            message="Fornecedor consultado no Protheus com sucesso.",
        )
    except ProtheusRestError as exc:
        if exc.code == "PROTHEUS_SUPPLIER_NOT_FOUND":
            return not_found_response(
                exc.message,
                code=exc.code,
            )
        return error_response(
            exc.message,
            status_code=exc.status_code,
            code=exc.code,
            recoverable=exc.recoverable,
        )
    except Exception as exc:
        log_error(f"Erro inesperado na consulta Protheus: {type(exc).__name__}")
        return error_response(
            "Erro interno ao consultar fornecedor no Protheus.",
            status_code=500,
            code="PROTHEUS_INTERNAL_ERROR",
            recoverable=True,
        )
