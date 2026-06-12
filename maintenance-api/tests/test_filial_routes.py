from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from maint_app.main import app


def _manage_user():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.manage"],
    )


def _view_user():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.mini-applicators.view.filial-01"],
    )


@patch("maint_app.interface.http.routes.filial_routes.resolve_user")
@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.filial_routes.FilialRepository")
def test_create_filial_requires_manage(mock_repo_cls, _public, mock_user):
    mock_user.return_value = _manage_user()
    mock_repo_cls.return_value.create.return_value = {
        "filial_id": 3,
        "codigo_filial": "03",
        "nome_filial": "Filial 03",
        "status_filial": "ativo",
        "data_criacao": None,
        "data_alteracao": None,
    }

    client = TestClient(app)
    response = client.post(
        "/maintenance/filiais",
        json={"codigo_filial": "03", "nome_filial": "Filial 03", "status_filial": "ativo"},
    )

    assert response.status_code == 201
    mock_repo_cls.return_value.create.assert_called_once()


@patch("maint_app.interface.http.routes.filial_routes.resolve_user")
@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.filial_routes.FilialRepository")
def test_create_filial_forbidden_without_manage(mock_repo_cls, _public, mock_user):
    mock_user.return_value = _view_user()

    client = TestClient(app)
    response = client.post(
        "/maintenance/filiais",
        json={"codigo_filial": "03", "nome_filial": "Filial 03", "status_filial": "ativo"},
    )

    assert response.status_code == 403
    mock_repo_cls.return_value.create.assert_not_called()


@patch("maint_app.interface.http.routes.filial_routes.resolve_access_scope")
@patch("maint_app.interface.http.routes.filial_routes.resolve_user")
@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.filial_routes.FilialRepository")
def test_list_filiais_admin(mock_repo_cls, _public, mock_user, mock_scope):
    from maint_app.application.services.filial_access_scope_service import FilialAccessScope

    mock_user.return_value = _manage_user()
    mock_scope.return_value = FilialAccessScope(
        mode="scoped",
        allowed_codigos=frozenset({"01"}),
        manage_codigos=frozenset({"01"}),
    )
    mock_repo_cls.return_value.list.return_value = [
        {
            "filial_id": 1,
            "codigo_filial": "01",
            "nome_filial": "Matriz",
            "status_filial": "ativo",
            "data_criacao": None,
            "data_alteracao": None,
        }
    ]

    client = TestClient(app)
    response = client.get("/maintenance/filiais?admin=true&include_inactive=true")

    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1
