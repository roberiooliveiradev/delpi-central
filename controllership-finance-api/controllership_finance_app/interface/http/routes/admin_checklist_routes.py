"""P6-MIN — administração do template de checklist por API (CP-D05=A).

Operações administrativas: consultar template/versões/eventos de
auditoria, criar e editar DRAFT (OCC `revision`), publicar com vigência
prospectiva e inativar. Autorização: `controllership-finance.manage`
efetivo (Core é a única autoridade). Consumida pela página
«Administração do checklist» do MFE (`closing/admin`).
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.interface.http.authz import (
    actor_subject,
    authorized_admin,
)

router = APIRouter(
    prefix="/admin/checklist-templates",
    tags=["Closing Checklist Admin"],
)

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class ChecklistItemInput(BaseModel):
    item_key: str = Field(min_length=1, max_length=32)
    sort_order: int | None = None
    sheet: str = Field(pattern="^(ELETRONICO|FISICO)$")
    name: str = Field(min_length=1, max_length=255)
    purpose: str | None = None
    origin_kind: str = Field(pattern="^(TOTVS|EXTERNAL|MIXED)$")
    recipient_area: str | None = Field(
        default=None, pattern="^(CONTABIL|FISCAL)$"
    )
    applicability: str = Field(
        default="REQUIRED", pattern="^(REQUIRED|CONDITIONAL|OPTIONAL)$"
    )
    branch_scope: str = Field(
        default="BOTH", pattern="^(MATRIX|BRANCH|BOTH)$"
    )
    totvs_report_ref: str | None = Field(default=None, max_length=8)
    requirement_notes: str | None = None
    validation_scope: str = Field(
        default="PER_ATTACHMENT",
        pattern="^(PER_ATTACHMENT|WHOLE_SET)$",
    )


class UpdateDraftRequest(BaseModel):
    revision: int = Field(ge=1)
    items: list[ChecklistItemInput] = Field(min_length=1)


class PublishVersionRequest(BaseModel):
    effective_from_period: str = Field(pattern=PERIOD_PATTERN)


class ReturnToDraftRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


def _repository() -> ClosingChecklistRepository:
    return ClosingChecklistRepository()


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


@router.get("", operation_id="list_checklist_templates")
def list_checklist_templates(request: Request):
    authorized_admin(request)
    try:
        templates = _repository().list_templates()
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_checklist_templates")
    return ok(
        {"templates": templates},
        operation_id="list_checklist_templates",
    )


@router.get(
    "/{template_id}/versions",
    operation_id="list_checklist_template_versions",
)
def list_checklist_template_versions(request: Request, template_id: str):
    authorized_admin(request)
    try:
        versions = _repository().list_versions(template_id)
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_checklist_template_versions")
    return ok(
        {"versions": versions},
        operation_id="list_checklist_template_versions",
    )


@router.get(
    "/{template_id}/versions/{version}",
    operation_id="get_checklist_template_version",
)
def get_checklist_template_version(
    request: Request, template_id: str, version: int
):
    authorized_admin(request)
    try:
        version_row = _repository().get_version_with_items(
            template_id, version
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "get_checklist_template_version")
    return ok(version_row, operation_id="get_checklist_template_version")


@router.get(
    "/{template_id}/events",
    operation_id="list_checklist_template_events",
)
def list_checklist_template_events(
    request: Request,
    template_id: str,
    version: int | None = Query(default=None),
):
    authorized_admin(request)
    try:
        events = _repository().list_template_events(template_id, version)
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_checklist_template_events")
    return ok(
        {"events": events},
        operation_id="list_checklist_template_events",
    )


@router.post(
    "/{template_id}/versions",
    operation_id="create_checklist_template_draft",
    status_code=201,
)
def create_checklist_template_draft(request: Request, template_id: str):
    user = authorized_admin(request)
    try:
        draft = _repository().create_draft_version(
            template_id, actor=actor_subject(user)
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "create_checklist_template_draft")
    return ok(
        draft,
        message="Versão DRAFT criada.",
        status_code=201,
        operation_id="create_checklist_template_draft",
    )


@router.put(
    "/{template_id}/versions/{version}",
    operation_id="update_checklist_template_draft",
)
def update_checklist_template_draft(
    request: Request,
    template_id: str,
    version: int,
    body: UpdateDraftRequest,
):
    user = authorized_admin(request)
    try:
        updated = _repository().update_draft_items(
            template_id,
            version,
            expected_revision=body.revision,
            items=[item.model_dump() for item in body.items],
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "update_checklist_template_draft")
    return ok(
        updated,
        message="Versão DRAFT atualizada.",
        operation_id="update_checklist_template_draft",
    )


@router.post(
    "/{template_id}/versions/{version}/publish",
    operation_id="publish_checklist_template_version",
)
def publish_checklist_template_version(
    request: Request,
    template_id: str,
    version: int,
    body: PublishVersionRequest,
):
    user = authorized_admin(request)
    try:
        published = _repository().publish_version(
            template_id,
            version,
            effective_from_period=body.effective_from_period,
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "publish_checklist_template_version")
    return ok(
        published,
        message="Versão publicada.",
        operation_id="publish_checklist_template_version",
    )


@router.post(
    "/{template_id}/versions/{version}/submit-review",
    operation_id="submit_checklist_version_for_review",
)
def submit_checklist_version_for_review(
    request: Request, template_id: str, version: int
):
    user = authorized_admin(request)
    try:
        submitted = _repository().submit_version_for_review(
            template_id, version, actor=actor_subject(user)
        )
    except ChecklistDomainError as exc:
        return _domain_fail(
            exc, "submit_checklist_version_for_review"
        )
    return ok(
        submitted,
        message="Versão enviada para revisão administrativa.",
        operation_id="submit_checklist_version_for_review",
    )


@router.post(
    "/{template_id}/versions/{version}/return-to-draft",
    operation_id="return_checklist_version_to_draft",
)
def return_checklist_version_to_draft(
    request: Request,
    template_id: str,
    version: int,
    body: ReturnToDraftRequest,
):
    user = authorized_admin(request)
    try:
        returned = _repository().return_version_to_draft(
            template_id,
            version,
            reason=body.reason,
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(
            exc, "return_checklist_version_to_draft"
        )
    return ok(
        returned,
        message="Versão devolvida a rascunho.",
        operation_id="return_checklist_version_to_draft",
    )


@router.post(
    "/{template_id}/versions/{version}/inactivate",
    operation_id="inactivate_checklist_template_version",
)
def inactivate_checklist_template_version(
    request: Request, template_id: str, version: int
):
    user = authorized_admin(request)
    try:
        inactivated = _repository().inactivate_version(
            template_id, version, actor=actor_subject(user)
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "inactivate_checklist_template_version")
    return ok(
        inactivated,
        message="Versão inativada prospectivamente.",
        operation_id="inactivate_checklist_template_version",
    )
