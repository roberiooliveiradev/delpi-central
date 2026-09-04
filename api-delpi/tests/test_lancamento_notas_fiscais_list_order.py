"""Lista de solicitações LNF — mais recentes primeiro (received_at DESC)."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.persistence.plugins.repositories.lancamento_notas_fiscais.postgres_invoice_posting_repository import (
    PostgresInvoicePostingRepository,
)


def test_list_requests_orders_by_received_at_desc() -> None:
    repo = PostgresInvoicePostingRepository(connection=MagicMock())
    captured: list[str] = []

    def fake_fetch_one(sql: str, _params=None):
        captured.append(sql)
        return {"total": 0}

    def fake_fetch_all(sql: str, _params=None):
        captured.append(sql)
        return []

    repo.fetch_one = fake_fetch_one  # type: ignore[method-assign]
    repo.fetch_all = fake_fetch_all  # type: ignore[method-assign]

    repo.list_requests(filters={}, created_by_user_id=None, page=1, page_size=20)

    list_sql = next(sql for sql in captured if "LIMIT" in sql.upper())
    assert "ORDER BY received_at DESC, created_at DESC" in list_sql
    assert "ORDER BY received_at ASC" not in list_sql
