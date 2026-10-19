"""HTTP routes — Protheus REST integration (status, supplier read, gated create)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Body, Path

from delpi_auth.authorization import require_any_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import (
    PROTHEUS_INTEGRATION_READ_PERMISSIONS,
    PROTHEUS_SUPPLIER_CREATE_PERMISSIONS,
)
from app.composition.protheus_rest_composer import (
    build_create_protheus_rest_supplier_use_case,
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


def _actor_user_id() -> UUID:
    user = get_current_user()
    if user is None:
        raise ProtheusRestError(
            "Usuário não autenticado.",
            code="PROTHEUS_UNAUTHORIZED",
            status_code=401,
            recoverable=False,
        )
    raw = getattr(user, "id", None) or getattr(user, "user_id", None)
    try:
        return UUID(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ProtheusRestError(
            "Identificador de usuário autenticado inválido.",
            code="PROTHEUS_UNAUTHORIZED",
            status_code=401,
            recoverable=False,
        ) from exc


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


@router.post(
    "/suppliers",
    operation_id="create_protheus_rest_supplier",
)
@require_any_permission(PROTHEUS_SUPPLIER_CREATE_PERMISSIONS)
def create_protheus_rest_supplier_route(
    body: dict[str, Any] = Body(...),
):
    """Create supplier via Protheus REST. Identity (codusr) resolved from Core only."""
    if not isinstance(body, dict):
        return error_response(
            "Corpo da requisição deve ser um objeto JSON.",
            status_code=422,
            code="PROTHEUS_SUPPLIER_PAYLOAD_INVALID",
            recoverable=False,
        )

    # Reject client-supplied identity at the edge (also rejected in payload normalizer).
    for forbidden in ("codusr", "user_id", "usr_id", "protheus_user_id"):
        if forbidden in body:
            return error_response(
                "Identidade Protheus não pode ser enviada pelo cliente.",
                status_code=422,
                code="PROTHEUS_IDENTITY_CLIENT_FORBIDDEN",
                recoverable=False,
            )

    fornecedor = body.get("fornecedor", body)
    try:
        actor_id = _actor_user_id()
        data = build_create_protheus_rest_supplier_use_case().execute(
            actor_user_id=actor_id,
            fornecedor=fornecedor if isinstance(fornecedor, dict) else {},
        )
        return api_delpi_success(
            data,
            operation_id="create_protheus_rest_supplier",
            message=(
                "Solicitação de inclusão de fornecedor processada."
                if data.get("creation_confirmed")
                else "Solicitação enviada ao Protheus; confirmação de código ainda não homologada."
            ),
        )
    except ProtheusRestError as exc:
        return error_response(
            exc.message,
            status_code=exc.status_code,
            code=exc.code,
            recoverable=exc.recoverable,
        )
    except Exception as exc:
        log_error(f"Erro inesperado na criação Protheus: {type(exc).__name__}")
        return error_response(
            "Erro interno ao criar fornecedor no Protheus.",
            status_code=500,
            code="PROTHEUS_INTERNAL_ERROR",
            recoverable=True,
        )
