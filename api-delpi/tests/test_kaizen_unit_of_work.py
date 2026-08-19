"""Regressão: cadastro/versão de kaizen precisa de lease único.

Sem ``with self.db():``, o pool devolve a conexão com rollback entre o
INSERT do kaizen e o da revisão (FK) — a UI mostra
«Falha ao executar comando com retorno no banco de plugins.» no cadastro
e «Kaizen não encontrado.» ao criar nova versão.
"""
from __future__ import annotations

import inspect

from app.infrastructure.persistence.plugins.repositories.kaizen.postgres_kaizen_repository import (
    PostgresKaizenRepository,
)


def _assert_unit_of_work(method) -> None:
    source = inspect.getsource(method)
    assert "with self.db():" in source, (
        f"{method.__qualname__} deve abrir lease único antes de "
        "execute(auto_commit=False)"
    )


def test_kaizen_writes_use_unit_of_work() -> None:
    _assert_unit_of_work(PostgresKaizenRepository.create_record)
    _assert_unit_of_work(PostgresKaizenRepository.update_record)
    _assert_unit_of_work(PostgresKaizenRepository.create_version)
    _assert_unit_of_work(PostgresKaizenRepository.update_version)
    _assert_unit_of_work(PostgresKaizenRepository.implement_version)
    _assert_unit_of_work(PostgresKaizenRepository.delete_version)
    _assert_unit_of_work(PostgresKaizenRepository.delete_record)
