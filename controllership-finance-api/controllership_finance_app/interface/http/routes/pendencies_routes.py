"""P4 — fila de pendências e classificações (doc 11/104).

Autorização: leitura e criação exigem `access` efetivo; confirmação de
classificação e reassign exigem `manage` (decisão governada). Claim e
transições de estado exigem `access` — o backend revalida estado/escopo
em cada mutação; a lista de ações visíveis nunca é authority.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Path, Query, Request
from pydantic import BaseModel, Field

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    Forbidden,
)
from controllership_finance_app.domain.closing_documents.resource_scope import (
    normalize_request_scope,
)
from controllership_finance_app.infrastructure.persistence.closing_pendency_repository import (
    ClosingPendencyRepository,
)
from controllership_finance_app.interface.http.authz import (
    MANAGE_PERMISSION,
    actor_subject,
    authorized_user,
)
from delpi_auth.authz_core import has_permission

router = APIRouter(
    prefix="/closing/competences", tags=["Closing Pendencies"]
)

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class CreatePendencyRequest(BaseModel):
    kind: str
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    snapshot_item_id: uuid.UUID | None = None
    queue: str | None = None
    responsible_subject: str | None = None
    branch_scope: str | None = Field(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    )
    suggested_classification: str | None = None
    suggestion_rationale: str | None = None
    suggestion_source: str | None = Field(
        default=None, pattern="^(DETERMINISTIC|AI|MANUAL)$"
    )


class RevisionRequest(BaseModel):
    revision: int = Field(ge=1)


class ReassignRequest(RevisionRequest):
    new_responsible: str = Field(min_length=1)


class TransitionRequest(RevisionRequest):
    to_state: str
    justification: str | None = None
    notes: str | None = None


class ConfirmClassificationRequest(RevisionRequest):
    classification: str = Field(min_length=1)
    reason: str | None = None


def _repository() -> ClosingPendencyRepository:
    return ClosingPendencyRepository()


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


def _require_manage(request: Request) -> str:
    """Decisões governadas de P4 exigem `access` + `manage` efetivos."""
    user = authorized_user(request)
    if not has_permission(user, MANAGE_PERMISSION):
        raise Forbidden(
            "Somente ator elegível (manage) executa esta decisão."
        )
    return actor_subject(user)


@router.get(
    "/{period}/pendencies",
    operation_id="list_closing_pendencies",
)
def list_closing_pendencies(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    state: str | None = Query(default=None),
    kind: str | None = Query(default=None),
    responsible: str | None = Query(default=None),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    authorized_user(request)
    try:
        result = _repository().list_pendencies(
            period,
            state=state,
            kind=kind,
            responsible=responsible,
            request_scope=normalize_request_scope(branch_scope),
            limit=limit,
            offset=offset,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_closing_pendencies")
    return ok(result, operation_id="list_closing_pendencies")


@router.get(
    "/{period}/pendencies/{pendency_id}",
    operation_id="get_closing_pendency",
)
def get_closing_pendency(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    pendency_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    authorized_user(request)
    try:
        pendency = _repository().get_pendency(
            period,
            str(pendency_id),
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_closing_pendency")
    return ok(
        {"pendency": pendency}, operation_id="get_closing_pendency"
    )


@router.get(
    "/{period}/pendencies/{pendency_id}/history",
    operation_id="list_pendency_history",
)
def list_pendency_history(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    pendency_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    authorized_user(request)
    try:
        result = _repository().list_pendency_history(
            period,
            str(pendency_id),
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_pendency_history")
    return ok(result, operation_id="list_pendency_history")


@router.post(
    "/{period}/pendencies",
    operation_id="create_closing_pendency",
    status_code=201,
)
def create_closing_pendency(
    request: Request,
    body: CreatePendencyRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    try:
        actor = actor_subject(authorized_user(request))
        pendency = _repository().create_pendency(
            period,
            actor=actor,
            kind=body.kind,
            title=body.title,
            description=body.description,
            snapshot_item_id=(
                str(body.snapshot_item_id)
                if body.snapshot_item_id
                else None
            ),
            queue=body.queue,
            responsible_subject=body.responsible_subject,
            branch_scope=body.branch_scope,
            suggested_classification=body.suggested_classification,
            suggestion_rationale=body.suggestion_rationale,
            suggestion_source=body.suggestion_source,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "create_closing_pendency")
    return ok(
        {"pendency": pendency},
        status_code=201,
        operation_id="create_closing_pendency",
    )


@router.post(
    "/{period}/pendencies/{pendency_id}/claim",
    operation_id="claim_pendency",
)
def claim_pendency(
    request: Request,
    body: RevisionRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    pendency_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    try:
        actor = actor_subject(authorized_user(request))
        pendency = _repository().claim_pendency(
            period,
            str(pendency_id),
            actor,
            expected_revision=body.revision,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "claim_pendency")
    return ok(
        {"pendency": pendency}, operation_id="claim_pendency"
    )


@router.post(
    "/{period}/pendencies/{pendency_id}/reassign",
    operation_id="reassign_pendency",
)
def reassign_pendency(
    request: Request,
    body: ReassignRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    pendency_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    try:
        actor = _require_manage(request)
        pendency = _repository().reassign_pendency(
            period,
            str(pendency_id),
            actor,
            new_responsible=body.new_responsible,
            expected_revision=body.revision,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "reassign_pendency")
    return ok(
        {"pendency": pendency}, operation_id="reassign_pendency"
    )


@router.post(
    "/{period}/pendencies/{pendency_id}/transition",
    operation_id="transition_pendency",
)
def transition_pendency(
    request: Request,
    body: TransitionRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    pendency_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    try:
        actor = actor_subject(authorized_user(request))
        pendency = _repository().transition_pendency(
            period,
            str(pendency_id),
            actor,
            to_state=body.to_state,
            expected_revision=body.revision,
            justification=body.justification,
            notes=body.notes,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "transition_pendency")
    return ok(
        {"pendency": pendency}, operation_id="transition_pendency"
    )


@router.post(
    "/{period}/pendencies/{pendency_id}/classification",
    operation_id="confirm_pendency_classification",
)
def confirm_pendency_classification(
    request: Request,
    body: ConfirmClassificationRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    pendency_id: uuid.UUID = Path(),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """RQ-P4-02 — confirmação humana de classificação (sugestão não decide)."""
    try:
        actor = _require_manage(request)
        pendency = _repository().confirm_classification(
            period,
            str(pendency_id),
            actor,
            classification=body.classification,
            reason=body.reason,
            expected_revision=body.revision,
            request_scope=normalize_request_scope(branch_scope),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(
            exc, "confirm_pendency_classification"
        )
    return ok(
        {"pendency": pendency},
        operation_id="confirm_pendency_classification",
    )
