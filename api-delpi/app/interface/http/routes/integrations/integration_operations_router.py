"""HTTP routes — integration write-operation tracking (scoped reads).

Authorization model:
- S2S path: individual client-credentials token (supplies-api) with the
  read scope; the operation must have been recorded for that same client.
- User path: PROTHEUS_INTEGRATION_READ permission; the operation must have
  been recorded for that same authenticated actor.
- A caller can never read another consumer's or another user's operation
  just by knowing its UUID.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Path, Query, Request

from app.application.security.api_delpi_permissions import (
    PROTHEUS_INTEGRATION_READ_PERMISSIONS,
)
from app.composition.integration_tracking_composer import (
    build_integration_tracking_service,
)
from app.core.responses import error_response, not_found_response
from app.domain.integrations.integration_operation import (
    IntegrationTrackingError,
)
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.s2s_service_access import require_s2s_or_any_permission
from app.utils.logger import log_error

router = APIRouter(
    prefix="/integrations/operations",
    tags=["Integrations — Operation Tracking"],
)

_UUID_ERROR = (
    "Identificador de operação inválido.",
    "PROTHEUS_OPERATION_ID_INVALID",
)


def _caller_binding(request: Request) -> dict[str, str | None]:
    service_identity = getattr(request.state, "service_identity", None)
    caller_app = getattr(service_identity, "client_id", None)
    actor = getattr(request.state, "user", None)
    actor_id = getattr(actor, "id", None) or getattr(actor, "user_id", None)
    if actor_id is None:
        # Fallback: delpi_auth request context (same source as protheus_router).
        from delpi_auth.request_context import get_current_user

        user = get_current_user()
        actor_id = getattr(user, "id", None) or getattr(user, "user_id", None)
    return {
        "caller_app": str(caller_app) if caller_app else None,
        "actor_subject": str(actor_id).strip() if actor_id else None,
    }


def _validated_operation_id(operation_id: str) -> str:
    try:
        return str(uuid.UUID(str(operation_id).strip()))
    except (TypeError, ValueError) as exc:
        raise ProtheusRestError(
            _UUID_ERROR[0],
            code=_UUID_ERROR[1],
            status_code=422,
            recoverable=False,
        ) from exc


def _project_operation(op: dict) -> dict:
    """Public projection — internals (hashes, auth context) stay server-side."""
    return {
        "operation_id": op.get("operation_id"),
        "integration": op.get("integration"),
        "resource": op.get("resource"),
        "action": op.get("action"),
        "resource_key": op.get("resource_key"),
        "status": op.get("status"),
        "http_status": op.get("http_status"),
        "upstream_error_code": op.get("upstream_error_code"),
        "attempt_count": op.get("attempt_count"),
        "environment_key": op.get("environment_key"),
        "correlation_id": op.get("correlation_id"),
        "request_payload": op.get("request_payload"),
        "response_payload": op.get("response_payload"),
        "error_details": op.get("error_details"),
        "confirmation_evidence": op.get("confirmation_evidence"),
        "created_at": op.get("created_at"),
        "send_started_at": op.get("send_started_at"),
        "acknowledged_at": op.get("acknowledged_at"),
        "confirmed_at": op.get("confirmed_at"),
        "updated_at": op.get("updated_at"),
    }


def _load_scoped_operation(
    operation_id: str, request: Request
) -> dict | None:
    service = build_integration_tracking_service()
    op = service.get_operation(operation_id)
    if op is None:
        return None
    binding = _caller_binding(request)
    service.assert_can_view(
        op,
        caller_app=binding["caller_app"],
        actor_subject=binding["actor_subject"],
    )
    return op


@router.get(
    "/{operation_id}",
    operation_id="get_integration_operation",
)
@require_s2s_or_any_permission(
    PROTHEUS_INTEGRATION_READ_PERMISSIONS,
    required_scopes=("suppliers.read",),
    allowed_clients=("supplies-api",),
)
def get_integration_operation_route(
    request: Request,
    operation_id: str = Path(..., description="Tracked operation UUID"),
):
    try:
        oid = _validated_operation_id(operation_id)
        op = _load_scoped_operation(oid, request)
        if op is None:
            return not_found_response(
                "Operação de integração não encontrada.",
                code="PROTHEUS_OPERATION_NOT_FOUND",
            )
        return api_delpi_success(
            _project_operation(op),
            operation_id="get_integration_operation",
            message="Operação de integração consultada com sucesso.",
        )
    except IntegrationTrackingError as exc:
        status = 403 if exc.code == "INTEGRATION_OPERATION_FORBIDDEN" else 503
        return error_response(
            "Acesso à operação não autorizado."
            if status == 403
            else "Rastreio de integração indisponível.",
            status_code=status,
            code=exc.code,
            recoverable=False,
        )
    except ProtheusRestError as exc:
        return error_response(
            exc.message,
            status_code=exc.status_code,
            code=exc.code,
            recoverable=exc.recoverable,
        )
    except Exception as exc:
        log_error(f"Erro inesperado na consulta de operação: {type(exc).__name__}")
        return error_response(
            "Erro interno ao consultar operação de integração.",
            status_code=500,
            code="PROTHEUS_INTERNAL_ERROR",
            recoverable=True,
        )


@router.get(
    "/{operation_id}/events",
    operation_id="list_integration_operation_events",
)
@require_s2s_or_any_permission(
    PROTHEUS_INTEGRATION_READ_PERMISSIONS,
    required_scopes=("suppliers.read",),
    allowed_clients=("supplies-api",),
)
def list_integration_operation_events_route(
    request: Request,
    operation_id: str = Path(..., description="Tracked operation UUID"),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    try:
        oid = _validated_operation_id(operation_id)
        op = _load_scoped_operation(oid, request)
        if op is None:
            return not_found_response(
                "Operação de integração não encontrada.",
                code="PROTHEUS_OPERATION_NOT_FOUND",
            )
        service = build_integration_tracking_service()
        events = service.list_events(oid, limit=limit, offset=offset)
        return api_delpi_success(
            {"operation_id": oid, "events": events},
            operation_id="list_integration_operation_events",
            message="Eventos da operação consultados com sucesso.",
        )
    except IntegrationTrackingError as exc:
        status = 403 if exc.code == "INTEGRATION_OPERATION_FORBIDDEN" else 503
        return error_response(
            "Acesso à operação não autorizado."
            if status == 403
            else "Rastreio de integração indisponível.",
            status_code=status,
            code=exc.code,
            recoverable=False,
        )
    except ProtheusRestError as exc:
        return error_response(
            exc.message,
            status_code=exc.status_code,
            code=exc.code,
            recoverable=exc.recoverable,
        )
    except Exception as exc:
        log_error(
            f"Erro inesperado na consulta de eventos: {type(exc).__name__}"
        )
        return error_response(
            "Erro interno ao consultar eventos da operação.",
            status_code=500,
            code="PROTHEUS_INTERNAL_ERROR",
            recoverable=True,
        )
