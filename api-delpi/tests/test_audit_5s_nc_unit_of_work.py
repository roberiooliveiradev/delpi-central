from __future__ import annotations

import inspect
from uuid import UUID

from app.infrastructure.persistence.plugins.repositories.audit_5s.postgres_audit_5s_repository import (
    PostgresAudit5sRepository,
)


def test_create_and_update_nc_use_unit_of_work() -> None:
    """Regressão: sem lease, o pool dá rollback e o evento da NC quebra com FK."""
    create_src = inspect.getsource(PostgresAudit5sRepository.create_nonconformity)
    update_src = inspect.getsource(PostgresAudit5sRepository.update_nonconformity)
    assert "with self.db():" in create_src
    assert "with self.db():" in update_src


def test_nc_event_payload_serializes_uuid() -> None:
    dumped = PostgresAudit5sRepository._json_dumps(
        {"responsible_user_id": UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")}
    )
    assert "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa" in dumped
