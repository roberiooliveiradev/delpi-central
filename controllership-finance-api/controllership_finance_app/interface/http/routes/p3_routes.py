"""P3 — cutoff, conciliação e revalidação (docs 10/15.1/104).

Leitura de readiness exige `access`; cutoff, revalidação e registro de
resultados de sources são decisões governadas → `manage` efetivo.
`STOCK_CLOSED` reflete somente a tabela `closing_stock_state`
sincronizada pelo owner — nenhuma rota escreve esse estado (RQ-P3-08).
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Path, Request
from pydantic import BaseModel, Field

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    Forbidden,
)
from controllership_finance_app.infrastructure.persistence.closing_p3_repository import (
    RECONCILIATION_DOMAINS,
    ClosingP3Repository,
)
from controllership_finance_app.interface.http.authz import (
    MANAGE_PERMISSION,
    actor_subject,
    authorized_user,
)
from delpi_auth.authz_core import has_permission

router = APIRouter(
    prefix="/closing/competences", tags=["Closing P3 Cutoff"]
)

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class CutoffRequest(BaseModel):
    notes: str | None = None


class RevalidationRequest(BaseModel):
    notes: str | None = None


class ReconciliationRequest(BaseModel):
    source_state: str
    expected_amount: Decimal | None = None
    reported_amount: Decimal | None = None
    rule_version: str | None = None
    provenance: dict | None = None
    revision: int | None = Field(default=None, ge=1)


def _repository() -> ClosingP3Repository:
    return ClosingP3Repository()


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


def _require_manage(request: Request) -> str:
    user = authorized_user(request)
    if not has_permission(user, MANAGE_PERMISSION):
        raise Forbidden(
            "Somente ator elegível (manage) governa cutoff/conciliação."
        )
    return actor_subject(user)


@router.get(
    "/{period}/p3",
    operation_id="get_p3_state",
)
def get_p3_state(
    request: Request, period: str = Path(pattern=PERIOD_PATTERN)
):
    authorized_user(request)
    try:
        state = _repository().get_p3_state(period)
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_p3_state")
    return ok(state, operation_id="get_p3_state")


@router.get(
    "/{period}/p3/events",
    operation_id="list_p3_events",
)
def list_p3_events(
    request: Request, period: str = Path(pattern=PERIOD_PATTERN)
):
    authorized_user(request)
    try:
        events = _repository().list_p3_events(period)
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_p3_events")
    return ok(events, operation_id="list_p3_events")


@router.post(
    "/{period}/p3/cutoff",
    operation_id="confirm_p3_cutoff",
    status_code=201,
)
def confirm_p3_cutoff(
    request: Request,
    body: CutoffRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    """RQ-P3-01 — confirmação humana governada, única por competência."""
    try:
        actor = _require_manage(request)
        cutoff = _repository().confirm_cutoff(
            period, actor=actor, notes=body.notes
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "confirm_p3_cutoff")
    return ok(
        {"cutoff": cutoff},
        status_code=201,
        operation_id="confirm_p3_cutoff",
    )


@router.put(
    "/{period}/p3/reconciliations/{domain}",
    operation_id="upsert_p3_reconciliation",
)
def upsert_p3_reconciliation(
    request: Request,
    body: ReconciliationRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    domain: str = Path(pattern="^(ENTRADAS_SAIDAS|P7|H02)$"),
):
    """Registra resultado de uma source (disponível, parcial,
    indisponível, stale, erro) com proveniência explícita. Indisponível
    nunca vira zero — readiness é derivada por domínio."""
    try:
        actor = _require_manage(request)
        row = _repository().upsert_reconciliation(
            period,
            domain,
            actor=actor,
            source_state=body.source_state,
            expected_amount=body.expected_amount,
            reported_amount=body.reported_amount,
            rule_version=body.rule_version,
            provenance=body.provenance,
            expected_revision=body.revision,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "upsert_p3_reconciliation")
    return ok(
        {"reconciliation": row},
        operation_id="upsert_p3_reconciliation",
    )


@router.post(
    "/{period}/p3/revalidations",
    operation_id="revalidate_p3",
    status_code=201,
)
def revalidate_p3(
    request: Request,
    body: RevalidationRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    """RQ-P3-02 — revalidação pós-cutoff; resultado `STALE_INPUT` quando
    faltar source, `VALID` somente com todas AVAILABLE."""
    try:
        actor = _require_manage(request)
        row = _repository().revalidate(
            period, actor=actor, notes=body.notes
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "revalidate_p3")
    return ok(
        {"revalidation": row},
        status_code=201,
        operation_id="revalidate_p3",
    )
