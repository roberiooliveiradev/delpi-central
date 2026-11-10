"""Rotas de instâncias de banco de dados e dos serviços consumidores (E2A)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from it_portal_app.application.database_inventory import DatabaseInventory
from it_portal_app.application.ports import DatabaseQuery
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.authz import (
    DATABASES_MANAGE,
    DATABASES_VIEW,
    SERVERS_VIEW,
    SERVICES_VIEW,
    actor_from,
    authorize,
)
from it_portal_app.interface.http.dependencies import get_database_inventory
from it_portal_app.interface.http.schemas import (
    ERROR_RESPONSES,
    DatabaseConsumerInput,
    DatabaseConsumerOut,
    DatabaseInstanceInput,
    DatabaseInstanceOut,
    DatabaseInstanceUpdateInput,
    Envelope,
    HistoryEventOut,
    LinkRemovedOut,
    PageOut,
    RevisionInput,
)

READ = (SERVERS_VIEW, DATABASES_VIEW)
WRITE = (*READ, DATABASES_MANAGE)

router = APIRouter(tags=["Database instances"], responses=ERROR_RESPONSES)

DatabaseSortKey = Literal["name", "dbms", "criticality", "environment", "created_at", "updated_at"]


@router.get(
    "/database-instances",
    operation_id="list_it_database_instances",
    response_model=Envelope[PageOut[DatabaseInstanceOut]],
    summary="Lista instâncias de banco com busca, filtros, ordenação e paginação",
)
def list_it_database_instances(
    request: Request,
    q: str | None = Query(default=None, max_length=120, description="Instância, versão ou servidor"),
    dbms: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    criticality: str | None = Query(default=None),
    server_id: UUID | None = Query(default=None, description="Somente instâncias deste servidor"),
    archived: Literal["active", "archived", "all"] = Query(default="active"),
    sort: DatabaseSortKey = Query(default="name"),
    direction: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    authorize(request, *READ)
    result = inventory.list_databases(
        DatabaseQuery(
            q=q,
            dbms=dbms,
            environment=environment,
            criticality=criticality,
            server_id=str(server_id) if server_id else None,
            archived=archived,
            sort=sort,
            direction=direction,
            page=page,
            page_size=page_size,
        )
    )
    return ok(result, operation_id="list_it_database_instances")


@router.post(
    "/database-instances",
    operation_id="create_it_database_instance",
    response_model=Envelope[DatabaseInstanceOut],
    status_code=201,
    summary="Cadastra uma instância de banco hospedada em um servidor existente",
)
def create_it_database_instance(
    request: Request,
    payload: DatabaseInstanceInput,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    user = authorize(request, *WRITE)
    created = inventory.create_database(payload.model_dump(), actor_from(user))
    return ok(created, "Instância cadastrada.", 201, operation_id="create_it_database_instance")


@router.get(
    "/database-instances/{database_id}",
    operation_id="get_it_database_instance",
    response_model=Envelope[DatabaseInstanceOut],
    summary="Detalhe da instância de banco",
)
def get_it_database_instance(
    request: Request,
    database_id: UUID,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    authorize(request, *READ)
    return ok(inventory.get_database(str(database_id)), operation_id="get_it_database_instance")


@router.put(
    "/database-instances/{database_id}",
    operation_id="update_it_database_instance",
    response_model=Envelope[DatabaseInstanceOut],
    summary="Atualiza a instância (concorrência otimista por revision)",
)
def update_it_database_instance(
    request: Request,
    database_id: UUID,
    payload: DatabaseInstanceUpdateInput,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    user = authorize(request, *WRITE)
    data = payload.model_dump(exclude={"revision"})
    updated = inventory.update_database(str(database_id), data, payload.revision, actor_from(user))
    return ok(updated, "Instância atualizada.", operation_id="update_it_database_instance")


@router.post(
    "/database-instances/{database_id}/archive",
    operation_id="archive_it_database_instance",
    response_model=Envelope[DatabaseInstanceOut],
    summary="Arquiva a instância (vínculos e histórico são preservados)",
)
def archive_it_database_instance(
    request: Request,
    database_id: UUID,
    payload: RevisionInput,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    user = authorize(request, *WRITE)
    archived = inventory.archive_database(str(database_id), payload.revision, actor_from(user))
    return ok(archived, "Instância arquivada.", operation_id="archive_it_database_instance")


@router.post(
    "/database-instances/{database_id}/restore",
    operation_id="restore_it_database_instance",
    response_model=Envelope[DatabaseInstanceOut],
    summary="Restaura uma instância arquivada",
)
def restore_it_database_instance(
    request: Request,
    database_id: UUID,
    payload: RevisionInput,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    user = authorize(request, *WRITE)
    restored = inventory.restore_database(str(database_id), payload.revision, actor_from(user))
    return ok(restored, "Instância restaurada.", operation_id="restore_it_database_instance")


@router.get(
    "/database-instances/{database_id}/history",
    operation_id="list_it_database_instance_history",
    response_model=Envelope[list[HistoryEventOut]],
    summary="Trilha de auditoria da instância e dos vínculos dela",
)
def list_it_database_instance_history(
    request: Request,
    database_id: UUID,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    authorize(request, *READ)
    return ok(
        inventory.list_history(str(database_id)),
        operation_id="list_it_database_instance_history",
    )


@router.get(
    "/database-instances/{database_id}/consumers",
    operation_id="list_it_database_consumers",
    response_model=Envelope[list[DatabaseConsumerOut]],
    summary="Serviços que consomem a instância de banco",
)
def list_it_database_consumers(
    request: Request,
    database_id: UUID,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    authorize(request, *READ, SERVICES_VIEW)
    return ok(
        inventory.list_database_consumers(str(database_id)),
        operation_id="list_it_database_consumers",
    )


@router.post(
    "/database-consumers",
    operation_id="create_it_database_consumer",
    response_model=Envelope[DatabaseConsumerOut],
    status_code=201,
    summary="Vincula um serviço consumidor a uma instância de banco",
)
def create_it_database_consumer(
    request: Request,
    payload: DatabaseConsumerInput,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    user = authorize(request, *WRITE, SERVICES_VIEW)
    consumer = inventory.link_consumer(payload.model_dump(), actor_from(user))
    return ok(consumer, "Vínculo registrado.", 201, operation_id="create_it_database_consumer")


@router.delete(
    "/database-consumers/{consumer_id}",
    operation_id="delete_it_database_consumer",
    response_model=Envelope[LinkRemovedOut],
    summary="Remove o vínculo de consumo (instância e serviço são preservados)",
)
def delete_it_database_consumer(
    request: Request,
    consumer_id: UUID,
    inventory: DatabaseInventory = Depends(get_database_inventory),
):
    user = authorize(request, *WRITE, SERVICES_VIEW)
    inventory.unlink_consumer(str(consumer_id), actor_from(user))
    return ok(
        {"id": str(consumer_id)}, "Vínculo removido.", operation_id="delete_it_database_consumer"
    )
