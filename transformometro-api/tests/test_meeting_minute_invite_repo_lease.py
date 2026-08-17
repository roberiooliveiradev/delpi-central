"""Regressão: métodos multi-statement do repo de atas usam lease do pool."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock

from tm_app.infrastructure.persistence.repositories.meeting_minute_repository import (
    MeetingMinuteRepository,
)


def test_invalidate_open_invites_acquires_db_lease():
    """Sem lease prévio, invalidate não pode acessar self._connection direto."""
    conn = MagicMock()
    cur = MagicMock()
    cur.rowcount = 2
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = None

    repo = MeetingMinuteRepository()

    @contextmanager
    def fake_db():
        yield conn

    repo.db = fake_db  # type: ignore[method-assign]
    assert repo.invalidate_open_invites(signer_id="00000000-0000-0000-0000-000000000001") == 2
    conn.commit.assert_called_once()
    cur.execute.assert_called_once()
