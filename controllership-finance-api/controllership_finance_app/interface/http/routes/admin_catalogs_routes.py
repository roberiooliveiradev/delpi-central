"""P6 — administração dos catálogos governados do fechamento (doc 105/F1).

`closing_catalog_entry` cobre BANK_ACCOUNT, REJECTION_REASON,
ATTACHMENT_ROLE, NOTIFICATION_TARGET, PACKAGE_REQUIRED_AREA (P5-H) e
REVIEW_ELIGIBILITY (T05-binding). Códigos imutáveis; edição com OCC
(`revision`); desativação prospectiva — nunca delete, histórico
referenciável por pacotes/competências já fechados.

Autorização: `controllership-finance.manage` efetivo (Core).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.infrastructure.persistence.closing_catalog_repository import (
    CATALOG_KEYS,
    ClosingCatalogRepository,
)
from controllership_finance_app.interface.http.authz import (
    actor_subject,
    authorized_admin,
)

router = APIRouter(
    prefix="/admin/closing-catalogs",
    tags=["Closing Catalogs Admin"],
)

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


class CreateEntryRequest(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=255)
    attributes: dict[str, Any] | None = None
    effective_from_period: str | None = Field(
        default=None, pattern=PERIOD_PATTERN
    )


class UpdateEntryRequest(BaseModel):
    label: str | None = Field(default=None, max_length=255)
    attributes: dict[str, Any] | None = None
    revision: int = Field(ge=1)


class RevisionRequest(BaseModel):
    revision: int = Field(ge=1)


def _repository() -> ClosingCatalogRepository:
    return ClosingCatalogRepository()


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


@router.get("", operation_id="list_closing_catalogs")
def list_closing_catalogs(request: Request):
    """Inventário dos catálogos disponíveis + contagem de entradas."""
    authorized_admin(request)
    try:
        entries = _repository().list_entries()
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_closing_catalogs")
    counts: dict[str, dict[str, int]] = {
        key: {"active": 0, "inactive": 0} for key in CATALOG_KEYS
    }
    for entry in entries:
        bucket = "active" if entry["active"] else "inactive"
        counts[entry["catalog_key"]][bucket] += 1
    return ok(
        {
            "catalogs": [
                {"catalog_key": key, **counts[key]}
                for key in CATALOG_KEYS
            ]
        },
        operation_id="list_closing_catalogs",
    )


@router.get(
    "/{catalog_key}/entries",
    operation_id="list_closing_catalog_entries",
)
def list_closing_catalog_entries(
    request: Request,
    catalog_key: str,
    include_inactive: bool = Query(default=True),
):
    authorized_admin(request)
    try:
        entries = _repository().list_entries(
            catalog_key.upper(), include_inactive=include_inactive
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_closing_catalog_entries")
    return ok(
        {"items": entries},
        operation_id="list_closing_catalog_entries",
    )


@router.post(
    "/{catalog_key}/entries",
    operation_id="create_closing_catalog_entry",
)
def create_closing_catalog_entry(
    request: Request,
    catalog_key: str,
    body: CreateEntryRequest,
):
    user = authorized_admin(request)
    try:
        entry = _repository().create_entry(
            catalog_key.upper(),
            code=body.code,
            label=body.label,
            attributes=body.attributes,
            effective_from_period=body.effective_from_period,
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "create_closing_catalog_entry")
    return ok(
        entry,
        message="Entrada de catálogo criada.",
        operation_id="create_closing_catalog_entry",
    )


@router.put(
    "/{catalog_key}/entries/{code}",
    operation_id="update_closing_catalog_entry",
)
def update_closing_catalog_entry(
    request: Request,
    catalog_key: str,
    code: str,
    body: UpdateEntryRequest,
):
    user = authorized_admin(request)
    try:
        entry = _repository().update_entry(
            catalog_key.upper(),
            code,
            label=body.label,
            attributes=body.attributes,
            expected_revision=body.revision,
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "update_closing_catalog_entry")
    return ok(
        entry,
        message="Entrada de catálogo atualizada.",
        operation_id="update_closing_catalog_entry",
    )


@router.post(
    "/{catalog_key}/entries/{code}/deactivate",
    operation_id="deactivate_closing_catalog_entry",
)
def deactivate_closing_catalog_entry(
    request: Request,
    catalog_key: str,
    code: str,
    body: RevisionRequest,
):
    user = authorized_admin(request)
    try:
        entry = _repository().deactivate_entry(
            catalog_key.upper(),
            code,
            expected_revision=body.revision,
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "deactivate_closing_catalog_entry")
    return ok(
        entry,
        message="Entrada desativada prospectivamente.",
        operation_id="deactivate_closing_catalog_entry",
    )


@router.post(
    "/{catalog_key}/entries/{code}/reactivate",
    operation_id="reactivate_closing_catalog_entry",
)
def reactivate_closing_catalog_entry(
    request: Request, catalog_key: str, code: str
):
    user = authorized_admin(request)
    try:
        entry = _repository().reactivate_entry(
            catalog_key.upper(),
            code,
            actor=actor_subject(user),
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "reactivate_closing_catalog_entry")
    return ok(
        entry,
        message="Entrada reativada.",
        operation_id="reactivate_closing_catalog_entry",
    )
