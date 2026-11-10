"""Rotas de redes e da conectividade servidor ↔ rede (E2B)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from it_portal_app.application.network_inventory import NetworkInventory
from it_portal_app.application.ports import NetworkQuery
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.authz import (
    NETWORKS_MANAGE,
    NETWORKS_VIEW,
    SERVERS_VIEW,
    actor_from,
    authorize,
    authorize_write,
)
from it_portal_app.interface.http.dependencies import get_network_inventory
from it_portal_app.interface.http.schemas import (
    ERROR_RESPONSES,
    Envelope,
    HistoryEventOut,
    LinkRemovedOut,
    NetworkInput,
    NetworkOut,
    NetworkUpdateInput,
    PageOut,
    RevisionInput,
    ServerNetworkLinkInput,
    ServerNetworkLinkOut,
)

READ = (SERVERS_VIEW, NETWORKS_VIEW)
WRITE = (*READ, NETWORKS_MANAGE)

router = APIRouter(tags=["Networks"], responses=ERROR_RESPONSES)

NetworkSortKey = Literal["name", "criticality", "environment", "created_at", "updated_at"]


@router.get(
    "/networks",
    operation_id="list_it_networks",
    response_model=Envelope[PageOut[NetworkOut]],
    summary="Lista redes com busca, filtros, ordenação e paginação",
)
def list_it_networks(
    request: Request,
    q: str | None = Query(default=None, max_length=120, description="Nome, CIDR, zona ou local"),
    unit_code: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    network_scope: str | None = Query(default=None),
    criticality: str | None = Query(default=None),
    archived: Literal["active", "archived", "all"] = Query(default="active"),
    sort: NetworkSortKey = Query(default="name"),
    direction: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    authorize(request, *READ)
    result = inventory.list_networks(
        NetworkQuery(
            q=q,
            unit_code=unit_code,
            environment=environment,
            network_scope=network_scope,
            criticality=criticality,
            archived=archived,
            sort=sort,
            direction=direction,
            page=page,
            page_size=page_size,
        )
    )
    return ok(result, operation_id="list_it_networks")


@router.post(
    "/networks",
    operation_id="create_it_network",
    response_model=Envelope[NetworkOut],
    status_code=201,
    summary="Cadastra uma rede (CIDR validado no backend; sem varredura)",
)
def create_it_network(
    request: Request,
    payload: NetworkInput,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    user = authorize_write(request, *WRITE)
    created = inventory.create_network(payload.model_dump(), actor_from(user))
    return ok(created, "Rede cadastrada.", 201, operation_id="create_it_network")


@router.get(
    "/networks/{network_id}",
    operation_id="get_it_network",
    response_model=Envelope[NetworkOut],
    summary="Detalhe da rede",
)
def get_it_network(
    request: Request,
    network_id: UUID,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    authorize(request, *READ)
    return ok(inventory.get_network(str(network_id)), operation_id="get_it_network")


@router.put(
    "/networks/{network_id}",
    operation_id="update_it_network",
    response_model=Envelope[NetworkOut],
    summary="Atualiza a rede (concorrência otimista por revision)",
)
def update_it_network(
    request: Request,
    network_id: UUID,
    payload: NetworkUpdateInput,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    user = authorize_write(request, *WRITE)
    data = payload.model_dump(exclude={"revision"})
    updated = inventory.update_network(str(network_id), data, payload.revision, actor_from(user))
    return ok(updated, "Rede atualizada.", operation_id="update_it_network")


@router.post(
    "/networks/{network_id}/archive",
    operation_id="archive_it_network",
    response_model=Envelope[NetworkOut],
    summary="Arquiva a rede (vínculos e histórico são preservados)",
)
def archive_it_network(
    request: Request,
    network_id: UUID,
    payload: RevisionInput,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    user = authorize_write(request, *WRITE)
    archived = inventory.archive_network(str(network_id), payload.revision, actor_from(user))
    return ok(archived, "Rede arquivada.", operation_id="archive_it_network")


@router.post(
    "/networks/{network_id}/restore",
    operation_id="restore_it_network",
    response_model=Envelope[NetworkOut],
    summary="Restaura uma rede arquivada",
)
def restore_it_network(
    request: Request,
    network_id: UUID,
    payload: RevisionInput,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    user = authorize_write(request, *WRITE)
    restored = inventory.restore_network(str(network_id), payload.revision, actor_from(user))
    return ok(restored, "Rede restaurada.", operation_id="restore_it_network")


@router.get(
    "/networks/{network_id}/history",
    operation_id="list_it_network_history",
    response_model=Envelope[list[HistoryEventOut]],
    summary="Trilha de auditoria da rede e dos vínculos dela",
)
def list_it_network_history(
    request: Request,
    network_id: UUID,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    authorize(request, *READ)
    return ok(inventory.list_history(str(network_id)), operation_id="list_it_network_history")


@router.get(
    "/networks/{network_id}/server-links",
    operation_id="list_it_network_server_links",
    response_model=Envelope[list[ServerNetworkLinkOut]],
    summary="Servidores conectados à rede",
)
def list_it_network_server_links(
    request: Request,
    network_id: UUID,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    authorize(request, *READ)
    return ok(
        inventory.list_network_servers(str(network_id)),
        operation_id="list_it_network_server_links",
    )


@router.get(
    "/servers/{server_id}/network-links",
    operation_id="list_it_server_network_links",
    response_model=Envelope[list[ServerNetworkLinkOut]],
    summary="Redes às quais o servidor está conectado",
)
def list_it_server_network_links(
    request: Request,
    server_id: UUID,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    authorize(request, *READ)
    return ok(
        inventory.list_server_networks(str(server_id)),
        operation_id="list_it_server_network_links",
    )


@router.post(
    "/server-network-links",
    operation_id="create_it_server_network_link",
    response_model=Envelope[ServerNetworkLinkOut],
    status_code=201,
    summary="Conecta um servidor existente a uma rede (IP opcional dentro do CIDR)",
)
def create_it_server_network_link(
    request: Request,
    payload: ServerNetworkLinkInput,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    user = authorize_write(request, *WRITE)
    link = inventory.link_server_to_network(payload.model_dump(), actor_from(user))
    return ok(link, "Vínculo registrado.", 201, operation_id="create_it_server_network_link")


@router.delete(
    "/server-network-links/{link_id}",
    operation_id="delete_it_server_network_link",
    response_model=Envelope[LinkRemovedOut],
    summary="Remove a conexão servidor ↔ rede (servidor e rede são preservados)",
)
def delete_it_server_network_link(
    request: Request,
    link_id: UUID,
    inventory: NetworkInventory = Depends(get_network_inventory),
):
    user = authorize_write(request, *WRITE)
    inventory.unlink_server_from_network(str(link_id), actor_from(user))
    return ok(
        {"id": str(link_id)}, "Vínculo removido.", operation_id="delete_it_server_network_link"
    )
