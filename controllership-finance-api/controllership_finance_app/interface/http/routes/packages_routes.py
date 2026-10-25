"""P5 — recipient packages, submissão in-portal, review e conclusão
mensal (docs 12/37/104; contrato C2/P5-A..J/DEC-01..04).

Autorização (backend-first, fail-closed):
- leitura exige `access`; manage vê todos os pacotes, demais somente
  pacotes com assignment ativo (sibling nunca vaza — 404);
- finalize/reopen/complement/submit/assignments/clarification-resolve
  exigem `manage` (decisões governadas);
- review/decision/clarification exigem `access` + assignment ativo —
  `manage` isolado não vota por área sem assignment (P5-C);
- rejeição terminal exige `access` + COORDINATOR ativo (DEC-01);
- nenhum endpoint cria/revoga permission nem transporta pacote por
  e-mail; notification é outbox de emissão, nunca estado de negócio.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Path, Request
from pydantic import BaseModel, Field

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
    Forbidden,
)
from controllership_finance_app.infrastructure.persistence.closing_package_repository import (
    ClosingPackageRepository,
)
from controllership_finance_app.interface.http.authz import (
    MANAGE_PERMISSION,
    actor_subject,
    authorized_user,
)
from delpi_auth.authz_core import has_permission

router = APIRouter(
    prefix="/closing/competences", tags=["Closing Packages"]
)

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class FinalizeRequest(BaseModel):
    recipient_area: str = Field(min_length=1, max_length=16)
    notes: str | None = None


class ReasonRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class SubmitRequest(BaseModel):
    revision: int = Field(ge=1)


class AssignRequest(BaseModel):
    role: str
    subject: str = Field(min_length=1)
    recipient_area: str | None = None
    area: str | None = None


class DeactivateRequest(BaseModel):
    reason: str | None = None


class DecisionRequest(BaseModel):
    area: str = Field(min_length=1, max_length=32)
    outcome: str
    note: str | None = None


class ClarificationRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    area: str | None = None


class ResolveRequest(BaseModel):
    response: str = Field(min_length=1, max_length=4000)


def _repository() -> ClosingPackageRepository:
    return ClosingPackageRepository()


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


def _viewer(request: Request) -> tuple[str, bool]:
    user = authorized_user(request)
    return (
        actor_subject(user),
        has_permission(user, MANAGE_PERMISSION),
    )


def _manage_actor(request: Request) -> str:
    user = authorized_user(request)
    if not has_permission(user, MANAGE_PERMISSION):
        raise Forbidden(
            "Somente ator elegível (manage) executa esta decisão."
        )
    return actor_subject(user)


@router.get(
    "/{period}/packages",
    operation_id="list_closing_packages",
)
def list_closing_packages(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    try:
        viewer, is_manage = _viewer(request)
        result = _repository().list_packages(
            period, viewer=viewer, is_manage=is_manage
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_closing_packages")
    return ok(result, operation_id="list_closing_packages")


@router.get(
    "/{period}/packages/{package_id}",
    operation_id="get_closing_package",
)
def get_closing_package(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    package_id: uuid.UUID = Path(),
):
    try:
        viewer, is_manage = _viewer(request)
        result = _repository().get_package(
            period,
            str(package_id),
            viewer=viewer,
            is_manage=is_manage,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_closing_package")
    return ok(result, operation_id="get_closing_package")


@router.post(
    "/{period}/packages/finalize",
    operation_id="finalize_closing_package",
)
def finalize_closing_package(
    request: Request,
    body: FinalizeRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    try:
        actor = _manage_actor(request)
        result = _repository().finalize_package(
            period, body.recipient_area, actor=actor, notes=body.notes
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "finalize_closing_package")
    return ok(result, operation_id="finalize_closing_package")


@router.post(
    "/{period}/package-versions/{package_version_id}/reopen",
    operation_id="reopen_package_version",
)
def reopen_package_version(
    request: Request,
    body: ReasonRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    package_version_id: uuid.UUID = Path(),
):
    try:
        actor = _manage_actor(request)
        result = _repository().reopen_version(
            period,
            str(package_version_id),
            actor=actor,
            reason=body.reason,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "reopen_package_version")
    return ok(result, operation_id="reopen_package_version")


@router.post(
    "/{period}/package-versions/{package_version_id}/complement",
    operation_id="create_package_complement",
)
def create_package_complement(
    request: Request,
    body: ReasonRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    package_version_id: uuid.UUID = Path(),
):
    try:
        actor = _manage_actor(request)
        result = _repository().create_complement(
            period,
            str(package_version_id),
            actor=actor,
            reason=body.reason,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "create_package_complement")
    return ok(result, operation_id="create_package_complement")


@router.post(
    "/{period}/package-versions/{package_version_id}/submit",
    operation_id="submit_package_for_review",
)
def submit_package_for_review(
    request: Request,
    body: SubmitRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    package_version_id: uuid.UUID = Path(),
):
    try:
        actor = _manage_actor(request)
        result = _repository().submit_for_review(
            period,
            str(package_version_id),
            actor=actor,
            expected_revision=body.revision,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "submit_package_for_review")
    return ok(result, operation_id="submit_package_for_review")


@router.post(
    "/{period}/assignments",
    operation_id="create_review_assignment",
)
def create_review_assignment(
    request: Request,
    body: AssignRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    try:
        actor = _manage_actor(request)
        result = _repository().assign_actor(
            period,
            actor=actor,
            role=body.role,
            subject=body.subject,
            recipient_area=body.recipient_area,
            area=body.area,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "create_review_assignment")
    return ok(result, operation_id="create_review_assignment")


@router.post(
    "/{period}/assignments/{assignment_id}/deactivate",
    operation_id="deactivate_review_assignment",
)
def deactivate_review_assignment(
    request: Request,
    body: DeactivateRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    assignment_id: uuid.UUID = Path(),
):
    try:
        actor = _manage_actor(request)
        result = _repository().deactivate_assignment(
            period,
            str(assignment_id),
            actor=actor,
            reason=body.reason,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "deactivate_review_assignment")
    return ok(result, operation_id="deactivate_review_assignment")


@router.post(
    "/{period}/package-versions/{package_version_id}/review/start",
    operation_id="start_package_review",
)
def start_package_review(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    package_version_id: uuid.UUID = Path(),
):
    try:
        actor = actor_subject(authorized_user(request))
        result = _repository().start_review(
            period, str(package_version_id), actor=actor
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "start_package_review")
    return ok(result, operation_id="start_package_review")


@router.post(
    "/{period}/package-versions/{package_version_id}/decisions",
    operation_id="record_review_decision",
)
def record_review_decision(
    request: Request,
    body: DecisionRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    package_version_id: uuid.UUID = Path(),
):
    try:
        actor = actor_subject(authorized_user(request))
        result = _repository().record_decision(
            period,
            str(package_version_id),
            actor=actor,
            area=body.area,
            outcome=body.outcome,
            note=body.note,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "record_review_decision")
    return ok(result, operation_id="record_review_decision")


@router.post(
    "/{period}/package-versions/{package_version_id}/clarifications",
    operation_id="open_package_clarification",
)
def open_package_clarification(
    request: Request,
    body: ClarificationRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    package_version_id: uuid.UUID = Path(),
):
    try:
        actor = actor_subject(authorized_user(request))
        result = _repository().open_clarification(
            period,
            str(package_version_id),
            actor=actor,
            question=body.question,
            area=body.area,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "open_package_clarification")
    return ok(result, operation_id="open_package_clarification")


@router.post(
    "/{period}/clarifications/{clarification_id}/resolve",
    operation_id="resolve_package_clarification",
)
def resolve_package_clarification(
    request: Request,
    body: ResolveRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
    clarification_id: uuid.UUID = Path(),
):
    try:
        actor = _manage_actor(request)
        result = _repository().resolve_clarification(
            period,
            str(clarification_id),
            actor=actor,
            response=body.response,
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "resolve_package_clarification")
    return ok(result, operation_id="resolve_package_clarification")


@router.post(
    "/{period}/terminal-rejection",
    operation_id="confirm_terminal_rejection",
)
def confirm_terminal_rejection(
    request: Request,
    body: ReasonRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    try:
        actor = actor_subject(authorized_user(request))
        result = _repository().confirm_terminal_rejection(
            period, actor=actor, reason=body.reason
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "confirm_terminal_rejection")
    return ok(result, operation_id="confirm_terminal_rejection")


@router.post(
    "/{period}/terminal-rejection/revert",
    operation_id="revert_terminal_rejection",
)
def revert_terminal_rejection(
    request: Request,
    body: ReasonRequest,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    try:
        actor = actor_subject(authorized_user(request))
        result = _repository().revert_terminal_rejection(
            period, actor=actor, reason=body.reason
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "revert_terminal_rejection")
    return ok(result, operation_id="revert_terminal_rejection")


@router.get(
    "/{period}/closing-state",
    operation_id="get_monthly_closing_state",
)
def get_monthly_closing_state(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    try:
        authorized_user(request)
        result = _repository().derive_closing_state(period)
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_monthly_closing_state")
    return ok(result, operation_id="get_monthly_closing_state")


@router.get(
    "/{period}/cockpit",
    operation_id="get_closing_cockpit",
)
def get_closing_cockpit(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
):
    try:
        authorized_user(request)
        result = _repository().get_cockpit(period)
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_closing_cockpit")
    return ok(result, operation_id="get_closing_cockpit")
