"""Rotas autenticadas do Operator Feedback — inbox e tratativa do PCP (C4).

Separadas do cockpit público (/public/*): passam pelo JWT middleware e toda a
autorização (production-control.access + machine-load.view + filial) acontece
no PcpOperatorFeedbackService — a rota só traduz HTTP.
"""

from __future__ import annotations

from fastapi import APIRouter, Body, Query, Request
from pydantic import BaseModel, Field

from production_control_app.composition.pc_composer import (
    build_pcp_operator_feedback_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
    OperatorFeedbackConflict,
    OperatorFeedbackNotFound,
    OperatorFeedbackStateError,
)
from production_control_app.interface.http.auth_http import resolve_user

router = APIRouter(tags=["Operator feedback"])


class ResolveFeedbackBody(BaseModel):
    """resolutionNote é opcional nesta etapa — autoria nunca vem do body."""

    resolution_note: str | None = Field(
        default=None, max_length=500, alias="resolutionNote"
    )


def _handle_feedback_errors(exc: Exception):
    if isinstance(exc, InvalidBranch):
        return fail(str(exc), 422)
    if isinstance(exc, BranchAccessDenied):
        return fail(str(exc), 403)
    if isinstance(exc, PermissionError):
        return fail(str(exc), 403)
    if isinstance(exc, OperatorFeedbackNotFound):
        return fail(str(exc), 404)
    if isinstance(exc, (OperatorFeedbackStateError, OperatorFeedbackConflict)):
        return fail(str(exc), 409)
    if isinstance(exc, ValueError):
        return fail(str(exc), 422)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    raise exc


@router.get("/operator-feedbacks")
def list_operator_feedbacks(
    request: Request,
    branch: str = Query(..., description="Filial TOTVS (01 ou 02)"),
):
    """Inbox do PCP: impedimentos ativos (open|acknowledged) da filial.

    A listagem é por filial inteira — a identidade funcional é OP+operação,
    então feedback de OP transferida ou fora da fila atual continua visível.
    """
    user = resolve_user(request)
    try:
        data = build_pcp_operator_feedback_service().list_inbox(
            user, branch=branch
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle_feedback_errors(exc)


@router.post("/operator-feedbacks/{feedback_id}/acknowledge")
def acknowledge_operator_feedback(request: Request, feedback_id: str):
    """open -> acknowledged. Autoria vem do JWT; idempotente na C1."""
    user = resolve_user(request)
    try:
        data = build_pcp_operator_feedback_service().acknowledge(
            user, feedback_id=feedback_id
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle_feedback_errors(exc)


@router.post("/operator-feedbacks/{feedback_id}/resolve")
def resolve_operator_feedback(
    request: Request,
    feedback_id: str,
    body: ResolveFeedbackBody | None = Body(default=None),
):
    """open|acknowledged -> resolved, com observação opcional da tratativa."""
    user = resolve_user(request)
    try:
        data = build_pcp_operator_feedback_service().resolve(
            user,
            feedback_id=feedback_id,
            resolution_note=body.resolution_note if body else None,
        )
        return ok(data)
    except Exception as exc:  # noqa: BLE001
        return _handle_feedback_errors(exc)
