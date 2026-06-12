from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient

from maint_app.main import app


@patch("delpi_auth.middleware.fastapi_auth.is_public_path", return_value=True)
@patch("maint_app.interface.http.routes.preventiva_routes.build_preventiva_service")
def test_preventiva_alertas_envelope(mock_service, _public):
    mock_service.return_value.listar_alertas.return_value = [
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
    ]

    client = TestClient(app)
    response = client.get("/maintenance/preventiva/alertas?filial=01")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["total"] == 1
    assert payload["data"]["items"][0]["status"] == "OK"
