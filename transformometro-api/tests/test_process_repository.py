from __future__ import annotations

from unittest.mock import MagicMock

from tm_app.infrastructure.persistence.repositories.process_repository import ProcessoRepository


def test_next_codigo_increments():
    repo = ProcessoRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(return_value={"seq": 41})
    assert repo.next_codigo() == "PROC-0041"


def test_create_uses_generated_codigo_when_missing():
    conn = MagicMock()
    repo = ProcessoRepository(connection=conn)
    repo.fetch_one = MagicMock(return_value={"seq": 1})
    repo.execute_returning_one = MagicMock(
        return_value={
            "processo_id": "p1",
            "codigo_processo": "PROC-0001",
            "nome_processo": "Teste",
        }
    )

    row = repo.create(
        {
            "nome_processo": "Teste",
            "status_processo": "ativo",
        }
    )

    assert row["codigo_processo"] == "PROC-0001"
    repo.execute_returning_one.assert_called_once()


def test_touch_updated_at_bumps_process_timestamp():
    repo = ProcessoRepository(connection=MagicMock())
    repo.execute_returning_one = MagicMock(return_value={"processo_id": "p1"})
    assert repo.touch_updated_at("p1") is True
    sql = repo.execute_returning_one.call_args.args[0]
    assert "updated_at = NOW()" in sql
    assert "WHERE processo_id" in sql
    assert repo.execute_returning_one.call_args.args[1] == ("p1",)


def test_touch_updated_at_ignores_blank_id():
    repo = ProcessoRepository(connection=MagicMock())
    repo.execute_returning_one = MagicMock()
    assert repo.touch_updated_at("") is False
    repo.execute_returning_one.assert_not_called()
