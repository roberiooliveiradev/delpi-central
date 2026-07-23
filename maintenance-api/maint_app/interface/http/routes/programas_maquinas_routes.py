from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from delpi_api_client import DelpiApiError

from maint_app.application.list_query import ListQuery
from maint_app.application.services.maintenance_submodule_catalog import (
    assert_submodule_manage,
    assert_submodule_view,
)
from maint_app.composition.maintenance_composer import build_programas_maquina_service
from maint_app.core.auth_actor import actor_nome_from_request, actor_sub_from_request
from maint_app.core.errors import format_api_error
from maint_app.core.responses import fail, ok
from maint_app.infrastructure.persistence.repositories.programas_maquina_repository import (
    ProgramasMaquinaProdutosRepository,
)
from maint_app.interface.http.filial_access_http import resolve_access_scope, resolve_user
from maint_app.interface.http.list_query_params import list_query_params

router = APIRouter(prefix="/maintenance/programas-maquinas", tags=["Programas de máquina"])

_SUBMODULE_ID = "programas-maquinas"


class ProdutoCreateBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    codigo_intermediario: str = Field(min_length=1, max_length=40)
    descricao_intermediario: str | None = Field(default=None, max_length=255)
    codigo_produto_acabado: str | None = Field(default=None, max_length=40)
    codigo_ct_corte: str | None = Field(default=None, max_length=40)
    nome_programa: str | None = Field(default=None, max_length=120)
    observacao: str | None = None
    ativo: bool = True


class ProdutoUpdateBody(BaseModel):
    filial: str = Field(min_length=2, max_length=2)
    nome_programa: str | None = Field(default=None, max_length=120)
    observacao: str | None = None
    ativo: bool | None = None
    codigo_produto_acabado: str | None = Field(default=None, max_length=40)
    codigo_ct_corte: str | None = Field(default=None, max_length=40)
    descricao_intermediario: str | None = Field(default=None, max_length=255)


@router.get("/ranking")
def get_ranking(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    data_inicial: Optional[str] = Query(None),
    data_final: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        data = build_programas_maquina_service().ranking(
            filial=filial,
            data_inicial=data_inicial,
            data_final=data_final,
            page=query.page,
            page_size=query.page_size,
            search=search,
        )
        return ok(data, message="Ranking de intermediários consultado.")
    except DelpiApiError as exc:
        return fail(exc.detail, status_code=exc.status_code)
    except Exception as exc:
        return fail(format_api_error(exc), status_code=500)


@router.get("/produtos")
def list_produtos(
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
    search: Optional[str] = Query(None),
    incluir_inativos: bool = Query(False),
    query: ListQuery = Depends(list_query_params),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)
    try:
        assert_submodule_view(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    items, total = ProgramasMaquinaProdutosRepository().list_paged(
        filial=filial,
        query=query,
        search=search,
        apenas_ativos=not incluir_inativos,
    )
    return ok({"items": items, "total": total}, message="Produtos cadastrados listados.")


@router.post("/produtos")
def create_produto(body: ProdutoCreateBody, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=body.filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    codigo = body.codigo_intermediario.strip()
    if not codigo:
        return fail("Código do intermediário é obrigatório.", 400)

    actor_sub = actor_sub_from_request(request)
    actor_nome = actor_nome_from_request(request)

    try:
        item = ProgramasMaquinaProdutosRepository().create(
            {
                "filial": body.filial,
                "codigo_intermediario": codigo,
                "descricao_intermediario": (body.descricao_intermediario or "").strip() or None,
                "codigo_produto_acabado": (body.codigo_produto_acabado or "").strip() or None,
                "codigo_ct_corte": (body.codigo_ct_corte or "").strip() or None,
                "nome_programa": (body.nome_programa or "").strip() or None,
                "observacao": body.observacao,
                "ativo": body.ativo,
                "usuario_sub": actor_sub,
                "usuario_ativacao_sub": actor_sub,
                "usuario_ativacao_nome": actor_nome,
            }
        )
    except Exception as exc:
        msg = str(exc).lower()
        if "unique" in msg or "duplicate" in msg:
            return fail("Produto já cadastrado para este programa nesta filial.", 409)
        return fail(format_api_error(exc), status_code=500)

    return ok(item, message="Produto cadastrado no programa.", status_code=201)


@router.patch("/produtos/{item_id}")
def update_produto(item_id: UUID, body: ProdutoUpdateBody, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=body.filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    item = ProgramasMaquinaProdutosRepository().update(
        str(item_id),
        filial=body.filial,
        nome_programa=body.nome_programa,
        observacao=body.observacao,
        ativo=body.ativo,
        codigo_produto_acabado=body.codigo_produto_acabado,
        codigo_ct_corte=body.codigo_ct_corte,
        descricao_intermediario=body.descricao_intermediario,
        usuario_ativacao_sub=actor_sub_from_request(request),
        usuario_ativacao_nome=actor_nome_from_request(request),
    )
    if not item:
        return fail("Produto não encontrado.", 404)
    return ok(item, message="Cadastro atualizado.")


@router.delete("/produtos/{item_id}")
def delete_produto(
    item_id: UUID,
    request: Request,
    filial: str = Query(..., min_length=2, max_length=2),
):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID, codigo_filial=filial, scope=scope)
    except PermissionError as exc:
        return fail(str(exc), 403)

    deleted = ProgramasMaquinaProdutosRepository().soft_delete(str(item_id), filial=filial)
    if not deleted:
        return fail("Produto não encontrado.", 404)
    return ok(None, message="Produto removido do cadastro.")
