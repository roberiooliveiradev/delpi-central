from __future__ import annotations

from unittest.mock import MagicMock

from tm_app.infrastructure.persistence.repositories.audit_repository import AuditRepository


def test_list_for_processo_paginates_and_counts():
    repo = AuditRepository(connection=MagicMock())
    repo.fetch_one = MagicMock(return_value={"total": 3})
    repo.fetch_all = MagicMock(
        return_value=[
            {
                "audit_id": "a1",
                "entity_type": "processo",
                "entity_id": "p1",
                "action": "create",
                "user_id": "u1",
                "user_email": "user@example.com",
                "payload_json": {},
                "created_at": "2026-01-01T10:00:00+00:00",
            }
        ]
    )

    result = repo.list_for_processo("p1", page=1, page_size=50)

    assert result["total"] == 3
    assert result["page"] == 1
    assert result["page_size"] == 50
    assert len(result["items"]) == 1
    repo.fetch_one.assert_called_once()
    repo.fetch_all.assert_called_once()
    sql = repo.fetch_all.call_args[0][0]
    assert "processo_instancias" in sql
    assert "investimentos" in sql
