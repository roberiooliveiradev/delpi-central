from unittest.mock import MagicMock, patch

import pytest

from maint_app.application.list_query import ListQuery
from maint_app.infrastructure.persistence.repositories.audit_repository import AuditRepository


@patch.object(AuditRepository, "execute")
def test_log_inserts_audit_row(mock_execute):
    repo = AuditRepository(connection=MagicMock())

    repo.log(
        entidade="ferramenta",
        entidade_id="23-026",
        acao="reposicao.create",
        filial="01",
        usuario_sub="user-123",
        usuario_nome="Maria Silva",
        payload={"reposicao_id": "abc", "golpes": 1000},
    )

    mock_execute.assert_called_once()
    query, params = mock_execute.call_args[0]
    assert "INSERT INTO maintenance.audit_logs" in query
    assert "usuario_nome" in query
    assert params[0] == "ferramenta"
    assert params[1] == "23-026"
    assert params[2] == "reposicao.create"
    assert params[3] == "01"
    assert '"golpes": 1000' in params[4]
    assert params[5] == "user-123"
    assert params[6] == "Maria Silva"


@patch.object(AuditRepository, "fetch_paged")
def test_list_by_ferramenta_paged(mock_fetch_paged):
    mock_fetch_paged.return_value = ([{"audit_id": "1"}], 1)
    repo = AuditRepository(connection=MagicMock())
    query = ListQuery(page=2, page_size=5)

    items, total = repo.list_by_ferramenta_paged(
        filial="01",
        codigo_ferramenta="23-026",
        query=query,
    )

    assert items == [{"audit_id": "1"}]
    assert total == 1
    mock_fetch_paged.assert_called_once()
    kwargs = mock_fetch_paged.call_args.kwargs
    assert kwargs["params"] == ("01", "23-026")
    assert kwargs["page"] == 2
    assert kwargs["page_size"] == 5
    assert "entidade = 'ferramenta'" in kwargs["select_sql"]
