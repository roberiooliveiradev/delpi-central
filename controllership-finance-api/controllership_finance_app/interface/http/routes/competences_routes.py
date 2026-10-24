"""P2-READ — competências mensais e checklist esperado (snapshot).

Abertura idempotente: a mesma competência nunca é duplicada; retry/replay
retorna a existente (200). Somente versão PUBLISHED vigente gera snapshot;
sem fallback para DRAFT (`no_published_template`, 409). Itens do snapshot
iniciam em `EXPECTED` — nunca representados como entregues.
"""

from __future__ import annotations

from fastapi import APIRouter, Path, Query, Request
from pydantic import BaseModel, Field

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.interface.http.authz import authorized_user

router = APIRouter(prefix="/closing/competences", tags=["Closing Competences"])

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class OpenCompetenceRequest(BaseModel):
    period: str = Field(pattern=PERIOD_PATTERN)


def _repository() -> ClosingChecklistRepository:
    return ClosingChecklistRepository()


def _actor(user) -> str:
    return str(getattr(user, "id", None) or getattr(user, "email", ""))


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


@router.get("", operation_id="list_closing_competences")
def list_closing_competences(request: Request):
    authorized_user(request)
    try:
        competences = _repository().list_competences()
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_closing_competences")
    return ok(
        {"competences": competences},
        operation_id="list_closing_competences",
    )


@router.post("", operation_id="open_closing_competence")
def open_closing_competence(request: Request, body: OpenCompetenceRequest):
    user = authorized_user(request)
    try:
        competence, created = _repository().open_competence(
            body.period, actor=_actor(user)
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "open_closing_competence")
    return ok(
        competence,
        message=(
            "Competência aberta."
            if created
            else "Competência já existente."
        ),
        status_code=201 if created else 200,
        operation_id="open_closing_competence",
    )


@router.get(
    "/{period}",
    operation_id="get_closing_competence",
)
def get_closing_competence(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    authorized_user(request)
    try:
        competence = _repository().get_competence(period)
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_closing_competence")
    return ok(competence, operation_id="get_closing_competence")


@router.get(
    "/{period}/items",
    operation_id="list_closing_competence_items",
)
def list_closing_competence_items(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    sheet: str | None = Query(None, pattern="^(ELETRONICO|FISICO)$"),
    origin_kind: str | None = Query(None, pattern="^(TOTVS|EXTERNAL|MIXED)$"),
    recipient_area: str | None = Query(
        None, pattern="^(CONTABIL|FISCAL)$"
    ),
    branch_scope: str | None = Query(
        None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
    state: str | None = Query(None, pattern="^(EXPECTED)$"),
):
    authorized_user(request)
    try:
        items = _repository().list_competence_items(
            period,
            sheet=sheet,
            origin_kind=origin_kind,
            recipient_area=recipient_area,
            branch_scope=branch_scope,
            state=state,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_closing_competence_items")
    return ok(
        {"items": items},
        operation_id="list_closing_competence_items",
    )


@router.get(
    "/{period}/items/{item_key}",
    operation_id="get_closing_competence_item",
)
def get_closing_competence_item(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    item_key: str = Path(min_length=1, max_length=32),
):
    authorized_user(request)
    try:
        item = _repository().get_competence_item(period, item_key)
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_closing_competence_item")
    return ok(item, operation_id="get_closing_competence_item")
