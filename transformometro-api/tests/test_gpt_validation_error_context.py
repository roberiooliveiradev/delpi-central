from __future__ import annotations

from unittest.mock import MagicMock, patch

from pydantic import ValidationError

from tm_app.core.errors import format_api_error, format_validation_error
from tm_app.interface.http.routes import gpt_actions_routes
from tm_app.interface.http.schemas.crud_schemas import RecursoBody


def test_format_validation_error_lists_missing_fields():
    try:
        RecursoBody.model_validate({"observacoes": "x"})
    except ValidationError as exc:
        message, data = format_validation_error(exc)

    assert "nome_recurso" in message
    assert "tipo_custo" in message
    assert "recorrencia" in message
    assert "Campos obrigatórios ausentes" in message
    fields = {item["field"] for item in data["errors"]}
    assert {"nome_recurso", "tipo_custo", "recorrencia"} <= fields
    assert data["error_count"] == 3


def test_format_api_error_does_not_collapse_pydantic_to_generic():
    try:
        RecursoBody.model_validate({})
    except ValidationError as exc:
        msg = format_api_error(exc)
    assert msg != "Erro interno do servidor."
    assert "nome_recurso" in msg or "Campos obrigatórios" in msg


def test_gpt_handle_returns_structured_400_for_pydantic_validation():
    try:
        RecursoBody.model_validate({"conteudo": {"nome_recurso": "x"}})
    except ValidationError as exc:
        response = gpt_actions_routes._handle(exc)

    assert response.status_code == 400
    body = response.body
    import json

    payload = json.loads(body.decode("utf-8"))
    assert payload["success"] is False
    assert "nome_recurso" in payload["message"]
    assert payload["data"]["errors"]
    assert payload["data"]["error_count"] >= 1


def test_create_shared_resource_validation_exposes_fields_to_gpt(tm_client):
    """Regression: packing fields in conteudo must yield readable missing-field message."""
    with patch.object(gpt_actions_routes._dispatch, "_require_capability"):
        response = tm_client.post(
            "/transformometro/gpt-actions/v1/records/shared_resource",
            json={
                "data": {
                    "conteudo": {
                        "nome_recurso": "Embaixador",
                        "tipo_custo": "mao_obra",
                        "recorrencia": "mensal",
                    }
                }
            },
        )
    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert "nome_recurso" in payload["message"]
    assert "tipo_custo" in payload["message"]
    assert "recorrencia" in payload["message"]
    assert "Erro interno" not in payload["message"]
