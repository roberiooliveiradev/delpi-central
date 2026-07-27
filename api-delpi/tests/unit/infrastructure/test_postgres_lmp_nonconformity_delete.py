"""Regressão — exclusão de NC deve liberar CASCADE do histórico append-only."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from app.infrastructure.persistence.plugins.repositories.engineering.postgres_lmp_nonconformity_repository import (
    PostgresLmpNonconformityRepository,
)


class _FakeCursor:
    def __init__(self) -> None:
        self.statements: list[str] = []
        self._returning: dict[str, Any] | None = {"id": "11111111-1111-1111-1111-111111111111"}

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, query: str, params: tuple[Any, ...] | None = None) -> None:
        self.statements.append(" ".join(query.split()))
        self._last_params = params

    def fetchone(self) -> dict[str, Any] | None:
        return self._returning


def test_delete_record_enables_history_delete_guc_before_cascade() -> None:
    cursor = _FakeCursor()
    connection = MagicMock()
    connection.cursor.return_value = cursor
    repo = PostgresLmpNonconformityRepository(connection=connection)
    repo.commit = MagicMock()  # type: ignore[method-assign]
    repo.rollback = MagicMock()  # type: ignore[method-assign]

    assert repo.delete_record("11111111-1111-1111-1111-111111111111") is True

    assert any(
        "set_config('app.allow_lmp_nc_history_delete', 'true', true)" in sql
        for sql in cursor.statements
    )
    assert any(
        "DELETE FROM engineering.lmp_nonconformities" in sql for sql in cursor.statements
    )
    assert cursor.statements[0].startswith("SELECT set_config")
    repo.commit.assert_called_once()
