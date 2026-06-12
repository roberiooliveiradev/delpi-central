from typing import Optional

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from delpi_api_client import DelpiApiError

from maint_app.application.services.filial_access_scope_service import FilialAccessScopeService
from maint_app.composition.maintenance_composer import build_reposicao_service
from maint_app.core.errors import format_api_error
from maint_app.core.responses import fail, ok
from maint_app.infrastructure.persistence.repositories.operational_repositories import (
    MotivoRepository,
    ReposicaoRepository,
    StatusPecaRepository,
)
from maint_app.interface.http.filial_access_http import resolve_access_scope, resolve_user

router = APIRouter(prefix="/maintenance", tags=["Manutenção — operacional"])

_scope = FilialAccessScopeService()


class MotivoCreateBody(BaseModel):
    descricao: str = Field(min_length=1, max_length=120)


class MotivoUpdateBody(BaseModel):
    descricao: str = Field(min_length=1, max_length=120)


class StatusUpdateBody(BaseModel):
    descricao: Optional[str] = Field(default=None, max_length=60)
    operador: Optional[str] = Field(default=None, pattern="^(>=|<=|>|<)$")
    percentual: Optional[int] = Field(default=None, ge=0, le=200)


class ReposicaoBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    codigo_ferramenta: str = Field(min_length=1, max_length=40)
    codigo_peca: str = Field(min_length=1, max_length=40)
    data_reposicao: str
    golpes: int = Field(gt=0)
    motivo_id: int
    observacao: Optional[str] = None


@router.get("/motivos")
def list_motivos(request: Request):
    items = MotivoRepository().list_active()
    return ok({"items": items, "total": len(items)}, message="Motivos listados.")


@router.post("/motivos")
def create_motivo(body: MotivoCreateBody, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    if not _scope.can_manage_filial(scope, "01", user=user) and not _scope.can_manage_filial(
        scope, "02", user=user
    ):
        return fail("Sem permissão para gerenciar motivos.", 403)
    item = MotivoRepository().create(body.descricao)
    return ok(item, message="Motivo criado.", status_code=201)


@router.put("/motivos/{motivo_id}")
def update_motivo(motivo_id: int, body: MotivoUpdateBody, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    if not _scope.can_manage_filial(scope, "01", user=user) and not _scope.can_manage_filial(
        scope, "02", user=user
    ):
        return fail("Sem permissão para gerenciar motivos.", 403)
    item = MotivoRepository().update(motivo_id, body.descricao)
    if not item:
        return fail("Motivo não encontrado.", 404)
    return ok(item, message="Motivo atualizado.")


@router.delete("/motivos/{motivo_id}")
def delete_motivo(motivo_id: int, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    if not _scope.can_manage_filial(scope, "01", user=user) and not _scope.can_manage_filial(
        scope, "02", user=user
    ):
        return fail("Sem permissão para gerenciar motivos.", 403)
    MotivoRepository().soft_delete(motivo_id)
    return ok(None, message="Motivo excluído.")


@router.get("/status-peca")
def list_status_peca(request: Request):
    items = StatusPecaRepository().list_active()
    return ok({"items": items, "total": len(items)}, message="Status listados.")


@router.put("/status-peca/{status_id}")
def update_status_peca(status_id: int, body: StatusUpdateBody, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    if not _scope.can_manage_filial(scope, "01", user=user) and not _scope.can_manage_filial(
        scope, "02", user=user
    ):
        return fail("Sem permissão para gerenciar status.", 403)
    item = StatusPecaRepository().update(
        status_id,
        descricao=body.descricao,
        operador=body.operador,
        percentual=body.percentual,
    )
    if not item:
        return fail("Status não encontrado.", 404)
    return ok(item, message="Status atualizado.")


@router.get("/reposicoes")
def list_reposicoes(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    codigo_ferramenta: str = Query(...),
    codigo_peca: Optional[str] = Query(None),
):
    scope = resolve_access_scope(request)
    try:
        _scope.assert_view_filial(scope, filial)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items = ReposicaoRepository().list_by_ferramenta(
        filial=filial,
        codigo_ferramenta=codigo_ferramenta,
        codigo_peca=codigo_peca,
    )
    return ok({"items": items, "total": len(items)}, message="Reposições listadas.")


@router.post("/reposicoes")
def create_reposicao(body: ReposicaoBody, request: Request):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    service = build_reposicao_service()
    try:
        item = service.create(body.model_dump(), scope=scope, user=user)
        return ok(item, message="Reposição registrada.", status_code=201)
    except PermissionError as exc:
        return fail(str(exc), 403)
    except ValueError as exc:
        return fail(str(exc), 422)


@router.put("/reposicoes/{reposicao_id}")
def update_reposicao(reposicao_id: str, body: ReposicaoBody, request: Request):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    service = build_reposicao_service()
    try:
        item = service.update(reposicao_id, body.model_dump(), scope=scope, user=user)
        if not item:
            return fail("Reposição não encontrada.", 404)
        return ok(item, message="Reposição atualizada.")
    except PermissionError as exc:
        return fail(str(exc), 403)
    except ValueError as exc:
        return fail(str(exc), 422)


@router.delete("/reposicoes/{reposicao_id}")
def delete_reposicao(reposicao_id: str, request: Request):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    service = build_reposicao_service()
    try:
        deleted = service.delete(reposicao_id, scope=scope, user=user)
        if not deleted:
            return fail("Reposição não encontrada.", 404)
        return ok(None, message="Reposição excluída.")
    except PermissionError as exc:
        return fail(str(exc), 403)


@router.get("/mini-aplicadores/sugerir-golpes")
def sugerir_golpes(
    filial: str = Query(..., min_length=2, max_length=2),
    codigo_ferramenta: str = Query(...),
    codigo_peca: str = Query(...),
):
    service = build_reposicao_service()
    try:
        total = service.sugerir_golpes(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            codigo_peca=codigo_peca,
        )
        return ok(
            {
                "filial": filial,
                "codigo_ferramenta": codigo_ferramenta,
                "codigo_peca": codigo_peca,
                "total_golpes": total,
            },
            message="Golpes sugeridos.",
        )
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)
