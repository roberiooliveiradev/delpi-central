"""Comex NCM allowlist upsert — S2S management use case (COMEX.S2)."""

from __future__ import annotations

import pytest

from app.application.contracts import (
    ContractNotReadyError,
    InvalidQueryError,
    StorageUnavailableError,
)
from app.application import market_data_allowlist as mda
from app.infrastructure.config.settings import Settings


class _FakeConnCtx:
    def __init__(self):
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def commit(self):
        self.committed = True


class _FakeRepo:
    def __init__(self, existing=None):
        self.existing = existing
        self.upserts = []

    def get_ncm_allowlist(self, code):
        return self.existing

    def upsert_ncm_allowlist(self, **kwargs):
        self.upserts.append(kwargs)
        return {
            "ncm_code": kwargs["ncm_code"],
            "ncm_version": kwargs["ncm_version"],
            "description": kwargs["description"],
            "family_code": kwargs["family_code"],
            "approved_by": kwargs["approved_by"],
            "approved_at": kwargs["approved_at"],
            "active": kwargs["active"],
        }


@pytest.fixture()
def storage_on(monkeypatch):
    monkeypatch.setattr(
        Settings, "plugins_db_configured", classmethod(lambda cls: True)
    )


def _wire(monkeypatch, repo):
    ctx = _FakeConnCtx()
    monkeypatch.setattr(mda, "get_connection", lambda: ctx)
    monkeypatch.setattr(mda, "check_market_contract_ready", lambda conn: None)
    monkeypatch.setattr(
        mda, "_repo", lambda conn: repo
    )
    return ctx


def test_invalid_ncm_code_rejected():
    with pytest.raises(InvalidQueryError):
        mda.upsert_ncm_allowlist(
            ncm_code="8544.49.00", body={"description": "x"}, actor="supplies-api"
        )
    with pytest.raises(InvalidQueryError):
        mda.upsert_ncm_allowlist(
            ncm_code="1234567", body={}, actor="supplies-api"
        )


def test_create_requires_description(storage_on, monkeypatch):
    repo = _FakeRepo(existing=None)
    _wire(monkeypatch, repo)
    with pytest.raises(InvalidQueryError):
        mda.upsert_ncm_allowlist(
            ncm_code="74081190", body={"ncm_version": "NCM 2022"}, actor="s"
        )
    assert repo.upserts == []


def test_create_defaults_ncm_version_to_current_revision(
    storage_on, monkeypatch
):
    repo = _FakeRepo(existing=None)
    _wire(monkeypatch, repo)
    payload = mda.upsert_ncm_allowlist(
        ncm_code="74081190", body={"description": "Fios de cobre"}, actor="s"
    )
    assert payload["created"] is True
    assert repo.upserts[0]["ncm_version"] == "2022"
    assert payload["allowlist_entry"]["ncm_version"] == "2022"


def test_create_persists_and_commits(storage_on, monkeypatch):
    repo = _FakeRepo(existing=None)
    ctx = _wire(monkeypatch, repo)
    payload = mda.upsert_ncm_allowlist(
        ncm_code="74081190",
        body={
            "description": "Fios de cobre refinado",
            "ncm_version": "NCM 2022",
            "family_code": "copper",
            "approved_by": "fiscal.user@delpi",
            "active": True,
        },
        actor="supplies-api",
    )
    assert payload["created"] is True
    assert payload["synced_by"] == "supplies-api"
    assert payload["allowlist_entry"]["ncm_code"] == "74081190"
    assert payload["allowlist_entry"]["active"] is True
    assert ctx.committed is True
    assert repo.upserts[0]["ncm_version"] == "NCM 2022"


def test_deactivation_keeps_fields(storage_on, monkeypatch):
    existing = {
        "ncm_code": "74081190",
        "ncm_version": "NCM 2022",
        "description": "Fios de cobre refinado",
        "family_code": "copper",
        "approved_by": "fiscal.user@delpi",
        "approved_at": None,
        "active": True,
    }
    repo = _FakeRepo(existing=existing)
    _wire(monkeypatch, repo)
    payload = mda.upsert_ncm_allowlist(
        ncm_code="74081190", body={"active": False}, actor="supplies-api"
    )
    assert payload["created"] is False
    assert payload["allowlist_entry"]["active"] is False
    assert repo.upserts[0]["description"] == "Fios de cobre refinado"
    assert repo.upserts[0]["ncm_version"] == "NCM 2022"


def test_update_without_active_flag_preserves_state(storage_on, monkeypatch):
    existing = {
        "ncm_code": "74081190",
        "ncm_version": "NCM 2022",
        "description": "old",
        "family_code": None,
        "approved_by": None,
        "approved_at": None,
        "active": False,
    }
    repo = _FakeRepo(existing=existing)
    _wire(monkeypatch, repo)
    payload = mda.upsert_ncm_allowlist(
        ncm_code="74081190",
        body={"description": "new"},
        actor="supplies-api",
    )
    assert payload["allowlist_entry"]["active"] is False


def test_non_boolean_active_rejected(storage_on, monkeypatch):
    _wire(monkeypatch, _FakeRepo())
    with pytest.raises(InvalidQueryError):
        mda.upsert_ncm_allowlist(
            ncm_code="74081190", body={"active": "yes"}, actor="s"
        )


def test_fails_closed_without_storage(monkeypatch):
    monkeypatch.setattr(
        Settings, "plugins_db_configured", classmethod(lambda cls: False)
    )
    with pytest.raises(StorageUnavailableError):
        mda.upsert_ncm_allowlist(
            ncm_code="74081190",
            body={"description": "x", "ncm_version": "y"},
            actor="s",
        )


def test_contract_not_ready_propagates(storage_on, monkeypatch):
    ctx = _FakeConnCtx()
    monkeypatch.setattr(mda, "get_connection", lambda: ctx)

    def _boom(conn):
        raise ContractNotReadyError("pending")

    monkeypatch.setattr(mda, "check_market_contract_ready", _boom)
    with pytest.raises(ContractNotReadyError):
        mda.upsert_ncm_allowlist(
            ncm_code="74081190",
            body={"description": "x", "ncm_version": "y"},
            actor="s",
        )
