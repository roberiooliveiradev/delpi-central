from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from maint_app.application.services.filial_access_scope_service import FilialAccessScope
from maint_app.main import app

STATUS_ID = "b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22"
STATUS_ID_UPDATE = "c2eebc99-9c0b-4ef8-bb6d-6bb9bd380a33"
STATUS_ID_DELETE = "d3eebc99-9c0b-4ef8-bb6d-6bb9bd380a44"
STATUS_ID_LIST = "e4eebc99-9c0b-4ef8-bb6d-6bb9bd380a55"


def _manage_user():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=[
            "maintenance.mini-applicators.view.filial-01",
            "maintenance.mini-applicators.manage.filial-01",
        ],
    )


def _view_user():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.mini-applicators.view.filial-01"],
    )


def _scope():
    return FilialAccessScope(
        mode="scoped",
        allowed_codigos=frozenset({"01"}),
        manage_codigos=frozenset({"01"}),
    )


@patch("maint_app.interface.http.routes.operational_routes.resolve_access_scope")
@patch("maint_app.interface.http.routes.operational_routes.resolve_user")
@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.operational_routes.StatusPecaRepository")
def test_create_status_peca(mock_repo_cls, _public, mock_user, mock_scope):
    mock_user.return_value = _manage_user()
    mock_scope.return_value = _scope()
    mock_repo_cls.return_value.create.return_value = {
        "status_id": STATUS_ID,
        "descricao": "CRÍTICO",
        "operador": ">=",
        "percentual": 95,
        "filial": "01",
    }

    client = TestClient(app)
    response = client.post(
        "/maintenance/status-peca",
        json={
            "filial": "01",
            "descricao": "CRÍTICO",
            "operador": ">=",
            "percentual": 95,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status_id"] == STATUS_ID
    mock_repo_cls.return_value.create.assert_called_once_with(
        filial="01",
        descricao="CRÍTICO",
        operador=">=",
        percentual=95,
    )


@patch("maint_app.interface.http.routes.operational_routes.resolve_access_scope")
@patch("maint_app.interface.http.routes.operational_routes.resolve_user")
@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.operational_routes.StatusPecaRepository")
def test_update_status_peca(mock_repo_cls, _public, mock_user, mock_scope):
    mock_user.return_value = _manage_user()
    mock_scope.return_value = _scope()
    mock_repo_cls.return_value.update.return_value = {
        "status_id": STATUS_ID_UPDATE,
        "descricao": "ATENÇÃO",
        "operador": ">=",
        "percentual": 85,
        "filial": "01",
    }

    client = TestClient(app)
    response = client.put(
        f"/maintenance/status-peca/{STATUS_ID_UPDATE}?filial=01",
        json={"descricao": "ATENÇÃO", "operador": ">=", "percentual": 85},
    )

    assert response.status_code == 200
    assert response.json()["data"]["percentual"] == 85


@patch("maint_app.interface.http.routes.operational_routes.resolve_access_scope")
@patch("maint_app.interface.http.routes.operational_routes.resolve_user")
@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.operational_routes.StatusPecaRepository")
def test_delete_status_peca(mock_repo_cls, _public, mock_user, mock_scope):
    mock_user.return_value = _manage_user()
    mock_scope.return_value = _scope()

    client = TestClient(app)
    response = client.delete(f"/maintenance/status-peca/{STATUS_ID_DELETE}?filial=01")

    assert response.status_code == 200
    assert response.json()["success"] is True
    mock_repo_cls.return_value.soft_delete.assert_called_once_with(STATUS_ID_DELETE, filial="01")


@patch("maint_app.interface.http.routes.operational_routes.resolve_access_scope")
@patch("maint_app.interface.http.routes.operational_routes.resolve_user")
@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.operational_routes.StatusPecaRepository")
def test_list_status_peca(mock_repo_cls, _public, mock_user, mock_scope):
    mock_user.return_value = _view_user()
    mock_scope.return_value = _scope()
    mock_repo_cls.return_value.list_active_paged.return_value = (
        [
            {
                "status_id": STATUS_ID_LIST,
                "descricao": "OK",
                "operador": "<",
                "percentual": 80,
                "filial": "01",
            },
        ],
        1,
    )

    client = TestClient(app)
    response = client.get("/maintenance/status-peca?filial=01")

    assert response.status_code == 200
    assert response.json()["data"]["total"] == 1
