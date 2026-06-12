from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from maint_app.application.services.filial_access_scope_service import FilialAccessScope
from maint_app.main import app


@patch("maint_app.interface.http.routes.preventiva_routes.resolve_access_scope")
@patch("maint_app.interface.http.routes.preventiva_routes.resolve_user")
@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.preventiva_routes.build_preventiva_service")
def test_preventiva_alertas_envelope(mock_service, _public, mock_user, mock_scope):
    mock_user.return_value = SimpleNamespace(
        is_superadmin=False,
        permissions=["maintenance.mini-applicators.view.filial-01"],
    )
    mock_scope.return_value = FilialAccessScope(
        mode="scoped",
        allowed_codigos=frozenset({"01"}),
        manage_codigos=frozenset(),
    )
    mock_service.return_value.listar_alertas.return_value = (
        [
            {
                "filial": "01",
                "codigo_ferramenta": "23-001",
                "codigo_peca": "P1",
                "data_ultima_reposicao": datetime(2026, 6, 1),
                "status": "OK",
                "golpes_atuais": 10,
                "media_golpes": 100,
                "percentual_uso": 10,
            }
        ],
        1,
    )

    client = TestClient(app)
    response = client.get("/maintenance/preventiva/alertas?filial=01")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 1
    assert payload["data"]["items"][0]["status"] == "OK"
