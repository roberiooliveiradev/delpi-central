"""Cockpit público — Operator Feedback (impedimentos do operador ao PCP).

O operador só informa OP/operação/tipo/motivo/nota; identidade, filial e posto
vêm da bench session (X-Delpi-Bench-Session) e o contexto da OP da fila
PUBLISHED. Mesmo token do cockpit e mesmo honeypot das outras escritas.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, Field

from production_control_app.composition.pc_composer import (
    build_public_operator_feedback_service,
)
from production_control_app.core.responses import ok
from production_control_app.interface.http.routes.public_machine_load_routes import (  # noqa: E501
    _BENCH_SESSION_HEADER,
    _assert_cockpit_token,
    _handle_public_errors,
    _honeypot_ok,
)

router = APIRouter(prefix="/public/machine-load", tags=["Public operator feedback"])


class ReportOperatorFeedbackBody(BaseModel):
    model_config = {"populate_by_name": True}

    production_order: str = Field(
        ..., alias="productionOrder", min_length=1, max_length=40
    )
    operation_code: str = Field(
        ..., alias="operationCode", min_length=1, max_length=20
    )
    feedback_type: str = Field(
        ..., alias="feedbackType", min_length=1, max_length=40
    )
    reason_code: str = Field(
        ..., alias="reasonCode", min_length=1, max_length=40
    )
    note: str | None = Field(default=None, max_length=500)
    website: str | None = None  # honeypot


@router.post("/{token}/operator-feedbacks")
def report_operator_feedback(
    token: str,
    body: ReportOperatorFeedbackBody,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    if not _honeypot_ok(body.website):
        return ok({"accepted": True, "id": None})
    try:
        data = build_public_operator_feedback_service().report(
            session_token=session_token,
            production_order=body.production_order,
            operation_code=body.operation_code,
            feedback_type=body.feedback_type,
            reason_code=body.reason_code,
            note=body.note,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)


@router.get("/{token}/operator-feedbacks/active")
def list_active_operator_feedbacks(
    token: str,
    production_order: str = Query(..., alias="productionOrder"),
    operation_code: str = Query(..., alias="operationCode"),
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    try:
        data = build_public_operator_feedback_service().list_active(
            session_token=session_token,
            production_order=production_order,
            operation_code=operation_code,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data)
