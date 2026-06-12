from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import Request

from maint_app.interface.http.audit_http import log_ferramenta_audit


@pytest.fixture
def request_with_user():
    req = Request({"type": "http", "method": "POST", "path": "/", "headers": []})
    req.state.user = SimpleNamespace(
        id="4ac305a6-0569-40b8-a918-b908cfeba169",
        name="Ana Operadora",
        email="ana@empresa.com",
    )
    return req


@patch("maint_app.interface.http.audit_http._get_audit_repo")
def test_log_ferramenta_audit_persists(mock_get_repo, request_with_user):
    mock_repo = mock_get_repo.return_value
    log_ferramenta_audit(
        request_with_user,
        acao="reposicao.create",
        filial="01",
        codigo_ferramenta="23-026",
        payload={"reposicao_id": "r1"},
    )

    mock_repo.log.assert_called_once_with(
        entidade="ferramenta",
        entidade_id="23-026",
        acao="reposicao.create",
        filial="01",
        usuario_sub="4ac305a6-0569-40b8-a918-b908cfeba169",
        usuario_nome="Ana Operadora",
        payload={"reposicao_id": "r1"},
    )


@patch("maint_app.interface.http.audit_http._get_audit_repo")
def test_log_ferramenta_audit_does_not_raise_on_failure(mock_get_repo, request_with_user):
    mock_repo = mock_get_repo.return_value
    mock_repo.log.side_effect = RuntimeError("db down")

    log_ferramenta_audit(
        request_with_user,
        acao="reposicao.delete",
        filial="01",
        codigo_ferramenta="23-026",
    )

    mock_repo.log.assert_called_once()
