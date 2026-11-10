"""Rotas de servidores, notas técnicas e histórico."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request

from it_portal_app.application.ports import ServerQuery
from it_portal_app.application.server_service import ServerService
from it_portal_app.core.responses import ok
from it_portal_app.interface.http.authz import (
    NOTES_CREATE,
    SERVERS_MANAGE,
    SERVERS_VIEW,
    actor_from,
    authorize,
)
from it_portal_app.interface.http.dependencies import get_server_service
from it_portal_app.interface.http.schemas import (
    ERROR_RESPONSES,
    Envelope,
    HistoryEventOut,
    NoteInput,
    NoteOut,
    PageOut,
    RevisionInput,
    ServerInput,
    ServerOut,
    ServerUpdateInput,
)

router = APIRouter(prefix="/servers", tags=["Servers"], responses=ERROR_RESPONSES)

ServerSortKey = Literal["name", "hostname", "criticality", "environment", "created_at", "updated_at"]


@router.get(
    "",
    operation_id="list_it_servers",
    response_model=Envelope[PageOut[ServerOut]],
    summary="Lista servidores com busca, filtros, ordenação e paginação",
)
def list_it_servers(
    request: Request,
    q: str | None = Query(default=None, max_length=120, description="Nome, hostname ou IP"),
    unit_code: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    criticality: str | None = Query(default=None),
    archived: Literal["active", "archived", "all"] = Query(default="active"),
    sort: ServerSortKey = Query(default="name"),
    direction: Literal["asc", "desc"] = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    service: ServerService = Depends(get_server_service),
):
    authorize(request, SERVERS_VIEW)
    result = service.list_servers(
        ServerQuery(
            q=q,
            unit_code=unit_code,
            environment=environment,
            criticality=criticality,
            archived=archived,
            sort=sort,
            direction=direction,
            page=page,
            page_size=page_size,
        )
    )
    return ok(result, operation_id="list_it_servers")


@router.post(
    "",
    operation_id="create_it_server",
    response_model=Envelope[ServerOut],
    status_code=201,
    summary="Cadastra um servidor",
)
def create_it_server(
    request: Request,
    payload: ServerInput,
    service: ServerService = Depends(get_server_service),
):
    user = authorize(request, SERVERS_MANAGE)
    created = service.create_server(payload.model_dump(), actor_from(user))
    return ok(created, "Servidor cadastrado.", 201, operation_id="create_it_server")


@router.get(
    "/{server_id}",
    operation_id="get_it_server",
    response_model=Envelope[ServerOut],
    summary="Detalhe do servidor",
)
def get_it_server(
    request: Request,
    server_id: UUID,
    service: ServerService = Depends(get_server_service),
):
    authorize(request, SERVERS_VIEW)
    return ok(service.get_server(str(server_id)), operation_id="get_it_server")


@router.put(
    "/{server_id}",
    operation_id="update_it_server",
    response_model=Envelope[ServerOut],
    summary="Atualiza o cadastro do servidor (concorrência otimista por revision)",
)
def update_it_server(
    request: Request,
    server_id: UUID,
    payload: ServerUpdateInput,
    service: ServerService = Depends(get_server_service),
):
    user = authorize(request, SERVERS_MANAGE)
    data = payload.model_dump(exclude={"revision"})
    updated = service.update_server(
        str(server_id), data, payload.revision, actor_from(user)
    )
    return ok(updated, "Servidor atualizado.", operation_id="update_it_server")


@router.post(
    "/{server_id}/archive",
    operation_id="archive_it_server",
    response_model=Envelope[ServerOut],
    summary="Arquiva o servidor (sem exclusão física)",
)
def archive_it_server(
    request: Request,
    server_id: UUID,
    payload: RevisionInput,
    service: ServerService = Depends(get_server_service),
):
    user = authorize(request, SERVERS_MANAGE)
    archived = service.archive_server(str(server_id), payload.revision, actor_from(user))
    return ok(archived, "Servidor arquivado.", operation_id="archive_it_server")


@router.post(
    "/{server_id}/restore",
    operation_id="restore_it_server",
    response_model=Envelope[ServerOut],
    summary="Restaura um servidor arquivado",
)
def restore_it_server(
    request: Request,
    server_id: UUID,
    payload: RevisionInput,
    service: ServerService = Depends(get_server_service),
):
    user = authorize(request, SERVERS_MANAGE)
    restored = service.restore_server(str(server_id), payload.revision, actor_from(user))
    return ok(restored, "Servidor restaurado.", operation_id="restore_it_server")


@router.get(
    "/{server_id}/notes",
    operation_id="list_it_server_notes",
    response_model=Envelope[list[NoteOut]],
    summary="Notas técnicas do servidor em ordem cronológica",
)
def list_it_server_notes(
    request: Request,
    server_id: UUID,
    service: ServerService = Depends(get_server_service),
):
    authorize(request, SERVERS_VIEW)
    return ok(service.list_notes(str(server_id)), operation_id="list_it_server_notes")


@router.post(
    "/{server_id}/notes",
    operation_id="create_it_server_note",
    response_model=Envelope[NoteOut],
    status_code=201,
    summary="Adiciona uma nota técnica (somente inclusão; nunca registre segredos)",
)
def create_it_server_note(
    request: Request,
    server_id: UUID,
    payload: NoteInput,
    service: ServerService = Depends(get_server_service),
):
    user = authorize(request, SERVERS_VIEW, NOTES_CREATE)
    note = service.add_note(str(server_id), payload.body, actor_from(user))
    return ok(note, "Nota registrada.", 201, operation_id="create_it_server_note")


@router.get(
    "/{server_id}/history",
    operation_id="list_it_server_history",
    response_model=Envelope[list[HistoryEventOut]],
    summary="Trilha de auditoria do servidor (eventos mais recentes primeiro)",
)
def list_it_server_history(
    request: Request,
    server_id: UUID,
    service: ServerService = Depends(get_server_service),
):
    authorize(request, SERVERS_VIEW)
    return ok(service.list_history(str(server_id)), operation_id="list_it_server_history")
