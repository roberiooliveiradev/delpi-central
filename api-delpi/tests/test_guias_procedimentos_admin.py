"""Testes administrativos — Guias e Procedimentos."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.application.security import api_delpi_permissions as perms
from app.application.services.guias_procedimentos.guide_html_sanitizer import (
    GuideHtmlSanitizer,
)
from app.application.use_cases.guias_procedimentos.admin_guias_use_cases import (
    ActorContext,
    ArchiveProcedureUseCase,
    CreateDepartmentUseCase,
    CreateProcedureUseCase,
    GetAdminDepartmentUseCase,
    ListAdminDepartmentsUseCase,
    PublishProcedureUseCase,
    UnpublishProcedureUseCase,
    UpdateDepartmentUseCase,
    UpdateProcedureUseCase,
)
from app.application.use_cases.guias_procedimentos.public_guias_use_cases import (
    GetGuiasProcedureBySlugUseCase,
)
from app.domain.services.guias_procedimentos.exceptions import (
    GuiasConflictError,
    GuiasNotFoundError,
    GuiasValidationError,
)
from app.domain.services.guias_procedimentos.guide_validators import validate_slug
from app.interface.http.routes.guias_procedimentos import (
    guias_procedimentos_admin_router,
    guias_procedimentos_router,
)


DEP_ID = "22222222-2222-4222-8222-222222222201"
PROC_ID = "22222222-2222-4222-8222-222222222202"
ACTOR = ActorContext("user-1", "Admin Teste")


class AdminProbeRepo:
    def __init__(self) -> None:
        self.departments: dict[str, dict[str, Any]] = {}
        self.procedures: dict[str, dict[str, Any]] = {}
        self.slug_depts: set[str] = set()
        self.slug_procs: set[str] = set()

    def list_admin_departments(self) -> list[dict[str, Any]]:
        rows = list(self.departments.values())
        return sorted(rows, key=lambda r: (r["order_index"], r["name"]))

    def get_department_by_id(self, department_id: str) -> dict[str, Any] | None:
        return self.departments.get(department_id)

    def create_department(self, **fields: Any) -> dict[str, Any]:
        if fields["slug"] in self.slug_depts:
            raise GuiasConflictError("Já existe um departamento com este slug.")
        dept_id = str(uuid4())
        row = {
            "id": dept_id,
            **fields,
            "procedure_count": 0,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        self.departments[dept_id] = row
        self.slug_depts.add(fields["slug"])
        return row

    def update_department(self, department_id: str, **fields: Any) -> dict[str, Any]:
        existing = self.departments.get(department_id)
        if existing is None:
            raise GuiasNotFoundError("Departamento não encontrado.")
        if fields["slug"] != existing["slug"] and fields["slug"] in self.slug_depts:
            raise GuiasConflictError("Já existe um departamento com este slug.")
        self.slug_depts.discard(existing["slug"])
        self.slug_depts.add(fields["slug"])
        existing.update(fields)
        existing["updated_at"] = datetime.now(timezone.utc)
        return existing

    def list_admin_procedures(self, **filters: Any) -> list[dict[str, Any]]:
        rows = list(self.procedures.values())
        if filters.get("department_id"):
            rows = [r for r in rows if str(r["department_id"]) == filters["department_id"]]
        if filters.get("status"):
            rows = [r for r in rows if r["status"] == filters["status"]]
        if filters.get("q"):
            q = filters["q"].lower()
            rows = [
                r
                for r in rows
                if q in r["title"].lower() or q in r["slug"].lower()
            ]
        return rows

    def get_admin_procedure_by_id(self, procedure_id: str) -> dict[str, Any] | None:
        return self.procedures.get(procedure_id)

    def create_procedure(self, **fields: Any) -> dict[str, Any]:
        if fields["slug"] in self.slug_procs:
            raise GuiasConflictError("Já existe um procedimento com este slug.")
        dept = self.departments.get(str(fields["department_id"]))
        if dept is None:
            raise GuiasValidationError("department_id inexistente.")
        proc_id = str(uuid4())
        row = {
            "id": proc_id,
            "status": "draft",
            "published_at": None,
            "archived_at": None,
            "published_by_user_id": None,
            "published_by_name": None,
            "archived_by_user_id": None,
            "archived_by_name": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "department_id": dept["id"],
            "department_name": dept["name"],
            "department_slug": dept["slug"],
            "department_icon": dept["icon"],
            "department_active": dept["active"],
            **{k: v for k, v in fields.items() if k != "department_id"},
        }
        self.procedures[proc_id] = row
        self.slug_procs.add(fields["slug"])
        dept["procedure_count"] = dept.get("procedure_count", 0) + 1
        return row

    def update_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]:
        existing = self.procedures.get(procedure_id)
        if existing is None:
            raise GuiasNotFoundError("Procedimento não encontrado.")
        if fields["slug"] != existing["slug"] and fields["slug"] in self.slug_procs:
            raise GuiasConflictError("Já existe um procedimento com este slug.")
        dept = self.departments.get(str(fields["department_id"]))
        if dept is None:
            raise GuiasValidationError("department_id inexistente.")
        self.slug_procs.discard(existing["slug"])
        self.slug_procs.add(fields["slug"])
        existing.update(fields)
        existing["department_id"] = dept["id"]
        existing["department_name"] = dept["name"]
        existing["department_slug"] = dept["slug"]
        existing["department_icon"] = dept["icon"]
        existing["department_active"] = dept["active"]
        existing["updated_at"] = datetime.now(timezone.utc)
        return existing

    def publish_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]:
        existing = self.procedures[procedure_id]
        existing["status"] = "published"
        existing["content_html"] = fields["content_html"]
        existing["published_at"] = datetime.now(timezone.utc)
        existing["published_by_user_id"] = fields["published_by_user_id"]
        existing["published_by_name"] = fields["published_by_name"]
        existing["archived_at"] = None
        existing["updated_by_user_id"] = fields["updated_by_user_id"]
        existing["updated_by_name"] = fields["updated_by_name"]
        return existing

    def unpublish_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]:
        existing = self.procedures[procedure_id]
        existing["status"] = "draft"
        existing["updated_by_user_id"] = fields["updated_by_user_id"]
        existing["updated_by_name"] = fields["updated_by_name"]
        return existing

    def archive_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]:
        existing = self.procedures[procedure_id]
        existing["status"] = "archived"
        existing["archived_at"] = datetime.now(timezone.utc)
        existing["archived_by_user_id"] = fields["archived_by_user_id"]
        existing["archived_by_name"] = fields["archived_by_name"]
        existing["updated_by_user_id"] = fields["updated_by_user_id"]
        existing["updated_by_name"] = fields["updated_by_name"]
        return existing

    def restore_procedure(self, procedure_id: str, **fields: Any) -> dict[str, Any]:
        existing = self.procedures[procedure_id]
        existing["status"] = "draft"
        existing["archived_at"] = None
        existing["archived_by_user_id"] = None
        existing["archived_by_name"] = None
        existing["updated_by_user_id"] = fields["updated_by_user_id"]
        existing["updated_by_name"] = fields["updated_by_name"]
        return existing

    # public helpers for visibility checks
    def get_published_procedure_by_slug(self, slug: str) -> dict[str, Any] | None:
        for row in self.procedures.values():
            if (
                row["slug"] == slug
                and row["status"] == "published"
                and row.get("department_active")
            ):
                return row
        return None

    def list_active_departments_with_published_counts(self) -> list[dict[str, Any]]:
        return []

    def get_active_department_by_slug(self, slug: str) -> dict[str, Any] | None:
        return None

    def list_published_procedures_by_department_id(self, department_id: Any) -> list:
        return []


def _seed_dept(repo: AdminProbeRepo, *, active: bool = True) -> dict[str, Any]:
    return repo.create_department(
        name="Faturamento",
        slug="faturamento-admin-test",
        description="desc",
        icon="receipt",
        active=active,
        order_index=1,
        created_by_user_id="seed",
        created_by_name="seed",
        updated_by_user_id="seed",
        updated_by_name="seed",
    )


def _body(response) -> dict:
    return json.loads(response.content)


def _admin_app() -> FastAPI:
    app = FastAPI()
    app.include_router(
        guias_procedimentos_admin_router.router,
        prefix="/guias-procedimentos",
    )
    app.include_router(
        guias_procedimentos_router.router,
        prefix="/guias-procedimentos",
    )
    return app


# --- auth ---


def test_write_permissions_only_manage() -> None:
    assert perms.GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS == [
        perms.GUIAS_PROCEDIMENTOS_MANAGE
    ]
    assert perms.GUIAS_PROCEDIMENTOS_ACCESS not in perms.GUIAS_PROCEDIMENTOS_WRITE_PERMISSIONS


def test_admin_without_user_unauthorized() -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router import (
        list_admin_departments,
    )

    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=None,
    ):
        with pytest.raises(Exception, match="Unauthorized"):
            list_admin_departments()


def test_admin_with_access_only_forbidden() -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router import (
        list_admin_departments,
    )

    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[perms.GUIAS_PROCEDIMENTOS_ACCESS],
    )
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with pytest.raises(Exception, match="Forbidden"):
            list_admin_departments()


def test_admin_http_without_bearer_401() -> None:
    from delpi_auth.middleware.fastapi_auth import jwt_middleware

    app = FastAPI()

    @app.middleware("http")
    async def auth_mw(request: Request, call_next):
        return await jwt_middleware(request, call_next)

    app.include_router(
        guias_procedimentos_admin_router.router,
        prefix="/guias-procedimentos",
    )
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/guias-procedimentos/admin/departments").status_code == 401


# --- slug ---


def test_slug_rejects_invalid() -> None:
    with pytest.raises(GuiasValidationError):
        validate_slug("Com Acento", max_length=120)
    with pytest.raises(GuiasValidationError):
        validate_slug("com_underscore", max_length=120)
    with pytest.raises(GuiasValidationError):
        validate_slug("com/barra", max_length=120)


def test_slug_accepts_valid() -> None:
    assert validate_slug("emissao-nota-fiscal", max_length=160) == "emissao-nota-fiscal"


# --- departments ---


def test_list_admin_departments_includes_inactive() -> None:
    repo = AdminProbeRepo()
    _seed_dept(repo, active=True)
    repo.create_department(
        name="Inativo",
        slug="inativo",
        description="",
        icon="book-open",
        active=False,
        order_index=2,
        created_by_user_id="u",
        created_by_name="u",
        updated_by_user_id="u",
        updated_by_name="u",
    )
    data = ListAdminDepartmentsUseCase(repo).execute()
    assert len(data) == 2
    assert {d["active"] for d in data} == {True, False}


def test_create_department_and_duplicate_slug() -> None:
    repo = AdminProbeRepo()
    created = CreateDepartmentUseCase(repo).execute(
        {
            "name": "Qualidade",
            "slug": "qualidade",
            "description": "d",
            "icon": "book-open",
            "active": True,
            "order_index": 1,
        },
        ACTOR,
    )
    assert created["slug"] == "qualidade"
    assert created["created_by_user_id"] == "user-1"
    with pytest.raises(GuiasConflictError):
        CreateDepartmentUseCase(repo).execute(
            {
                "name": "Outro",
                "slug": "qualidade",
                "description": "",
                "icon": "receipt",
                "active": True,
                "order_index": 0,
            },
            ACTOR,
        )


def test_update_and_deactivate_department() -> None:
    repo = AdminProbeRepo()
    dept = _seed_dept(repo)
    updated = UpdateDepartmentUseCase(repo).execute(
        dept["id"],
        {
            "name": "Faturamento",
            "slug": dept["slug"],
            "description": "nova",
            "icon": "receipt",
            "active": False,
            "order_index": 3,
        },
        ACTOR,
    )
    assert updated["active"] is False
    assert updated["order_index"] == 3
    assert updated["updated_by_user_id"] == "user-1"


def test_get_department_not_found() -> None:
    repo = AdminProbeRepo()
    with pytest.raises(GuiasNotFoundError):
        GetAdminDepartmentUseCase(repo).execute(str(uuid4()))


# --- procedures ---


def test_create_procedure_as_draft_and_sanitize() -> None:
    repo = AdminProbeRepo()
    dept = _seed_dept(repo)
    created = CreateProcedureUseCase(repo).execute(
        {
            "department_id": dept["id"],
            "title": "Guia NF",
            "slug": "guia-nf-test",
            "summary": "resumo",
            "content_html": '<p>ok</p><script>alert(1)</script><a href="javascript:x">x</a>',
            "reading_time_minutes": 4,
            "order_index": 1,
        },
        ACTOR,
    )
    assert created["status"] == "draft"
    assert "<script>" not in created["content_html"]
    assert "javascript:" not in created["content_html"].lower()
    assert created["created_by_user_id"] == "user-1"


def test_create_rejects_missing_department_and_duplicate_slug() -> None:
    repo = AdminProbeRepo()
    dept = _seed_dept(repo)
    with pytest.raises(GuiasValidationError):
        CreateProcedureUseCase(repo).execute(
            {
                "department_id": str(uuid4()),
                "title": "T",
                "slug": "x-y",
                "summary": "s",
                "content_html": "<p>a</p>",
                "order_index": 0,
            },
            ACTOR,
        )
    CreateProcedureUseCase(repo).execute(
        {
            "department_id": dept["id"],
            "title": "T",
            "slug": "dup-slug",
            "summary": "s",
            "content_html": "<p>a</p>",
            "order_index": 0,
        },
        ACTOR,
    )
    with pytest.raises(GuiasConflictError):
        CreateProcedureUseCase(repo).execute(
            {
                "department_id": dept["id"],
                "title": "T2",
                "slug": "dup-slug",
                "summary": "s",
                "content_html": "<p>b</p>",
                "order_index": 0,
            },
            ACTOR,
        )


def test_update_sanitizes_html() -> None:
    repo = AdminProbeRepo()
    dept = _seed_dept(repo)
    created = CreateProcedureUseCase(repo).execute(
        {
            "department_id": dept["id"],
            "title": "T",
            "slug": "upd-html",
            "summary": "s",
            "content_html": "<p>a</p>",
            "order_index": 0,
        },
        ACTOR,
    )
    updated = UpdateProcedureUseCase(repo).execute(
        created["id"],
        {
            "department_id": dept["id"],
            "title": "T",
            "slug": "upd-html",
            "summary": "s",
            "content_html": '<p onclick="x">y</p><iframe src="x"></iframe>',
            "order_index": 0,
        },
        ACTOR,
    )
    assert "onclick" not in updated["content_html"].lower()
    assert "iframe" not in updated["content_html"].lower()


def test_publish_unpublish_archive_visibility() -> None:
    repo = AdminProbeRepo()
    dept = _seed_dept(repo, active=True)
    created = CreateProcedureUseCase(repo).execute(
        {
            "department_id": dept["id"],
            "title": "Publicável",
            "slug": "pub-vis",
            "summary": "resumo ok",
            "content_html": "<p>conteudo</p>",
            "reading_time_minutes": 2,
            "order_index": 1,
        },
        ACTOR,
    )
    assert GetGuiasProcedureBySlugUseCase(repo).execute("pub-vis") is None

    published = PublishProcedureUseCase(repo).execute(created["id"], ACTOR)
    assert published["status"] == "published"
    assert published["published_by_user_id"] == "user-1"
    public = GetGuiasProcedureBySlugUseCase(repo).execute("pub-vis")
    assert public is not None
    assert public["slug"] == "pub-vis"

    unpublished = UnpublishProcedureUseCase(repo).execute(created["id"], ACTOR)
    assert unpublished["status"] == "draft"
    assert unpublished["published_at"] is not None  # histórico
    assert GetGuiasProcedureBySlugUseCase(repo).execute("pub-vis") is None

    # republicar e arquivar
    PublishProcedureUseCase(repo).execute(created["id"], ACTOR)
    archived = ArchiveProcedureUseCase(repo).execute(created["id"], ACTOR)
    assert archived["status"] == "archived"
    assert archived["archived_by_user_id"] == "user-1"
    assert GetGuiasProcedureBySlugUseCase(repo).execute("pub-vis") is None


def test_publish_blocked_when_department_inactive() -> None:
    repo = AdminProbeRepo()
    dept = _seed_dept(repo, active=False)
    created = CreateProcedureUseCase(repo).execute(
        {
            "department_id": dept["id"],
            "title": "T",
            "slug": "blocked-pub",
            "summary": "resumo",
            "content_html": "<p>x</p>",
            "order_index": 0,
        },
        ACTOR,
    )
    with pytest.raises(GuiasValidationError, match="inativo"):
        PublishProcedureUseCase(repo).execute(created["id"], ACTOR)


def test_sanitizer_blocks_more_vectors() -> None:
    dirty = (
        '<p onerror="x">a</p><style>b{}</style><form></form>'
        "<svg><script>1</script></svg>"
    )
    cleaned = GuideHtmlSanitizer.sanitize(dirty)
    assert "onerror" not in cleaned.lower()
    assert "style" not in cleaned.lower()
    assert "form" not in cleaned.lower()
    assert "svg" not in cleaned.lower()
    assert "script" not in cleaned.lower()


def test_manage_can_list_admin_via_http() -> None:
    client = TestClient(_admin_app())
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[perms.GUIAS_PROCEDIMENTOS_MANAGE],
    )
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.guias_procedimentos.guias_procedimentos_admin_router.build_list_admin_departments_use_case"
        ) as mock_build:
            mock_build.return_value.execute.return_value = []
            response = client.get("/guias-procedimentos/admin/departments")
    assert response.status_code == 200
    assert _body(response)["meta"]["operationId"] == (
        "list_guias_procedimentos_admin_departments"
    )
