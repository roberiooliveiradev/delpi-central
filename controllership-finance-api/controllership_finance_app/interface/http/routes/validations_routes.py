"""P2 — validação humana de evidências, N/A, item excepcional e correção.

V1 (doc 09 §Validação): `validator` é capability — `access` + `manage`
efetivos. Decisões são append-only (`evidence_decision`); substituição
cria nova exigência de validação porque a decisão é por versão/composição
corrente. Upload nunca é validação (`ATTACHED != VALIDATED`).

Resource scope: mesmo modelo dos documentos — `branch_scope` declara o
filial-contexto do request; item fora do contexto é 404.
"""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Path, Query, Request
from pydantic import BaseModel, Field

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    Forbidden,
    InvalidRejectionReason,
    InvalidUpload,
    MissingJustification,
)
from controllership_finance_app.domain.closing_documents.resource_scope import (
    normalize_request_scope,
)
from controllership_finance_app.infrastructure.persistence.closing_validation_repository import (
    ClosingValidationRepository,
)
from controllership_finance_app.interface.http.authz import (
    MANAGE_PERMISSION,
    actor_subject,
    authorized_user,
)
from delpi_auth.authz_core import has_permission

router = APIRouter(
    prefix="/closing/competences", tags=["Closing Validation"]
)

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"

REJECTION_REASONS = frozenset(
    {
        "WRONG_COMPETENCE",
        "INCOMPLETE",
        "ILLEGIBLE",
        "DIVERGENT",
        "WRONG_DOCUMENT",
        "OTHER",
    }
)


def _repository() -> ClosingValidationRepository:
    return ClosingValidationRepository()


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


def _require_manage(request: Request):
    """Validador V1 = `access` + `manage` efetivos (RQ-P2-03)."""
    user = authorized_user(request)
    if not has_permission(user, MANAGE_PERMISSION):
        raise Forbidden(
            "Somente validador elegível (manage) decide evidências."
        )
    return actor_subject(user)


def _validate_decision_payload(
    decision: str, reason_code: str | None, comment: str | None
) -> None:
    if decision == "REJECTED":
        if not reason_code or reason_code not in REJECTION_REASONS:
            raise InvalidRejectionReason(
                "Rejeição exige motivo estruturado do catálogo."
            )
        if reason_code == "OTHER" and not (comment or "").strip():
            raise MissingJustification(
                "Motivo 'Outro' exige comentário."
            )
    elif reason_code:
        raise InvalidRejectionReason(
            "Motivo só é permitido em rejeição."
        )


def _require_justification(justification: str | None) -> str:
    text = (justification or "").strip()
    if not text:
        raise MissingJustification("Justificativa é obrigatória.")
    return text


class EvidenceDecisionRequest(BaseModel):
    decision: Literal["ACCEPTED", "REJECTED"]
    reason_code: str | None = Field(default=None, max_length=40)
    comment: str | None = Field(default=None, max_length=2000)


class JustificationRequest(BaseModel):
    justification: str = Field(min_length=1, max_length=2000)


class ReverseDecisionRequest(BaseModel):
    result_state: Literal["UNDER_REVIEW", "ACCEPTED"]
    justification: str = Field(min_length=1, max_length=2000)


class ExceptionalItemRequest(BaseModel):
    sheet: Literal["ELETRONICO", "FISICO"]
    name: str = Field(min_length=1, max_length=255)
    justification: str = Field(min_length=1, max_length=2000)
    purpose: str | None = None
    origin_kind: Literal["TOTVS", "EXTERNAL", "MIXED"] = "EXTERNAL"
    recipient_area: Literal["CONTABIL", "FISCAL"] | None = None
    applicability: Literal["REQUIRED", "CONDITIONAL", "OPTIONAL"] = (
        "REQUIRED"
    )
    branch_scope: Literal["MATRIX", "BRANCH", "BOTH"] = "BOTH"
    validation_scope: Literal["PER_ATTACHMENT", "WHOLE_SET"] = (
        "PER_ATTACHMENT"
    )


class CorrectionRequestBody(BaseModel):
    changes: dict[str, str | None] = Field(min_length=1)
    justification: str = Field(min_length=1, max_length=2000)


class CorrectionReviewBody(BaseModel):
    approve: bool
    review_reason: str | None = Field(default=None, max_length=2000)


def _decision_view(row: dict) -> dict:
    out = {}
    for key, value in row.items():
        if isinstance(value, uuid.UUID):
            out[key] = str(value)
        elif hasattr(value, "isoformat"):
            out[key] = value.isoformat()
        else:
            out[key] = value
    return out


@router.post(
    "/{period}/documents/{document_id}/validation",
    operation_id="decide_document_evidence",
    status_code=201,
)
def decide_document_evidence(
    request: Request,
    body: EvidenceDecisionRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    document_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """RQ-P2-03/06 — decisão PER_ATTACHMENT sobre a versão corrente."""
    try:
        actor = _require_manage(request)
        _validate_decision_payload(
            body.decision, body.reason_code, body.comment
        )
        result = _repository().decide_version(
            period=period,
            document_id=str(document_id),
            actor=actor,
            decision=body.decision,
            reason_code=body.reason_code,
            comment=body.comment,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "decide_document_evidence")
    return ok(
        _decision_view(result),
        message=(
            "Evidência aceita."
            if body.decision == "ACCEPTED"
            else "Evidência rejeitada."
        ),
        status_code=201,
        operation_id="decide_document_evidence",
    )


@router.post(
    "/{period}/items/{item_key}/validation",
    operation_id="decide_item_evidence_set",
    status_code=201,
)
def decide_item_evidence_set(
    request: Request,
    body: EvidenceDecisionRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    item_key: str = Path(min_length=1, max_length=32),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """RQ-P2-06 — decisão WHOLE_SET sobre a composição corrente do item."""
    try:
        actor = _require_manage(request)
        _validate_decision_payload(
            body.decision, body.reason_code, body.comment
        )
        result = _repository().decide_item_set(
            period=period,
            item_key=item_key,
            actor=actor,
            decision=body.decision,
            reason_code=body.reason_code,
            comment=body.comment,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "decide_item_evidence_set")
    return ok(
        _decision_view(result),
        message=(
            "Conjunto de evidências aceito."
            if body.decision == "ACCEPTED"
            else "Conjunto de evidências rejeitado."
        ),
        status_code=201,
        operation_id="decide_item_evidence_set",
    )


@router.post(
    "/{period}/decisions/{decision_id}/reverse",
    operation_id="reverse_rejection",
    status_code=201,
)
def reverse_rejection(
    request: Request,
    body: ReverseDecisionRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    decision_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """RQ-P2-10 — reversão pelo mesmo validador; bloqueada se já existe
    versão/composição posterior à rejeitada."""
    try:
        actor = _require_manage(request)
        result = _repository().reverse_decision(
            period=period,
            decision_id=str(decision_id),
            actor=actor,
            result_state=body.result_state,
            justification=_require_justification(body.justification),
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "reverse_rejection")
    return ok(
        _decision_view(result),
        message="Rejeição revertida.",
        status_code=201,
        operation_id="reverse_rejection",
    )


@router.post(
    "/{period}/items/{item_key}/not-applicable",
    operation_id="mark_item_not_applicable",
)
def mark_item_not_applicable(
    request: Request,
    body: JustificationRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    item_key: str = Path(min_length=1, max_length=32),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """RQ-P2-02 — N/A somente em CONDITIONAL, com justificativa auditada."""
    actor = actor_subject(authorized_user(request))
    try:
        item = _repository().mark_not_applicable(
            period,
            item_key,
            actor,
            _require_justification(body.justification),
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "mark_item_not_applicable")
    return ok(
        _decision_view(item),
        message="Item marcado como não aplicável.",
        operation_id="mark_item_not_applicable",
    )


@router.post(
    "/{period}/items/{item_key}/not-applicable/revert",
    operation_id="revert_item_not_applicable",
)
def revert_item_not_applicable(
    request: Request,
    body: JustificationRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    item_key: str = Path(min_length=1, max_length=32),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """N/A → EXPECTED antes da submissão de pacote (P5 ainda não existe)."""
    actor = actor_subject(authorized_user(request))
    try:
        item = _repository().revert_not_applicable(
            period,
            item_key,
            actor,
            _require_justification(body.justification),
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "revert_item_not_applicable")
    return ok(
        _decision_view(item),
        message="Item voltou para pendente.",
        operation_id="revert_item_not_applicable",
    )


@router.post(
    "/{period}/items/{item_key}/cancel",
    operation_id="cancel_checklist_item",
)
def cancel_checklist_item(
    request: Request,
    body: JustificationRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    item_key: str = Path(min_length=1, max_length=32),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """RQ-P2-08 — cancelamento pré-execução: `CANCELLED != DELETED` e
    bloqueado após evento material (evidência anexada)."""
    actor = actor_subject(authorized_user(request))
    try:
        item = _repository().cancel_item(
            period,
            item_key,
            actor,
            _require_justification(body.justification),
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "cancel_checklist_item")
    return ok(
        _decision_view(item),
        message="Item cancelado. O histórico foi preservado.",
        operation_id="cancel_checklist_item",
    )


@router.post(
    "/{period}/items",
    operation_id="create_exceptional_item",
    status_code=201,
)
def create_exceptional_item(
    request: Request,
    body: ExceptionalItemRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """RQ-P2-07 — item excepcional existe só na competência; opções só
    dos catálogos vigentes; template mestre intocado."""
    actor = actor_subject(authorized_user(request))
    try:
        item = _repository().create_exceptional_item(
            period,
            actor,
            sheet=body.sheet,
            name=body.name,
            justification=_require_justification(body.justification),
            purpose=body.purpose,
            origin_kind=body.origin_kind,
            recipient_area=body.recipient_area,
            applicability=body.applicability,
            branch_scope=body.branch_scope,
            validation_scope=body.validation_scope,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "create_exceptional_item")
    return ok(
        _decision_view(item),
        message="Item excepcional adicionado à competência.",
        status_code=201,
        operation_id="create_exceptional_item",
    )


@router.post(
    "/{period}/items/{item_key}/corrections",
    operation_id="request_item_correction",
    status_code=201,
)
def request_item_correction(
    request: Request,
    body: CorrectionRequestBody,
    period: str = Path(pattern=PERIOD_PATTERN),
    item_key: str = Path(min_length=1, max_length=32),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """RQ-P2-09 — ACCESS REQUEST: correção estrutural pós-execução."""
    actor = actor_subject(authorized_user(request))
    try:
        correction = _repository().request_correction(
            period,
            item_key,
            actor,
            changes=dict(body.changes),
            justification=_require_justification(body.justification),
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "request_item_correction")
    return ok(
        _decision_view(correction),
        message="Correção estrutural solicitada.",
        status_code=201,
        operation_id="request_item_correction",
    )


@router.post(
    "/{period}/items/{item_key}/corrections/{correction_id}/review",
    operation_id="review_item_correction",
)
def review_item_correction(
    request: Request,
    body: CorrectionReviewBody,
    period: str = Path(pattern=PERIOD_PATTERN),
    item_key: str = Path(min_length=1, max_length=32),
    correction_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """RQ-P2-09 — MANAGE REVIEW: aprovação cria nova `revision` do item;
    request e revisão permanecem eventos separados auditados."""
    try:
        actor = _require_manage(request)
        if not body.approve and not (body.review_reason or "").strip():
            raise MissingJustification(
                "Rejeição da correção exige motivo."
            )
        correction = _repository().review_correction(
            period,
            str(correction_id),
            actor,
            approve=body.approve,
            review_reason=body.review_reason,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "review_item_correction")
    return ok(
        _decision_view(correction),
        message=(
            "Correção aprovada — item revisado."
            if body.approve
            else "Correção rejeitada."
        ),
        operation_id="review_item_correction",
    )


@router.get(
    "/{period}/items/{item_key}/corrections",
    operation_id="list_item_corrections",
)
def list_item_corrections(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    item_key: str = Path(min_length=1, max_length=32),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    authorized_user(request)
    try:
        corrections = _repository().list_corrections(
            period,
            item_key,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_item_corrections")
    return ok(
        {"corrections": [_decision_view(c) for c in corrections]},
        operation_id="list_item_corrections",
    )


@router.get(
    "/{period}/items/{item_key}/validation",
    operation_id="get_item_validation",
)
def get_item_validation(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    item_key: str = Path(min_length=1, max_length=32),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """Estado de validação do item: decisão corrente por documento +
    histórico append-only de decisões."""
    authorized_user(request)
    try:
        data = _repository().list_item_decisions(
            period,
            item_key,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_item_validation")
    return ok(
        _decision_view(data), operation_id="get_item_validation"
    )
