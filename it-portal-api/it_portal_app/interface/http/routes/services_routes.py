"""Rotas de serviços/aplicações e da hospedagem deles em servidores (E2A)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from it_portal_app.application.database_inventory import DatabaseInventory
from it_portal_app.application.ports import ServiceQuery
from it_portal_app.application.service_inventory import ServiceInventory
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.authz import (
    DATABASES_VIEW,
    SERVERS_VIEW,
    SERVICES_MANAGE,
    SERVICES_VIEW,
    actor_from,
    authorize,
)
from it_portal_app.interface.http.dependencies import (
    get_database_inventory,
    get_service_inventory,
)
from it_portal_app.interface.http.schemas import (
    ERROR_RESPONSES,
    DatabaseConsumerOut,
    Envelope,
    HistoryEventOut,
    LinkRemovedOut,
    PageOut,
    RevisionInput,
    ServiceHostingInput,
    ServiceHostingOut,
    ServiceInput,
    ServiceOut,
    ServiceUpdateInput,
)

READ = (SERVERS_VIEW, SERVICES_VIEW)
WRITE = (*READ, SERVICES_MANAGE)

router = APIRouter(tags=["Services"], responses=ERROR_RESPONSES)

ServiceSortKey = Literal["name", "criticality", "environment", "created_at", "updated_at"]


@router.get(
    "/services",
    operation_id="list_it_services",
    response_model=Envelope[PageOut[ServiceOut]],
    summary="Lista serviços e aplicações com busca, filtros, ordenação e paginação",
)
def list_it_services(
    request: Request,
    q: str | None = Query(default=None, max_length=120, description="Nome ou tecnologia"),
    service_kind: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    unit_code: str | None = Query(default=None),
    criticality: str | None = Query(default=None),
    archived: Literal["active", "archived", "all"] = Query(default="active"),
    sort: ServiceSortKey = Query(default="name"),
    direction: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    authorize(request, *READ)
    result = inventory.list_services(
        ServiceQuery(
            q=q,
            service_kind=service_kind,
            environment=environment,
            unit_code=unit_code,
            criticality=criticality,
            archived=archived,
            sort=sort,
            direction=direction,
            page=page,
            page_size=page_size,
        )
    )
    return ok(result, operation_id="list_it_services")


@router.post(
    "/services",
    operation_id="create_it_service",
    response_model=Envelope[ServiceOut],
    status_code=201,
    summary="Cadastra um serviço ou aplicação",
)
def create_it_service(
    request: Request,
    payload: ServiceInput,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    user = authorize(request, *WRITE)
    created = inventory.create_service(payload.model_dump(), actor_from(user))
    return ok(created, "Serviço cadastrado.", 201, operation_id="create_it_service")


@router.get(
    "/services/{service_id}",
    operation_id="get_it_service",
    response_model=Envelope[ServiceOut],
    summary="Detalhe do serviço",
)
def get_it_service(
    request: Request,
    service_id: UUID,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    authorize(request, *READ)
    return ok(inventory.get_service(str(service_id)), operation_id="get_it_service")


@router.put(
    "/services/{service_id}",
    operation_id="update_it_service",
    response_model=Envelope[ServiceOut],
    summary="Atualiza o serviço (concorrência otimista por revision)",
)
def update_it_service(
    request: Request,
    service_id: UUID,
    payload: ServiceUpdateInput,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    user = authorize(request, *WRITE)
    data = payload.model_dump(exclude={"revision"})
    updated = inventory.update_service(str(service_id), data, payload.revision, actor_from(user))
    return ok(updated, "Serviço atualizado.", operation_id="update_it_service")


@router.post(
    "/services/{service_id}/archive",
    operation_id="archive_it_service",
    response_model=Envelope[ServiceOut],
    summary="Arquiva o serviço (vínculos e histórico são preservados)",
)
def archive_it_service(
    request: Request,
    service_id: UUID,
    payload: RevisionInput,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    user = authorize(request, *WRITE)
    archived = inventory.archive_service(str(service_id), payload.revision, actor_from(user))
    return ok(archived, "Serviço arquivado.", operation_id="archive_it_service")


@router.post(
    "/services/{service_id}/restore",
    operation_id="restore_it_service",
    response_model=Envelope[ServiceOut],
    summary="Restaura um serviço arquivado",
)
def restore_it_service(
    request: Request,
    service_id: UUID,
    payload: RevisionInput,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    user = authorize(request, *WRITE)
    restored = inventory.restore_service(str(service_id), payload.revision, actor_from(user))
    return ok(restored, "Serviço restaurado.", operation_id="restore_it_service")


@router.get(
    "/services/{service_id}/history",
    operation_id="list_it_service_history",
    response_model=Envelope[list[HistoryEventOut]],
    summary="Trilha de auditoria do serviço e dos vínculos dele",
)
def list_it_service_history(
    request: Request,
    service_id: UUID,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    authorize(request, *READ)
    return ok(inventory.list_history(str(service_id)), operation_id="list_it_service_history")


@router.get(
    "/services/{service_id}/hostings",
    operation_id="list_it_service_hostings",
    response_model=Envelope[list[ServiceHostingOut]],
    summary="Servidores onde o serviço roda",
)
def list_it_service_hostings(
    request: Request,
    service_id: UUID,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    authorize(request, *READ)
    return ok(
        inventory.list_service_hostings(str(service_id)),
        operation_id="list_it_service_hostings",
    )


@router.get(
    "/services/{service_id}/database-instances",
    operation_id="list_it_service_database_links",
    response_model=Envelope[list[DatabaseConsumerOut]],
    summary="Instâncias de banco consumidas pelo serviço",
)
def list_it_service_database_links(
    request: Request,
    service_id: UUID,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    authorize(request, *READ, DATABASES_VIEW)
    return ok(
        inventory.list_service_databases(str(service_id)),
        operation_id="list_it_service_database_links",
    )


@router.get(
    "/servers/{server_id}/service-hostings",
    operation_id="list_it_server_service_hostings",
    response_model=Envelope[list[ServiceHostingOut]],
    summary="Serviços hospedados no servidor",
)
def list_it_server_service_hostings(
    request: Request,
    server_id: UUID,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    authorize(request, *READ)
    return ok(
        inventory.list_server_hostings(str(server_id)),
        operation_id="list_it_server_service_hostings",
    )


@router.post(
    "/service-hostings",
    operation_id="create_it_service_hosting",
    response_model=Envelope[ServiceHostingOut],
    status_code=201,
    summary="Vincula um serviço a um servidor existente (hospedagem)",
)
def create_it_service_hosting(
    request: Request,
    payload: ServiceHostingInput,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    user = authorize(request, *WRITE)
    hosting = inventory.link_service_to_server(payload.model_dump(), actor_from(user))
    return ok(hosting, "Vínculo registrado.", 201, operation_id="create_it_service_hosting")


@router.delete(
    "/service-hostings/{hosting_id}",
    operation_id="delete_it_service_hosting",
    response_model=Envelope[LinkRemovedOut],
    summary="Remove o vínculo de hospedagem (serviço e servidor são preservados)",
)
def delete_it_service_hosting(
    request: Request,
    hosting_id: UUID,
    inventory: ServiceInventory = Depends(get_service_inventory),
):
    user = authorize(request, *WRITE)
    inventory.unlink_hosting(str(hosting_id), actor_from(user))
    return ok(
        {"id": str(hosting_id)}, "Vínculo removido.", operation_id="delete_it_service_hosting"
    )
