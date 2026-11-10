"""Rotas de integrações e dependências operacionais entre serviços (E2B)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from it_portal_app.application.integration_inventory import IntegrationInventory
from it_portal_app.application.ports import IntegrationQuery
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.authz import (
    INTEGRATIONS_MANAGE,
    INTEGRATIONS_VIEW,
    SERVERS_VIEW,
    SERVICES_MANAGE,
    SERVICES_VIEW,
    actor_from,
    authorize,
    authorize_write,
)
from it_portal_app.interface.http.dependencies import get_integration_inventory
from it_portal_app.interface.http.schemas import (
    ERROR_RESPONSES,
    Envelope,
    HistoryEventOut,
    IntegrationInput,
    IntegrationOut,
    IntegrationUpdateInput,
    LinkRemovedOut,
    PageOut,
    RevisionInput,
    ServiceDependencyInput,
    ServiceDependencyOut,
)

READ = (SERVERS_VIEW, SERVICES_VIEW, INTEGRATIONS_VIEW)
WRITE = (*READ, INTEGRATIONS_MANAGE)
DEPENDENCY_READ = (SERVERS_VIEW, SERVICES_VIEW)
DEPENDENCY_WRITE = (*DEPENDENCY_READ, SERVICES_MANAGE)

router = APIRouter(tags=["Integrations"], responses=ERROR_RESPONSES)

IntegrationSortKey = Literal["name", "criticality", "protocol", "created_at", "updated_at"]


@router.get(
    "/integrations",
    operation_id="list_it_integrations",
    response_model=Envelope[PageOut[IntegrationOut]],
    summary="Lista integrações com busca, filtros, ordenação e paginação",
)
def list_it_integrations(
    request: Request,
    q: str | None = Query(
        default=None, max_length=120, description="Nome da integração, serviço ou sistema externo"
    ),
    service_id: UUID | None = Query(default=None, description="Serviço em qualquer das pontas"),
    protocol: str | None = Query(default=None),
    criticality: str | None = Query(default=None),
    administrative_status: str | None = Query(default=None),
    archived: Literal["active", "archived", "all"] = Query(default="active"),
    sort: IntegrationSortKey = Query(default="name"),
    direction: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    authorize(request, *READ)
    result = inventory.list_integrations(
        IntegrationQuery(
            q=q,
            service_id=str(service_id) if service_id else None,
            protocol=protocol,
            criticality=criticality,
            administrative_status=administrative_status,
            archived=archived,
            sort=sort,
            direction=direction,
            page=page,
            page_size=page_size,
        )
    )
    return ok(result, operation_id="list_it_integrations")


@router.post(
    "/integrations",
    operation_id="create_it_integration",
    response_model=Envelope[IntegrationOut],
    status_code=201,
    summary="Cadastra uma integração (origem e destino: serviço cadastrado ou sistema externo)",
)
def create_it_integration(
    request: Request,
    payload: IntegrationInput,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    user = authorize_write(request, *WRITE)
    created = inventory.create_integration(payload.model_dump(), actor_from(user))
    return ok(created, "Integração cadastrada.", 201, operation_id="create_it_integration")


@router.get(
    "/integrations/{integration_id}",
    operation_id="get_it_integration",
    response_model=Envelope[IntegrationOut],
    summary="Detalhe da integração",
)
def get_it_integration(
    request: Request,
    integration_id: UUID,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    authorize(request, *READ)
    return ok(inventory.get_integration(str(integration_id)), operation_id="get_it_integration")


@router.put(
    "/integrations/{integration_id}",
    operation_id="update_it_integration",
    response_model=Envelope[IntegrationOut],
    summary="Atualiza a integração (concorrência otimista por revision)",
)
def update_it_integration(
    request: Request,
    integration_id: UUID,
    payload: IntegrationUpdateInput,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    user = authorize_write(request, *WRITE)
    data = payload.model_dump(exclude={"revision"})
    updated = inventory.update_integration(
        str(integration_id), data, payload.revision, actor_from(user)
    )
    return ok(updated, "Integração atualizada.", operation_id="update_it_integration")


@router.post(
    "/integrations/{integration_id}/archive",
    operation_id="archive_it_integration",
    response_model=Envelope[IntegrationOut],
    summary="Arquiva a integração (serviços e histórico são preservados)",
)
def archive_it_integration(
    request: Request,
    integration_id: UUID,
    payload: RevisionInput,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    user = authorize_write(request, *WRITE)
    archived = inventory.archive_integration(
        str(integration_id), payload.revision, actor_from(user)
    )
    return ok(archived, "Integração arquivada.", operation_id="archive_it_integration")


@router.post(
    "/integrations/{integration_id}/restore",
    operation_id="restore_it_integration",
    response_model=Envelope[IntegrationOut],
    summary="Restaura uma integração arquivada",
)
def restore_it_integration(
    request: Request,
    integration_id: UUID,
    payload: RevisionInput,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    user = authorize_write(request, *WRITE)
    restored = inventory.restore_integration(
        str(integration_id), payload.revision, actor_from(user)
    )
    return ok(restored, "Integração restaurada.", operation_id="restore_it_integration")


@router.get(
    "/integrations/{integration_id}/history",
    operation_id="list_it_integration_history",
    response_model=Envelope[list[HistoryEventOut]],
    summary="Trilha de auditoria da integração",
)
def list_it_integration_history(
    request: Request,
    integration_id: UUID,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    authorize(request, *READ)
    return ok(
        inventory.list_history(str(integration_id)),
        operation_id="list_it_integration_history",
    )


@router.get(
    "/services/{service_id}/integrations",
    operation_id="list_it_service_integrations",
    response_model=Envelope[list[IntegrationOut]],
    summary="Integrações em que o serviço é origem ou destino",
)
def list_it_service_integrations(
    request: Request,
    service_id: UUID,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    authorize(request, *READ)
    return ok(
        inventory.list_service_integrations(str(service_id)),
        operation_id="list_it_service_integrations",
    )


@router.get(
    "/servers/{server_id}/integrations",
    operation_id="list_it_server_integrations",
    response_model=Envelope[list[IntegrationOut]],
    summary="Integrações dos serviços hospedados no servidor",
)
def list_it_server_integrations(
    request: Request,
    server_id: UUID,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    authorize(request, *READ)
    return ok(
        inventory.list_server_integrations(str(server_id)),
        operation_id="list_it_server_integrations",
    )


@router.get(
    "/services/{service_id}/dependencies",
    operation_id="list_it_service_dependencies",
    response_model=Envelope[list[ServiceDependencyOut]],
    summary="Dependências operacionais do serviço (das quais depende e que dependem dele)",
)
def list_it_service_dependencies(
    request: Request,
    service_id: UUID,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    authorize(request, *DEPENDENCY_READ)
    return ok(
        inventory.list_service_dependencies(str(service_id)),
        operation_id="list_it_service_dependencies",
    )


@router.post(
    "/service-dependencies",
    operation_id="create_it_service_dependency",
    response_model=Envelope[ServiceDependencyOut],
    status_code=201,
    summary="Registra uma dependência operacional explícita entre dois serviços",
)
def create_it_service_dependency(
    request: Request,
    payload: ServiceDependencyInput,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    user = authorize_write(request, *DEPENDENCY_WRITE)
    dependency = inventory.link_dependency(payload.model_dump(), actor_from(user))
    return ok(
        dependency, "Dependência registrada.", 201, operation_id="create_it_service_dependency"
    )


@router.delete(
    "/service-dependencies/{dependency_id}",
    operation_id="delete_it_service_dependency",
    response_model=Envelope[LinkRemovedOut],
    summary="Remove a dependência operacional (os serviços são preservados)",
)
def delete_it_service_dependency(
    request: Request,
    dependency_id: UUID,
    inventory: IntegrationInventory = Depends(get_integration_inventory),
):
    user = authorize_write(request, *DEPENDENCY_WRITE)
    inventory.unlink_dependency(str(dependency_id), actor_from(user))
    return ok(
        {"id": str(dependency_id)},
        "Dependência removida.",
        operation_id="delete_it_service_dependency",
    )
