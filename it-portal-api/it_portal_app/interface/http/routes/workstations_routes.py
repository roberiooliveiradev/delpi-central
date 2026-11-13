"""G1-API: inventario curado de desktops/notebooks, sem comandos remotos."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from it_portal_app.application.workstation_ports import WorkstationQuery
from it_portal_app.application.workstation_service import WorkstationService
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.authz import (
    COMPUTERS_MANAGE,
    COMPUTERS_VIEW,
    actor_from,
    authorize,
    authorize_write,
)
from it_portal_app.interface.http.dependencies import get_workstation_service
from it_portal_app.interface.http.schemas import (
    ERROR_RESPONSES,
    Envelope,
    HistoryEventOut,
    PageOut,
    RevisionInput,
    WorkstationInput,
    WorkstationOut,
    WorkstationUpdateInput,
)

router = APIRouter(prefix="/workstations", tags=["Workstations"], responses=ERROR_RESPONSES)
WorkstationSort = Literal["name", "hostname", "device_kind", "created_at", "updated_at"]


@router.get(
    "",
    operation_id="list_it_workstations",
    response_model=Envelope[PageOut[WorkstationOut]],
    summary="Lista computadores autorizados para inventario",
)
def list_it_workstations(
    request: Request,
    q: str | None = Query(default=None, max_length=120),
    unit_code: str | None = Query(default=None),
    device_kind: str | None = Query(default=None),
    administrative_status: str | None = Query(default=None),
    archived: Literal["active", "archived", "all"] = Query(default="active"),
    sort: WorkstationSort = Query(default="name"),
    direction: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: WorkstationService = Depends(get_workstation_service),
):
    authorize(request, COMPUTERS_VIEW)
    return ok(
        service.list_workstations(
            WorkstationQuery(
                q=q,
                unit_code=unit_code,
                device_kind=device_kind,
                administrative_status=administrative_status,
                archived=archived,
                sort=sort,
                direction=direction,
                page=page,
                page_size=page_size,
            )
        ),
        operation_id="list_it_workstations",
    )


@router.post(
    "",
    operation_id="create_it_workstation",
    status_code=201,
    response_model=Envelope[WorkstationOut],
    summary="Cadastra computador sem habilitar acesso remoto",
)
def create_it_workstation(
    request: Request,
    payload: WorkstationInput,
    service: WorkstationService = Depends(get_workstation_service),
):
    user = authorize_write(request, COMPUTERS_VIEW, COMPUTERS_MANAGE)
    data = service.create_workstation(
        payload.model_dump(exclude_unset=True), actor_from(user),
        access_token=str(getattr(user, "access_token", "") or ""),
    )
    return ok(data, "Computador cadastrado.", 201, operation_id="create_it_workstation")


@router.get(
    "/{workstation_id}",
    operation_id="get_it_workstation",
    response_model=Envelope[WorkstationOut],
    summary="Consulta computador pelo identificador UUID",
)
def get_it_workstation(
    request: Request,
    workstation_id: UUID,
    service: WorkstationService = Depends(get_workstation_service),
):
    authorize(request, COMPUTERS_VIEW)
    return ok(service.get_workstation(str(workstation_id)), operation_id="get_it_workstation")


@router.put(
    "/{workstation_id}",
    operation_id="update_it_workstation",
    response_model=Envelope[WorkstationOut],
    summary="Atualiza computador com versao otimista e auditoria",
)
def update_it_workstation(
    request: Request,
    workstation_id: UUID,
    payload: WorkstationUpdateInput,
    service: WorkstationService = Depends(get_workstation_service),
):
    user = authorize_write(request, COMPUTERS_VIEW, COMPUTERS_MANAGE)
    updated = service.update_workstation(
        str(workstation_id), payload.model_dump(exclude={"revision"}, exclude_unset=True),
        payload.revision, actor_from(user),
        access_token=str(getattr(user, "access_token", "") or ""),
    )
    return ok(updated, "Computador atualizado.", operation_id="update_it_workstation")


@router.post(
    "/{workstation_id}/archive",
    operation_id="archive_it_workstation",
    response_model=Envelope[WorkstationOut],
    summary="Arquiva cadastro preservando o historico",
)
def archive_it_workstation(
    request: Request,
    workstation_id: UUID,
    payload: RevisionInput,
    service: WorkstationService = Depends(get_workstation_service),
):
    user = authorize_write(request, COMPUTERS_VIEW, COMPUTERS_MANAGE)
    data = service.archive_workstation(str(workstation_id), payload.revision, actor_from(user))
    return ok(data, "Computador arquivado.", operation_id="archive_it_workstation")


@router.post(
    "/{workstation_id}/restore",
    operation_id="restore_it_workstation",
    response_model=Envelope[WorkstationOut],
    summary="Restaura cadastro arquivado",
)
def restore_it_workstation(
    request: Request,
    workstation_id: UUID,
    payload: RevisionInput,
    service: WorkstationService = Depends(get_workstation_service),
):
    user = authorize_write(request, COMPUTERS_VIEW, COMPUTERS_MANAGE)
    data = service.restore_workstation(str(workstation_id), payload.revision, actor_from(user))
    return ok(data, "Computador restaurado.", operation_id="restore_it_workstation")


@router.get(
    "/{workstation_id}/history",
    operation_id="list_it_workstation_history",
    response_model=Envelope[list[HistoryEventOut]],
    summary="Historico auditavel de alteracoes do computador",
)
def list_it_workstation_history(
    request: Request,
    workstation_id: UUID,
    service: WorkstationService = Depends(get_workstation_service),
):
    authorize(request, COMPUTERS_VIEW)
    return ok(service.list_history(str(workstation_id)), operation_id="list_it_workstation_history")
