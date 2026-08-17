"""Regressão: writes LNF com histórico precisam de lease único.

Sem ``with self.db():``, o pool devolve a conexão com rollback entre o
INSERT da solicitação e o INSERT do histórico — FK e 500
«Erro ao criar solicitação.» (mesmo padrão do Auditoria 5S).
"""
from __future__ import annotations

import inspect

from app.infrastructure.persistence.plugins.repositories.invoice_issuance.postgres_invoice_issuance_repository import (
    PostgresInvoiceIssuanceRepository,
)
from app.infrastructure.persistence.plugins.repositories.lancamento_notas_fiscais.postgres_invoice_posting_repository import (
    PostgresInvoicePostingRepository,
)


def _assert_unit_of_work(method) -> None:
    source = inspect.getsource(method)
    assert "with self.db():" in source, (
        f"{method.__qualname__} deve abrir lease único antes de "
        "execute(auto_commit=False) em sequência"
    )


def test_lnf_multi_statement_writes_use_unit_of_work() -> None:
    _assert_unit_of_work(PostgresInvoicePostingRepository.create_request_with_history)
    _assert_unit_of_work(PostgresInvoicePostingRepository.replace_linked_purchase_orders)
    _assert_unit_of_work(PostgresInvoicePostingRepository.mark_reconciled_posted_batch)
    _assert_unit_of_work(PostgresInvoicePostingRepository.update_request_with_history)
    _assert_unit_of_work(PostgresInvoicePostingRepository.add_comment)


def test_invoice_issuance_multi_statement_writes_use_unit_of_work() -> None:
    _assert_unit_of_work(PostgresInvoiceIssuanceRepository.create_request_with_history)
    _assert_unit_of_work(PostgresInvoiceIssuanceRepository.update_returned_request)
    _assert_unit_of_work(PostgresInvoiceIssuanceRepository.update_status)
