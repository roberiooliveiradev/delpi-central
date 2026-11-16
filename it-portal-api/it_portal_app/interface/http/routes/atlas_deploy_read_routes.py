"""P2.2h.2d: authenticated GET-only ATLAS OCI journal, default OFF.

No approval, PREPARE, ACT, migration, shell or host operations in this router.
The human must have EXPLICIT it-portal.deploy.view in fresh Core RBAC; even a
superadmin without the dedicated grant cannot read deployment metadata.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from it_portal_app.config import settings
from it_portal_app.core.responses import ok
from it_portal_app.domain.errors import PersistenceUnavailableError
from it_portal_app.infrastructure.persistence.atlas_deploy_read_repository import (
    PostgresAtlasDeployReadRepository,
)
from it_portal_app.interface.http.authz import ACCESS, actor_from, authorize_write
from it_portal_app.interface.http.schemas import ERROR_RESPONSES, Envelope

ATLAS_DEPLOY_VIEW = "it-portal.deploy.view"

router = APIRouter(
    tags=["ATLAS Journal (read-only)"],
    responses=ERROR_RESPONSES,
)

DeployEnvironment = Literal["prod", "hml"]
DeployStatus = Literal[
    "pending_approval", "approved", "revoked", "expired", "executing",
    "verified", "failed_needs_operator", "rolled_back",
]


class AtlasJournalItemOut(BaseModel):
    id: UUID
    requester_subject: UUID
    request_id: UUID
    environment: DeployEnvironment
    service_id: Literal["public-hub"]
    status: DeployStatus
    target_commit_sha: str
    base_commit_sha: str
    manifest_digest: str
    previous_image_id: str
    target_image_id: str
    rollback_image_id: str
    binding_sha256: str
    created_at: datetime
    expires_at: datetime
    expired: bool
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    revision: int = Field(ge=1)
    can_approve: Literal[False] = False
    can_execute: Literal[False] = False


class AtlasJournalEventOut(BaseModel):
    sequence: int = Field(ge=1)
    event_type: str
    actor_subject: UUID | None = None
    occurred_at: datetime


class AtlasJournalDetailOut(AtlasJournalItemOut):
    events: list[AtlasJournalEventOut]


class AtlasJournalPageOut(BaseModel):
    items: list[AtlasJournalItemOut]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=50)


def get_atlas_journal_reader() -> PostgresAtlasDeployReadRepository:
    return PostgresAtlasDeployReadRepository()


def _authorize_read(request: Request) -> None:
    # Existing authz uses force_refresh Core RBAC on synchronous worker routes.
    # Do not trust browser capabilities or grant-by-superadmin short-circuits.
    fresh = authorize_write(request, ATLAS_DEPLOY_VIEW)
    grants = getattr(fresh, "permissions", None)
    if (type(grants) not in (list, tuple)
            or ACCESS not in grants
            or ATLAS_DEPLOY_VIEW not in grants):
        raise Exception("Forbidden")
    if actor_from(fresh).id != actor_from(request.state.user).id:
        raise Exception("Forbidden")


def _require_read_enabled() -> None:
    if settings.ATLAS_JOURNAL_READ_ENABLED is not True:
        raise PersistenceUnavailableError(
            "atlas_journal_disabled",
            "Consulta de implantações ainda não habilitada.",
        )


@router.get(
    "/atlas/deployments",
    operation_id="list_atlas_deploy_journal",
    response_model=Envelope[AtlasJournalPageOut],
    summary="Lista propostas OCI persistidas (somente leitura, Core RBAC fresco)",
)
def list_atlas_deploy_journal(
    request: Request,
    environment: DeployEnvironment | None = Query(default=None),
    status: DeployStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1, le=1000),
    page_size: int = Query(default=20, ge=1, le=50),
    reader: PostgresAtlasDeployReadRepository = Depends(get_atlas_journal_reader),
):
    _authorize_read(request)
    _require_read_enabled()
    return ok(
        reader.list_proposals(
            environment=environment, status=status,
            page=page, page_size=page_size,
        ),
        operation_id="list_atlas_deploy_journal",
    )


@router.get(
    "/atlas/deployments/{proposal_id}",
    operation_id="get_atlas_deploy_journal",
    response_model=Envelope[AtlasJournalDetailOut],
    summary="Detalha proposta OCI e seus eventos (somente leitura)",
)
def get_atlas_deploy_journal(
    request: Request,
    proposal_id: UUID,
    reader: PostgresAtlasDeployReadRepository = Depends(get_atlas_journal_reader),
):
    _authorize_read(request)
    _require_read_enabled()
    return ok(
        reader.get_proposal(str(proposal_id)),
        operation_id="get_atlas_deploy_journal",
    )
