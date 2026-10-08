"""Regressão — PostgresRequestRepository.list_mine sem filtro de filial.

P1 copiou de list_work_queue um ``elif branch_codes is not None`` para
list_mine, cujo contrato (port + use case + repo em memória) só declara
``branch_code``. Em Postgres, toda chamada a /requests/mine sem filtro de
filial avaliava o elif → NameError → HTTP 500. Estes testes exercem o
caminho real de montagem da query com uma conexão fake.
"""

from __future__ import annotations

import pytest

from requests_app.infrastructure.persistence.repositories import (
    postgres_repositories,
)
from requests_app.infrastructure.persistence.repositories.postgres_repositories import (  # noqa: E501
    PostgresRequestRepository,
)


class _FakeCursor:
    def __init__(self) -> None:
        self.queries: list[tuple[str, list]] = []
        self._one: dict = {"total": 0}
        self._all: list = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        self.queries.append((sql, list(params or [])))

    def fetchone(self):
        return self._one

    def fetchall(self):
        return self._all


class _FakeConn:
    def __init__(self) -> None:
        self.cursor_obj = _FakeCursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        pass


@pytest.fixture
def fake_conn(monkeypatch):
    conn = _FakeConn()
    monkeypatch.setattr(
        postgres_repositories, "plugins_connection", lambda: conn
    )
    return conn


def test_list_mine_without_branch_filter_runs(fake_conn):
    repo = PostgresRequestRepository()
    items, total = repo.list_mine(user_id="u-1")
    assert items == []
    assert total == 0
    sql = fake_conn.cursor_obj.queries[0][0]
    assert "r.created_by_user_id = %s" in sql
    assert "branch_codes" not in sql


def test_list_mine_with_branch_filter_uses_branch_code(fake_conn):
    repo = PostgresRequestRepository()
    repo.list_mine(user_id="u-1", branch_code="02")
    sql, params = fake_conn.cursor_obj.queries[0]
    assert "r.branch_code = %s" in sql
    assert params[:2] == ["u-1", "02"]
