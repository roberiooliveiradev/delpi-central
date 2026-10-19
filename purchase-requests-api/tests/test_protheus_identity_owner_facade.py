from __future__ import annotations

from unittest.mock import MagicMock, patch

from purchase_requests_app.infrastructure.persistence.repositories.user_protheus_mapping_repository import (
    UserProtheusMappingRepository,
)


def test_repository_reads_core_when_owner_core(monkeypatch):
    monkeypatch.setenv("PROTHEUS_IDENTITY_OWNER", "core")
    gateway = MagicMock()
    gateway.get_by_user_id.return_value = {
        "user_id": "u1",
        "protheus_user_id": "000234",
        "mapping_status": "mapped",
        "verified": True,
    }
    repo = UserProtheusMappingRepository(core_gateway=gateway)
    result = repo.get_mapping("u1")
    assert result["protheus_user_id"] == "000234"
    gateway.get_by_user_id.assert_called_once_with("u1")


def test_repository_writes_core_when_owner_core(monkeypatch):
    monkeypatch.setenv("PROTHEUS_IDENTITY_OWNER", "core")
    gateway = MagicMock()
    gateway.upsert.return_value = {
        "user_id": "u1",
        "protheus_user_id": "000234",
        "mapping_status": "mapped",
        "verified": True,
    }
    repo = UserProtheusMappingRepository(core_gateway=gateway)
    result = repo.upsert_mapping(
        user_id="u1",
        protheus_user_id="000234",
        protheus_user_code="X",
        mapping_status="mapped",
        mapping_source="manual",
        verified=True,
    )
    assert result["protheus_user_id"] == "000234"
    gateway.upsert.assert_called_once()


def test_repository_uses_local_when_owner_legacy(monkeypatch):
    monkeypatch.setenv("PROTHEUS_IDENTITY_OWNER", "legacy")
    gateway = MagicMock()
    repo = UserProtheusMappingRepository(core_gateway=gateway)
    with patch.object(
        repo,
        "_get_mapping_local",
        return_value={"user_id": "u1", "protheus_user_id": "000001"},
    ) as local:
        result = repo.get_mapping("u1")
    assert result["protheus_user_id"] == "000001"
    local.assert_called_once_with("u1")
    gateway.get_by_user_id.assert_not_called()
