"""Cockpit público — Problema de Processo (P2; consumo visual na P3).

O operador só informa OP/operação/motivo/ferramenta/material/nota; identidade,
filial e posto vêm da bench session (X-Delpi-Bench-Session), o contexto da OP
da fila PUBLISHED e os materiais da SD4. Idempotency-Key é obrigatória e
atravessa ponta a ponta até o Requests API.
"""

from __future__ import annotations

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from production_control_app.composition.pc_composer import (
    build_public_process_issue_service,
)
from production_control_app.core.responses import fail, ok
from production_control_app.interface.http.routes.public_machine_load_routes import (  # noqa: E501
    _BENCH_SESSION_HEADER,
    _assert_cockpit_token,
    _handle_public_errors,
    _honeypot_ok,
)

router = APIRouter(prefix="/public/machine-load", tags=["Public process issues"])


class ReportProcessIssueBody(BaseModel):
    model_config = {"populate_by_name": True}

    production_order: str = Field(
        ..., alias="productionOrder", min_length=1, max_length=40
    )
    operation_code: str = Field(
        ..., alias="operationCode", min_length=1, max_length=20
    )
    issue_code: str = Field(..., alias="issueCode", min_length=1, max_length=60)
    # Declarados pelo operador — opcionais, NUNCA validados contra SD4/cadastro:
    # material_not_linked pode reportar justamente um material fora da operação.
    tool_code: str | None = Field(default=None, alias="toolCode", max_length=60)
    material_code: str | None = Field(
        default=None, alias="materialCode", max_length=60
    )
    note: str | None = Field(default=None, max_length=500)
    website: str | None = None  # honeypot


@router.post("/{token}/process-issues")
def report_process_issue(
    token: str,
    body: ReportProcessIssueBody,
    session_token: str | None = Header(default=None, alias=_BENCH_SESSION_HEADER),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    denied = _assert_cockpit_token(token)
    if denied is not None:
        return denied
    if not _honeypot_ok(body.website):
        return ok({"accepted": True, "requestId": None})
    if not str(idempotency_key or "").strip():
        return fail("Chave de idempotência ausente.", 422)
    try:
        data = build_public_process_issue_service().report(
            session_token=session_token,
            production_order=body.production_order,
            operation_code=body.operation_code,
            issue_code=body.issue_code,
            idempotency_key=str(idempotency_key).strip(),
            tool_code=body.tool_code,
            material_code=body.material_code,
            note=body.note,
        )
    except Exception as exc:  # noqa: BLE001
        return _handle_public_errors(exc)
    return ok(data, message="Solicitação enviada para Processos.", status_code=201)
