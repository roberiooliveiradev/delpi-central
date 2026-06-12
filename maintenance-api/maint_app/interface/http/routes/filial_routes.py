from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from maint_app.application.services.filial_access_scope_service import FilialAccessScopeService
from maint_app.application.services.maintenance_submodule_catalog import assert_submodule_manage
from maint_app.core.responses import fail, ok
from maint_app.infrastructure.persistence.repositories.filial_repository import FilialRepository
from maint_app.interface.http.filial_access_http import resolve_access_scope, resolve_user

router = APIRouter(prefix="/maintenance", tags=["Manutenção — filiais"])

_scope = FilialAccessScopeService()
_SUBMODULE_ID = "mini-aplicadores"


class FilialCreateBody(BaseModel):
    codigo_filial: str = Field(min_length=1, max_length=2)
    nome_filial: str = Field(min_length=1, max_length=120)
    status_filial: str = Field(default="ativo", pattern="^(ativo|inativo)$")


class FilialUpdateBody(BaseModel):
    nome_filial: str = Field(min_length=1, max_length=120)
    status_filial: str = Field(default="ativo", pattern="^(ativo|inativo)$")


def _serialize(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "filial_id": row["filial_id"],
        "codigo_filial": row["codigo_filial"],
        "nome_filial": row["nome_filial"],
        "status_filial": row["status_filial"],
        "data_criacao": row["data_criacao"].isoformat() if row.get("data_criacao") else None,
        "data_alteracao": row["data_alteracao"].isoformat() if row.get("data_alteracao") else None,
    }


@router.get("/filiais")
def list_filiais(
    request: Request,
    include_inactive: bool = Query(default=False),
    admin: bool = Query(default=False),
):
    scope = resolve_access_scope(request)
    user = resolve_user(request)

    if admin:
        try:
            assert_submodule_manage(user, _SUBMODULE_ID)
        except PermissionError as exc:
            return fail(str(exc), 403)
        rows = FilialRepository().list(include_inactive=include_inactive)
        items = [_serialize(row) for row in rows]
        return ok({"items": items, "total": len(items)}, message="Filiais listadas.")

    rows = FilialRepository().list(include_inactive=False)
    options = _scope.filter_filiais_options(
        [{"id": row["codigo_filial"], "label": row["nome_filial"]} for row in rows],
        scope,
    )
    return ok({"items": options, "total": len(options)}, message="Filiais listadas.")


@router.get("/filiais/{filial_ref}")
def get_filial(filial_ref: str, request: Request):
    user = resolve_user(request)
    scope = resolve_access_scope(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID)
    except PermissionError as exc:
        return fail(str(exc), 403)

    row = FilialRepository().get(filial_ref)
    if not row:
        return fail("Filial não encontrada.", 404)
    return ok(_serialize(row), message="Filial carregada.")


@router.post("/filiais")
def create_filial(body: FilialCreateBody, request: Request):
    user = resolve_user(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        row = FilialRepository().create(body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 422)

    return ok(_serialize(row), message="Filial criada.", status_code=201)


@router.put("/filiais/{filial_ref}")
def update_filial(filial_ref: str, body: FilialUpdateBody, request: Request):
    user = resolve_user(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID)
    except PermissionError as exc:
        return fail(str(exc), 403)

    try:
        row = FilialRepository().update(filial_ref, body.model_dump())
    except ValueError as exc:
        return fail(str(exc), 422)

    if not row:
        return fail("Filial não encontrada.", 404)
    return ok(_serialize(row), message="Filial atualizada.")


@router.delete("/filiais/{filial_ref}")
def delete_filial(filial_ref: str, request: Request):
    user = resolve_user(request)
    try:
        assert_submodule_manage(user, _SUBMODULE_ID)
    except PermissionError as exc:
        return fail(str(exc), 403)

    existing = FilialRepository().get(filial_ref)
    if not existing:
        return fail("Filial não encontrada.", 404)

    try:
        if not FilialRepository().soft_delete(filial_ref):
            return fail("Filial não encontrada.", 404)
    except ValueError as exc:
        return fail(str(exc), 422)

    return ok(None, message="Filial excluída.")
