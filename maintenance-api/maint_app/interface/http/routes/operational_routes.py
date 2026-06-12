from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from delpi_api_client import DelpiApiError

from maint_app.application.list_query import ListQuery
from maint_app.application.services.filial_access_scope_service import FilialAccessScopeService
from maint_app.application.services.maintenance_submodule_catalog import (
    assert_submodule_manage,
    assert_submodule_view,
)
from maint_app.composition.maintenance_composer import build_reposicao_service, build_revisao_programada_service
from maint_app.core.errors import format_api_error
from maint_app.core.responses import fail, ok
from maint_app.infrastructure.persistence.repositories.operational_repositories import (
    MotivoRepository,
    ReposicaoRepository,
    StatusPecaRepository,
)
from maint_app.interface.http.filial_access_http import resolve_access_scope, resolve_user
from maint_app.interface.http.list_query_params import list_query_params

router = APIRouter(prefix="/maintenance", tags=["Manutenção — operacional"])

_scope = FilialAccessScopeService()
_SUBMODULE_ID = "mini-aplicadores"


class MotivoCreateBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    descricao: str = Field(min_length=1, max_length=120)
    excluir_preventiva: bool = False


class MotivoUpdateBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    descricao: str = Field(min_length=1, max_length=120)
    excluir_preventiva: bool | None = None


class StatusUpdateBody(BaseModel):
    descricao: Optional[str] = Field(default=None, max_length=60)
    operador: Optional[str] = Field(default=None, pattern="^(>=|<=|>|<)$")
    percentual: Optional[int] = Field(default=None, ge=0, le=200)


class StatusCreateBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    descricao: str = Field(min_length=1, max_length=60)
    operador: str = Field(pattern="^(>=|<=|>|<)$")
    percentual: int = Field(ge=0, le=200)


class ReposicaoBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    codigo_ferramenta: str = Field(min_length=1, max_length=40)
    codigo_peca: str = Field(min_length=1, max_length=40)
    data_reposicao: str
    data_ultima_reposicao: Optional[str] = None
    golpes: int = Field(gt=0)
    motivo_id: str
    observacao: Optional[str] = None


class RevisaoProgramadaCreateBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    codigo_ferramenta: str = Field(min_length=1, max_length=40)
    intervalo_meses: int = Field(ge=1, le=120)
    observacao: Optional[str] = None
    data_ultima_revisao: Optional[str] = None


class RevisaoProgramadaUpdateBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    intervalo_meses: Optional[int] = Field(default=None, ge=1, le=120)
    observacao: Optional[str] = None
    data_ultima_revisao: Optional[str] = None


class RevisaoProgramadaRegistrarBody(BaseModel):
    data_revisao: Optional[str] = None


@router.get("/motivos")
def list_motivos(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    search: Optional[str] = Query(None),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items, total = MotivoRepository().list_active_paged(
        filial=filial,
        query=query,
        search=search,
    )
    return ok({"items": items, "total": total}, message="Motivos listados.")


@router.post("/motivos")
def create_motivo(body: MotivoCreateBody, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=body.filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)
    item = MotivoRepository().create(
        body.descricao,
        filial=body.filial,
        excluir_preventiva=body.excluir_preventiva,
    )
    return ok(item, message="Motivo criado.", status_code=201)


@router.put("/motivos/{motivo_id}")
def update_motivo(motivo_id: str, body: MotivoUpdateBody, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=body.filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)
    item = MotivoRepository().update(
        motivo_id,
        filial=body.filial,
        descricao=body.descricao,
        excluir_preventiva=body.excluir_preventiva,
    )
    if not item:
        return fail("Motivo não encontrado.", 404)
    return ok(item, message="Motivo atualizado.")


@router.delete("/motivos/{motivo_id}")
def delete_motivo(
    motivo_id: str,
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)
    MotivoRepository().soft_delete(motivo_id, filial=filial)
    return ok(None, message="Motivo excluído.")


@router.get("/status-peca")
def list_status_peca(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    search: Optional[str] = Query(None),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items, total = StatusPecaRepository().list_active_paged(
        filial=filial,
        query=query,
        search=search,
    )
    return ok({"items": items, "total": total}, message="Status listados.")


@router.post("/status-peca")
def create_status_peca(body: StatusCreateBody, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=body.filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)
    item = StatusPecaRepository().create(
        filial=body.filial,
        descricao=body.descricao,
        operador=body.operador,
        percentual=body.percentual,
    )
    return ok(item, message="Status criado.", status_code=201)


@router.put("/status-peca/{status_id}")
def update_status_peca(
    status_id: str,
    body: StatusUpdateBody,
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)
    item = StatusPecaRepository().update(
        status_id,
        filial=filial,
        descricao=body.descricao,
        operador=body.operador,
        percentual=body.percentual,
    )
    if not item:
        return fail("Status não encontrado.", 404)
    return ok(item, message="Status atualizado.")


@router.delete("/status-peca/{status_id}")
def delete_status_peca(
    status_id: str,
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)
    StatusPecaRepository().soft_delete(status_id, filial=filial)
    return ok(None, message="Status excluído.")


@router.get("/revisoes-programadas")
def list_revisoes_programadas(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    search: Optional[str] = Query(None),
    codigo_ferramenta: Optional[str] = Query(None),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    service = build_revisao_programada_service()
    items, total = service.listar_programacoes(
        filial=filial,
        query=query,
        search=search,
        codigo_ferramenta=codigo_ferramenta,
    )
    return ok({"items": items, "total": total}, message="Revisões programadas listadas.")


@router.post("/revisoes-programadas")
def create_revisao_programada(body: RevisaoProgramadaCreateBody, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=body.filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    service = build_revisao_programada_service()
    try:
        item = service.create(body.model_dump())
        return ok(item, message="Revisão programada criada.", status_code=201)
    except ValueError as exc:
        return fail(str(exc), 422)


@router.put("/revisoes-programadas/{revisao_id}")
def update_revisao_programada(
    revisao_id: str,
    body: RevisaoProgramadaUpdateBody,
    request: Request,
):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=body.filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    service = build_revisao_programada_service()
    try:
        payload = body.model_dump(exclude_unset=True)
        payload["filial"] = body.filial
        item = service.update(revisao_id, filial=body.filial, payload=payload)
        if not item:
            return fail("Revisão programada não encontrada.", 404)
        return ok(item, message="Revisão programada atualizada.")
    except ValueError as exc:
        return fail(str(exc), 422)


@router.delete("/revisoes-programadas/{revisao_id}")
def delete_revisao_programada(
    revisao_id: str,
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    build_revisao_programada_service().delete(revisao_id, filial=filial)
    return ok(None, message="Revisão programada excluída.")


@router.post("/revisoes-programadas/{revisao_id}/registrar")
def registrar_revisao_programada(
    revisao_id: str,
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    body: RevisaoProgramadaRegistrarBody | None = None,
):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    item = build_revisao_programada_service().registrar_revisao(
        revisao_id,
        filial=filial,
        data_revisao=body.data_revisao if body else None,
    )
    if not item:
        return fail("Revisão programada não encontrada.", 404)
    return ok(item, message="Revisão registrada.")


@router.get("/reposicoes")
def list_reposicoes(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    codigo_ferramenta: str = Query(...),
    codigo_peca: list[str] | None = Query(None),
    motivo_id: list[str] | None = Query(None),
    data_inicial: Optional[str] = Query(None),
    data_final: Optional[str] = Query(None),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)
    items, total = ReposicaoRepository().list_by_ferramenta_paged(
        filial=filial,
        codigo_ferramenta=codigo_ferramenta,
        codigo_peca=codigo_peca,
        motivo_ids=motivo_id,
        data_inicial=data_inicial,
        data_final=data_final,
        query=query,
    )
    return ok({"items": items, "total": total}, message="Reposições listadas.")


@router.post("/reposicoes")
def create_reposicao(body: ReposicaoBody, request: Request):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    service = build_reposicao_service()
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=body.filial, scope=scope)
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
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=body.filial, scope=scope)
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
        assert_submodule_manage(user, _SUBMODULE_ID)
        deleted = service.delete(reposicao_id, scope=scope, user=user)
        if not deleted:
            return fail("Reposição não encontrada.", 404)
        return ok(None, message="Reposição excluída.")
    except PermissionError as exc:
        return fail(str(exc), 403)


@router.get("/mini-aplicadores/sugerir-golpes")
def sugerir_golpes(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    codigo_ferramenta: str = Query(...),
    codigo_peca: str = Query(...),
    data_inicial: Optional[str] = Query(None),
    data_final: Optional[str] = Query(None),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    service = build_reposicao_service()
    try:
        payload = service.sugerir_golpes(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            codigo_peca=codigo_peca,
            data_inicial=data_inicial,
            data_final=data_final,
        )
        return ok(
            {
                "filial": filial,
                "codigo_ferramenta": codigo_ferramenta,
                "codigo_peca": codigo_peca,
                **payload,
            },
            message="Golpes sugeridos.",
        )
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)
