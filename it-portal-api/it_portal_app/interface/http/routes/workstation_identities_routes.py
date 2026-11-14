"""G2-S4: prepara identidade Keycloak exclusivamente DESABILITADA por dispositivo."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict

from it_portal_app.application.workstation_identity_service import WorkstationIdentityService
from it_portal_app.application.workstation_ports import WorkstationRepository
from it_portal_app.core.responses import ok
from it_portal_app.domain.errors import NotFoundError
from it_portal_app.interface.http.authz import (
    COMPUTERS_VIEW, COMPUTERS_MANAGE, actor_from, authorize, authorize_write,
)
from it_portal_app.interface.http.dependencies import (
    get_workstation_identity_service, get_workstation_repository,
)
from it_portal_app.interface.http.schemas import Envelope, ERROR_RESPONSES

router = APIRouter(prefix="/workstations", tags=["Workstation Agent Identities"], responses=ERROR_RESPONSES)


class PrepareIdentityInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmed: bool


@router.get(
    "/{workstation_id}/agent-identity",
    operation_id="get_it_workstation_agent_identity",
    response_model=Envelope[dict],
    summary="Estado do preparo da identidade individual (sem segredos)",
)
def get_identity(
    request: Request,
    workstation_id: UUID,
    service: WorkstationIdentityService = Depends(get_workstation_identity_service),
    workstations: WorkstationRepository = Depends(get_workstation_repository),
):
    authorize(request, COMPUTERS_VIEW)
    if workstations.get_workstation(str(workstation_id)) is None:
        raise NotFoundError("workstation_not_found", "Computador nao encontrado.")
    return ok(
        service.status(str(workstation_id)),
        operation_id="get_it_workstation_agent_identity",
    )


@router.post(
    "/{workstation_id}/agent-identity/prepare",
    operation_id="prepare_it_workstation_agent_identity",
    response_model=Envelope[dict],
    summary="Reserva e cria client DESABILITADO no Keycloak, sem token ou controle remoto",
)
def prepare_identity(
    request: Request,
    workstation_id: UUID,
    payload: PrepareIdentityInput,
    service: WorkstationIdentityService = Depends(get_workstation_identity_service),
):
    actor = actor_from(authorize_write(request, COMPUTERS_VIEW, COMPUTERS_MANAGE))
    result = service.prepare(str(workstation_id), actor, confirmed=payload.confirmed)
    return ok(
        result, "Identidade reservada e preparada, aguardando ativacao em piloto.",
        operation_id="prepare_it_workstation_agent_identity",
    )
