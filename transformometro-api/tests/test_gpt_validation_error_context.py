from __future__ import annotations

import json
from unittest.mock import patch

from pydantic import ValidationError

from tm_app.application.gpt_actions.dispatch_service import GptActionsError
from tm_app.core.errors import (
    envelope_from_detail_body,
    format_api_error,
    format_validation_error,
    public_error_parts,
    safe_public_message,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginsRepositoryError,
)
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


def test_long_value_error_is_truncated_not_generic():
    msg = "campo_x inválido: " + ("z" * 600)
    status, message, data = public_error_parts(ValueError(msg))
    assert status == 400
    assert data["error_kind"] == "validation"
    assert message != "Erro interno do servidor."
    assert message.endswith("…")
    assert "campo_x" in message


def test_plugins_repository_error_is_persistence_503():
    status, message, data = public_error_parts(
        PluginsRepositoryError("unique violation on codigo_recurso")
    )
    assert status == 503
    assert data["error_kind"] == "persistence"
    assert "codigo_recurso" in message


def test_gpt_actions_error_keeps_domain_message():
    status, message, data = public_error_parts(
        GptActionsError("Recurso não encontrado.", 404)
    )
    assert status == 404
    assert message == "Recurso não encontrado."
    assert data["error_kind"] == "domain"


def test_type_error_exposes_kind_not_only_blank():
    status, message, data = public_error_parts(TypeError("boom"))
    assert status == 500
    assert message == "Erro interno do servidor."
    assert data["error_kind"] == "internal"
    assert data["error_type"] == "TypeError"


def test_auth_detail_converts_to_envelope_fields():
    message, data = envelope_from_detail_body(
        status_code=401,
        body={"detail": "Unauthorized"},
    )
    assert message == "Unauthorized"
    assert data["error_kind"] == "authn"


def test_gpt_handle_returns_structured_400_for_pydantic_validation():
    try:
        RecursoBody.model_validate({"conteudo": {"nome_recurso": "x"}})
    except ValidationError as exc:
        response = gpt_actions_routes._handle(exc)

    assert response.status_code == 400
    payload = json.loads(response.body.decode("utf-8"))
    assert payload["success"] is False
    assert "nome_recurso" in payload["message"]
    assert payload["data"]["errors"]
    assert payload["data"]["error_kind"] == "validation"


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
    assert payload["data"]["error_kind"] == "validation"


def test_safe_public_message_truncates():
    assert safe_public_message("ok") == "ok"
    assert safe_public_message("a" * 500).endswith("…")
