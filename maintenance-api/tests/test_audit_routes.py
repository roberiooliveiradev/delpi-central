from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from maint_app.application.services.filial_access_scope_service import FilialAccessScope
from maint_app.main import app


def _view_user():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.mini-applicators.view.filial-01"],
    )


def _scope():
    return FilialAccessScope(
        mode="scoped",
        allowed_codigos=frozenset({"01"}),
        manage_codigos=frozenset(),
    )


@patch("maint_app.interface.http.routes.mini_applicators_routes.resolve_access_scope")
@patch("maint_app.interface.http.routes.mini_applicators_routes.resolve_user")
@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.mini_applicators_routes.AuditRepository")
def test_list_ferramenta_auditoria(mock_repo_cls, _public, mock_user, mock_scope):
    mock_user.return_value = _view_user()
    mock_scope.return_value = _scope()
    mock_repo_cls.return_value.list_by_ferramenta_paged.return_value = (
        [
            {
                "audit_id": "a1",
                "entidade": "ferramenta",
                "entidade_id": "23-026",
                "acao": "reposicao.create",
                "filial": "01",
                "payload": {"golpes": 100},
                "usuario_sub": "user-1",
                "data_criacao": "2026-06-12T10:00:00",
            }
        ],
        1,
    )

    client = TestClient(app)
    response = client.get(
        "/maintenance/mini-aplicadores/ferramentas/23-026/auditoria?filial=01&page=1&page_size=10",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 1
    assert payload["data"]["items"][0]["acao"] == "reposicao.create"
    mock_repo_cls.return_value.list_by_ferramenta_paged.assert_called_once()
