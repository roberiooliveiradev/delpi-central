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
from maint_app.composition.maintenance_composer import (
    build_mini_applicators_totvs_gateway,
    build_reposicao_service,
    build_revisao_programada_service,
)
from maint_app.core.errors import format_api_error
from maint_app.core.responses import fail, ok
from maint_app.infrastructure.persistence.repositories.operational_repositories import (
    MotivoRepository,
    ReposicaoRepository,
    RevisaoProgramadaRealizacaoRepository,
    RevisaoProgramadaRepository,
    StatusPecaRepository,
)
from maint_app.interface.http.audit_http import log_ferramenta_audit
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


class RevisaoProgramadaRealizacaoUpdateBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    data_revisao: Optional[str] = None
    observacao: Optional[str] = None


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


@router.get("/revisoes-programadas/realizacoes")
def list_revisao_programada_realizacoes(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    codigo_ferramenta: str = Query(..., min_length=1, max_length=40),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    items, total = build_revisao_programada_service().listar_realizacoes(
        filial=filial,
        codigo_ferramenta=codigo_ferramenta,
        query=query,
    )
    return ok({"items": items, "total": total}, message="Revisões realizadas listadas.")


@router.put("/revisoes-programadas/realizacoes/{realizacao_id}")
def update_revisao_programada_realizacao(
    realizacao_id: str,
    body: RevisaoProgramadaRealizacaoUpdateBody,
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
        item = service.atualizar_realizacao(realizacao_id, filial=body.filial, payload=payload)
        if not item:
            return fail("Marcação de revisão não encontrada.", 404)
        log_ferramenta_audit(
            request,
            acao="revisao_realizacao.update",
            filial=body.filial,
            codigo_ferramenta=str(item["codigo_ferramenta"]),
            payload={
                "realizacao_id": realizacao_id,
                "revisao_id": str(item.get("revisao_id") or ""),
                "data_revisao": item.get("data_revisao"),
                "observacao": item.get("observacao"),
            },
        )
        return ok(item, message="Marcação de revisão atualizada.")
    except ValueError as exc:
        return fail(str(exc), 422)


@router.delete("/revisoes-programadas/realizacoes/{realizacao_id}")
def delete_revisao_programada_realizacao(
    realizacao_id: str,
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    realizacao_repo = RevisaoProgramadaRealizacaoRepository()
    existing = realizacao_repo.get_by_id(realizacao_id, filial=filial)
    deleted = build_revisao_programada_service().remover_realizacao(realizacao_id, filial=filial)
    if not deleted:
        return fail("Marcação de revisão não encontrada.", 404)
    if existing:
        log_ferramenta_audit(
            request,
            acao="revisao_realizacao.delete",
            filial=filial,
            codigo_ferramenta=str(existing["codigo_ferramenta"]),
            payload={
                "realizacao_id": realizacao_id,
                "revisao_id": str(existing.get("revisao_id") or ""),
                "data_revisao": existing.get("data_revisao"),
            },
        )
    return ok(None, message="Marcação de revisão removida.")


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
        log_ferramenta_audit(
            request,
            acao="revisao_programada.create",
            filial=body.filial,
            codigo_ferramenta=str(item["codigo_ferramenta"]),
            payload={
                "revisao_id": str(item.get("revisao_id") or ""),
                "intervalo_meses": item.get("intervalo_meses"),
                "data_ultima_revisao": item.get("data_ultima_revisao"),
                "observacao": item.get("observacao"),
            },
        )
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
        log_ferramenta_audit(
            request,
            acao="revisao_programada.update",
            filial=body.filial,
            codigo_ferramenta=str(item["codigo_ferramenta"]),
            payload={
                "revisao_id": revisao_id,
                "intervalo_meses": item.get("intervalo_meses"),
                "data_ultima_revisao": item.get("data_ultima_revisao"),
                "observacao": item.get("observacao"),
            },
        )
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

    revisao_repo = RevisaoProgramadaRepository()
    existing = revisao_repo.get_by_id(revisao_id, filial=filial)
    build_revisao_programada_service().delete(revisao_id, filial=filial)
    if existing:
        log_ferramenta_audit(
            request,
            acao="revisao_programada.delete",
            filial=filial,
            codigo_ferramenta=str(existing["codigo_ferramenta"]),
            payload={"revisao_id": revisao_id},
        )
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
    log_ferramenta_audit(
        request,
        acao="revisao_programada.registrar",
        filial=filial,
        codigo_ferramenta=str(item["codigo_ferramenta"]),
        payload={
            "revisao_id": revisao_id,
            "data_ultima_revisao": item.get("data_ultima_revisao"),
            "data_revisao": body.data_revisao if body else None,
        },
    )
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
        log_ferramenta_audit(
            request,
            acao="reposicao.create",
            filial=body.filial,
            codigo_ferramenta=body.codigo_ferramenta,
            payload={
                "reposicao_id": str(item.get("reposicao_id") or ""),
                "codigo_peca": body.codigo_peca,
                "golpes": body.golpes,
                "data_reposicao": body.data_reposicao,
                "motivo_id": body.motivo_id,
            },
        )
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
        log_ferramenta_audit(
            request,
            acao="reposicao.update",
            filial=body.filial,
            codigo_ferramenta=body.codigo_ferramenta,
            payload={
                "reposicao_id": reposicao_id,
                "codigo_peca": body.codigo_peca,
                "golpes": body.golpes,
                "data_reposicao": body.data_reposicao,
                "motivo_id": body.motivo_id,
            },
        )
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
        existing = ReposicaoRepository().get_by_id(reposicao_id)
        deleted = service.delete(reposicao_id, scope=scope, user=user)
        if not deleted:
            return fail("Reposição não encontrada.", 404)
        if existing:
            log_ferramenta_audit(
                request,
                acao="reposicao.delete",
                filial=str(existing["filial"]),
                codigo_ferramenta=str(existing["codigo_ferramenta"]),
                payload={
                    "reposicao_id": reposicao_id,
                    "codigo_peca": existing.get("codigo_peca"),
                    "golpes": existing.get("golpes"),
                    "data_reposicao": existing.get("data_reposicao"),
                },
            )
        return ok(None, message="Reposição excluída.")
    except PermissionError as exc:
        return fail(str(exc), 403)


@router.get("/mini-aplicadores/catalogo-pecas-3019")
def list_catalogo_pecas_3019(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    codigo: Optional[str] = Query(None),
    descricao: Optional[str] = Query(None),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        gateway = build_mini_applicators_totvs_gateway()
        data = gateway.listar_pecas_reposicao(
            codigo=codigo,
            descricao=descricao,
            page=query.page,
            page_size=query.page_size,
            sort_by=query.sort_by,
            sort_dir=query.sort_dir,
        )
        return ok(data, message="Peças de reposição listadas.")
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)


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
