"""Regressão: criar reserva precisa de lease único.

Sem ``with self.db():``, o pool dá rollback no INSERT e a API devolve o
RETURNING em memória — sucesso na UI, calendário e minhas reservas vazios.
"""
from __future__ import annotations

import inspect

from app.infrastructure.persistence.plugins.repositories.scheduling.postgres_scheduling_repository import (
    PostgresSchedulingRepository,
)


def _assert_unit_of_work(method) -> None:
    source = inspect.getsource(method)
    assert "with self.db():" in source, (
        f"{method.__qualname__} deve abrir lease único antes de "
        "execute(auto_commit=False)"
    )


def test_scheduling_writes_use_unit_of_work() -> None:
    _assert_unit_of_work(PostgresSchedulingRepository.create_booking)
    _assert_unit_of_work(PostgresSchedulingRepository.create_recurring_bookings)
