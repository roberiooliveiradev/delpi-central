"""Testes — Guias e Procedimentos (sanitizer, auth, leitura pública)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.application.security import api_delpi_permissions as perms
from app.application.services.guias_procedimentos.guide_html_sanitizer import (
    GuideHtmlSanitizer,
)
from app.application.use_cases.guias_procedimentos.public_guias_use_cases import (
    GetGuiasDepartmentBySlugUseCase,
    GetGuiasProcedureBySlugUseCase,
    ListGuiasDepartmentsUseCase,
)
from app.interface.http.routes.guias_procedimentos import guias_procedimentos_router


MIGRATIONS_DIR = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "plugins"
    / "guias-procedimentos"
)


class GuiasProbeRepo:
    def __init__(self) -> None:
        self.departments: list[dict[str, Any]] = []
        self.department_by_slug: dict[str, dict[str, Any]] = {}
        self.procedures_by_department: dict[str, list[dict[str, Any]]] = {}
        self.procedure_by_slug: dict[str, dict[str, Any] | None] = {}

    def list_active_departments_with_published_counts(self) -> list[dict[str, Any]]:
        return list(self.departments)

    def get_active_department_by_slug(self, slug: str) -> dict[str, Any] | None:
        return self.department_by_slug.get(slug)

    def list_published_procedures_by_department_id(
        self,
        department_id: Any,
    ) -> list[dict[str, Any]]:
        return list(self.procedures_by_department.get(str(department_id), []))

    def get_published_procedure_by_slug(self, slug: str) -> dict[str, Any] | None:
        return self.procedure_by_slug.get(slug)


def _auth_app() -> FastAPI:
    app = FastAPI()
    app.include_router(
        guias_procedimentos_router.router,
        prefix="/guias-procedimentos",
    )
    return app


def _body(response) -> dict:
    return json.loads(response.content)


# --- permissions ---


def test_guias_procedimentos_permission_constants() -> None:
    assert perms.GUIAS_PROCEDIMENTOS_ACCESS == "guias-procedimentos.access"
    assert perms.GUIAS_PROCEDIMENTOS_MANAGE == "guias-procedimentos.manage"
    assert perms.GUIAS_PROCEDIMENTOS_ACCESS in perms.GUIAS_PROCEDIMENTOS_READ_PERMISSIONS
    assert perms.GUIAS_PROCEDIMENTOS_MANAGE in perms.GUIAS_PROCEDIMENTOS_READ_PERMISSIONS


# --- sanitizer ---


def test_sanitizer_removes_script() -> None:
    cleaned = GuideHtmlSanitizer.sanitize('<p>ok</p><script>alert(1)</script>')
    assert "<script>" not in cleaned.lower()
    assert "alert" not in cleaned
    assert "<p>ok</p>" in cleaned


def test_sanitizer_removes_onclick() -> None:
    cleaned = GuideHtmlSanitizer.sanitize('<p onclick="evil()">texto</p>')
    assert "onclick" not in cleaned.lower()
    assert "texto" in cleaned


def test_sanitizer_blocks_javascript_url() -> None:
    cleaned = GuideHtmlSanitizer.sanitize(
        '<a href="javascript:alert(1)">link</a><a href="https://delpi.example">ok</a>'
    )
    assert "javascript:" not in cleaned.lower()
    assert 'href="https://delpi.example"' in cleaned


def test_sanitizer_keeps_editorial_tags() -> None:
    raw = (
        "<h2>Título</h2><p>Intro <strong>destaque</strong></p>"
        "<ul><li>Item</li></ul><blockquote>Nota</blockquote>"
    )
    cleaned = GuideHtmlSanitizer.sanitize(raw)
    assert "<h2>Título</h2>" in cleaned
    assert "<strong>destaque</strong>" in cleaned
    assert "<ul>" in cleaned and "<li>Item</li>" in cleaned
    assert "<blockquote>Nota</blockquote>" in cleaned


def test_sanitizer_strips_iframe_and_style() -> None:
    cleaned = GuideHtmlSanitizer.sanitize(
        '<p>x</p><iframe src="https://evil"></iframe><style>body{}</style>'
    )
    assert "iframe" not in cleaned.lower()
    assert "style" not in cleaned.lower()


def test_sanitizer_keeps_controlled_guide_media() -> None:
    media_id = "11111111-1111-4111-8111-111111111111"
    raw = (
        f'<figure class="guide-media guide-media--image">'
        f'<img src="/apps/api-delpi/guias-procedimentos/media/{media_id}/file" '
        f'alt="Diagrama" loading="lazy">'
        f"<figcaption>Diagrama</figcaption></figure>"
        f'<figure class="guide-media guide-media--video">'
        f'<video src="/apps/api-delpi/guias-procedimentos/media/{media_id}/file" '
        f'controls preload="metadata"></video>'
        f"<figcaption>Vídeo</figcaption></figure>"
        f'<p class="guide-attachment">'
        f'<a class="guide-attachment__link" '
        f'href="/apps/api-delpi/guias-procedimentos/attachments/{media_id}/file">'
        f"Baixar PDF</a></p>"
    )
    cleaned = GuideHtmlSanitizer.sanitize(raw)
    assert "guide-media--image" in cleaned
    assert "guide-media--video" in cleaned
    assert "guide-attachment" in cleaned
    assert f"/media/{media_id}/file" in cleaned
    assert "controls" in cleaned


def test_sanitizer_rejects_arbitrary_img_src() -> None:
    cleaned = GuideHtmlSanitizer.sanitize(
        '<img src="https://evil.example/x.png" alt="x">'
        '<img src="data:image/png;base64,xxx" alt="y">'
    )
    assert "<img" not in cleaned.lower()


# --- use cases / visibility ---


def test_list_departments_returns_only_repo_active_rows() -> None:
    repo = GuiasProbeRepo()
    repo.departments = [
        {
            "id": "d1",
            "name": "Faturamento",
            "slug": "faturamento",
            "description": "desc",
            "icon": "receipt",
            "order_index": 1,
            "procedure_count": 1,
        }
    ]
    result = ListGuiasDepartmentsUseCase(repo).execute()
    assert len(result) == 1
    assert result[0]["slug"] == "faturamento"
    assert result[0]["procedure_count"] == 1


def test_department_detail_returns_only_published_procedures() -> None:
    repo = GuiasProbeRepo()
    repo.department_by_slug["faturamento"] = {
        "id": "d1",
        "name": "Faturamento",
        "slug": "faturamento",
        "description": "desc",
        "icon": "receipt",
        "order_index": 1,
    }
    # Repo público já filtra published; aqui simulamos só publicados.
    repo.procedures_by_department["d1"] = [
        {
            "id": "p1",
            "title": "NF",
            "slug": "emissao-nota-fiscal",
            "summary": "resumo",
            "reading_time_minutes": 4,
            "order_index": 1,
        }
    ]
    data = GetGuiasDepartmentBySlugUseCase(repo).execute("faturamento")
    assert data is not None
    assert len(data["procedures"]) == 1
    assert data["procedures"][0]["slug"] == "emissao-nota-fiscal"


def test_department_inactive_or_missing_returns_none() -> None:
    repo = GuiasProbeRepo()
    assert GetGuiasDepartmentBySlugUseCase(repo).execute("inexistente") is None


def test_procedure_draft_or_archived_not_returned() -> None:
    repo = GuiasProbeRepo()
    # get_published_procedure_by_slug retorna None para draft/archived
    repo.procedure_by_slug["rascunho"] = None
    repo.procedure_by_slug["arquivo"] = None
    assert GetGuiasProcedureBySlugUseCase(repo).execute("rascunho") is None
    assert GetGuiasProcedureBySlugUseCase(repo).execute("arquivo") is None


def test_procedure_detail_includes_sanitized_html_and_department() -> None:
    repo = GuiasProbeRepo()
    repo.procedure_by_slug["emissao-nota-fiscal"] = {
        "id": "p1",
        "title": "NF",
        "slug": "emissao-nota-fiscal",
        "summary": "resumo",
        "content_html": '<p>ok</p><script>x</script>',
        "reading_time_minutes": 4,
        "order_index": 1,
        "published_at": datetime(2026, 7, 15, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 7, 15, tzinfo=timezone.utc),
        "department_id": "d1",
        "department_name": "Faturamento",
        "department_slug": "faturamento",
        "department_icon": "receipt",
    }
    data = GetGuiasProcedureBySlugUseCase(repo).execute("emissao-nota-fiscal")
    assert data is not None
    assert "<script>" not in data["content_html"]
    assert data["department"]["slug"] == "faturamento"
    assert "status" not in data


def test_slug_missing_procedure_returns_none() -> None:
    repo = GuiasProbeRepo()
    assert GetGuiasProcedureBySlugUseCase(repo).execute("nao-existe") is None


# --- HTTP auth / smoke com mock ---


@pytest.fixture
def guias_client() -> TestClient:
    return TestClient(_auth_app())


def test_list_departments_without_user_returns_401() -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_router import (
        list_guias_departments,
    )

    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=None,
    ):
        with pytest.raises(Exception, match="Unauthorized"):
            list_guias_departments()


def test_list_departments_without_permission_returns_403() -> None:
    from app.interface.http.routes.guias_procedimentos.guias_procedimentos_router import (
        list_guias_departments,
    )

    user = SimpleNamespace(is_superadmin=False, permissions=["other.access"])
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with pytest.raises(Exception, match="Forbidden"):
            list_guias_departments()


def test_http_without_bearer_returns_401() -> None:
    """Middleware JWT da api-delpi rejeita ausência de token com 401."""
    from delpi_auth.middleware.fastapi_auth import jwt_middleware
    from fastapi import Request

    app = FastAPI()

    @app.middleware("http")
    async def auth_mw(request: Request, call_next):
        return await jwt_middleware(request, call_next)

    app.include_router(
        guias_procedimentos_router.router,
        prefix="/guias-procedimentos",
    )
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/guias-procedimentos/departments")
    assert response.status_code == 401


def test_list_departments_with_access_permission_ok(guias_client: TestClient) -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[perms.GUIAS_PROCEDIMENTOS_ACCESS],
    )
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.guias_procedimentos.guias_procedimentos_router.build_list_guias_departments_use_case"
        ) as mock_build:
            mock_uc = mock_build.return_value
            mock_uc.execute.return_value = [
                {
                    "id": "d1",
                    "name": "Faturamento",
                    "slug": "faturamento",
                    "description": "d",
                    "icon": "receipt",
                    "order_index": 1,
                    "procedure_count": 1,
                }
            ]
            response = guias_client.get("/guias-procedimentos/departments")
    assert response.status_code == 200
    body = _body(response)
    assert body["success"] is True
    assert body["meta"]["operationId"] == "list_guias_procedimentos_departments"
    assert body["data"][0]["slug"] == "faturamento"


def test_list_departments_with_manage_permission_ok(guias_client: TestClient) -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[perms.GUIAS_PROCEDIMENTOS_MANAGE],
    )
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.guias_procedimentos.guias_procedimentos_router.build_list_guias_departments_use_case"
        ) as mock_build:
            mock_build.return_value.execute.return_value = []
            response = guias_client.get("/guias-procedimentos/departments")
    assert response.status_code == 200


def test_get_department_not_found(guias_client: TestClient) -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[perms.GUIAS_PROCEDIMENTOS_ACCESS],
    )
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.guias_procedimentos.guias_procedimentos_router.build_get_guias_department_by_slug_use_case"
        ) as mock_build:
            mock_build.return_value.execute.return_value = None
            response = guias_client.get("/guias-procedimentos/departments/x")
    assert response.status_code == 404


def test_get_procedure_not_found_for_draft(guias_client: TestClient) -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[perms.GUIAS_PROCEDIMENTOS_ACCESS],
    )
    with patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.guias_procedimentos.guias_procedimentos_router.build_get_guias_procedure_by_slug_use_case"
        ) as mock_build:
            mock_build.return_value.execute.return_value = None
            response = guias_client.get("/guias-procedimentos/procedures/rascunho")
    assert response.status_code == 404


# --- seed migration ---


def test_seed_migration_contains_current_slugs() -> None:
    seed = (MIGRATIONS_DIR / "V002__seed_faturamento_emissao_nf.sql").read_text(
        encoding="utf-8"
    )
    assert "'faturamento'" in seed
    assert "'emissao-nota-fiscal'" in seed
    assert "Faturamento" in seed
    assert "published" in seed
    assert "receipt" in seed


def test_seed_html_survives_sanitizer() -> None:
    seed = (MIGRATIONS_DIR / "V002__seed_faturamento_emissao_nf.sql").read_text(
        encoding="utf-8"
    )
    start = seed.index("$html$") + len("$html$")
    end = seed.index("$html$", start)
    html = seed[start:end]
    cleaned = GuideHtmlSanitizer.sanitize(html)
    assert "Dados do destinatário" in cleaned
    assert "Checklist de conferência" in cleaned
    assert "Faturamento" in cleaned
    assert "<script>" not in cleaned.lower()
