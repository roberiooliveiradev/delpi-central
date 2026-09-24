"""commit_now additive behavior on GovernedActionsFacade (mocked orchestrator)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import Request

from tm_app.application.governed_writes.errors import GovernedWriteError
from tm_app.application.governed_writes.idempotency_store import clear_idempotency_store
from tm_app.application.gpt_actions.governed_actions_facade import GovernedActionsFacade


@pytest.fixture(autouse=True)
def _clear_idem():
    clear_idempotency_store()
    yield
    clear_idempotency_store()


def _request() -> Request:
    scope = {"type": "http", "headers": []}
    req = Request(scope)
    req.state.user = SimpleNamespace(id="user-1", email="u@example.com")
    return req


def _facade_with_mocks():
    orch = MagicMock()
    facade = GovernedActionsFacade(orchestrator=orch)
    return facade, orch


def test_prepare_without_commit_now_does_not_act(monkeypatch):
    facade, orch = _facade_with_mocks()
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.entity_supports",
        lambda *_a, **_k: True,
    )
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.parse_entity",
        lambda e: e,
    )
    orch.prepare.return_value = {
        "proposal_handle": "h1",
        "proposal_id": "p1",
        "capability": "create_record",
        "resource_type": "process",
        "resource_id": None,
        "exact_change": {},
        "confirmation_requirement": {"explicit_user_confirmation": True},
        "expected_postcondition": {},
        "expires_at": None,
        "act_allowed": True,
        "ready": True,
        "validation_result": {"ready": True},
        "consequential_impact": {},
    }
    out = facade.prepare_record_change(
        _request(),
        entity="process",
        operation="create",
        changes={"nome": "x"},
        commit_now=False,
    )
    assert out["persisted"] is False
    assert out["commit_now_applied"] is False
    orch.act.assert_not_called()


def test_commit_now_create_persists(monkeypatch):
    facade, orch = _facade_with_mocks()
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.entity_supports",
        lambda *_a, **_k: True,
    )
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.parse_entity",
        lambda e: e,
    )
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade._actor",
        lambda _r: ("user-1", "u@example.com"),
    )
    orch.prepare.return_value = {
        "proposal_handle": "h1",
        "proposal_id": "p1",
        "capability": "create_record",
        "resource_type": "process",
        "resource_id": None,
        "exact_change": {},
        "confirmation_requirement": {},
        "expected_postcondition": {},
        "expires_at": None,
        "act_allowed": True,
        "ready": True,
        "validation_result": {"ready": True},
        "consequential_impact": {},
    }
    orch.act.return_value = {
        "verified": True,
        "capability": "create_record",
        "proposal_id": "p1",
        "data": {"id": "new"},
    }
    out = facade.prepare_record_change(
        _request(),
        entity="process",
        operation="create",
        changes={"nome": "x"},
        commit_now=True,
        confirmation=True,
        idempotency_key="k1",
    )
    assert out["persisted"] is True
    assert out["commit_now_applied"] is True
    orch.act.assert_called_once()


def test_commit_now_delete_ignored(monkeypatch):
    facade, orch = _facade_with_mocks()
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.entity_supports",
        lambda *_a, **_k: True,
    )
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.parse_entity",
        lambda e: e,
    )
    orch.prepare.return_value = {
        "proposal_handle": "h1",
        "proposal_id": "p1",
        "capability": "delete_record",
        "resource_type": "process",
        "resource_id": "id1",
        "exact_change": {},
        "confirmation_requirement": {},
        "expected_postcondition": {},
        "expires_at": None,
        "act_allowed": True,
        "ready": True,
        "validation_result": {"ready": True},
        "consequential_impact": {},
    }
    out = facade.prepare_record_change(
        _request(),
        entity="process",
        operation="delete",
        record_id="id1",
        commit_now=True,
        confirmation=True,
        idempotency_key="k-del",
    )
    assert out["persisted"] is False
    assert out["commit_now_applied"] is False
    assert "ignored" in (out.get("message") or "").lower()
    orch.act.assert_not_called()


def test_commit_now_requires_confirmation_and_key(monkeypatch):
    facade, orch = _facade_with_mocks()
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.entity_supports",
        lambda *_a, **_k: True,
    )
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.parse_entity",
        lambda e: e,
    )
    orch.prepare.return_value = {
        "proposal_handle": "h1",
        "proposal_id": "p1",
        "capability": "create_record",
        "resource_type": "process",
        "resource_id": None,
        "exact_change": {},
        "confirmation_requirement": {},
        "expected_postcondition": {},
        "expires_at": None,
        "act_allowed": True,
        "ready": True,
        "validation_result": {"ready": True},
        "consequential_impact": {},
    }
    with pytest.raises(GovernedWriteError) as exc:
        facade.prepare_record_change(
            _request(),
            entity="process",
            operation="create",
            changes={"nome": "x"},
            commit_now=True,
            confirmation=False,
            idempotency_key="k1",
        )
    assert exc.value.data.get("error_code") == "CONFIRMATION_REQUIRED"

    with pytest.raises(GovernedWriteError) as exc2:
        facade.prepare_record_change(
            _request(),
            entity="process",
            operation="create",
            changes={"nome": "x"},
            commit_now=True,
            confirmation=True,
            idempotency_key=None,
        )
    assert exc2.value.data.get("error_code") == "IDEMPOTENCY_KEY_REQUIRED"


def test_commit_now_idempotent_retry(monkeypatch):
    facade, orch = _facade_with_mocks()
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.entity_supports",
        lambda *_a, **_k: True,
    )
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade.parse_entity",
        lambda e: e,
    )
    monkeypatch.setattr(
        "tm_app.application.gpt_actions.governed_actions_facade._actor",
        lambda _r: ("user-1", "u@example.com"),
    )
    orch.prepare.return_value = {
        "proposal_handle": "h1",
        "proposal_id": "p1",
        "capability": "create_record",
        "resource_type": "process",
        "resource_id": None,
        "exact_change": {},
        "confirmation_requirement": {},
        "expected_postcondition": {},
        "expires_at": None,
        "act_allowed": True,
        "ready": True,
        "validation_result": {"ready": True},
        "consequential_impact": {},
    }
    orch.act.return_value = {
        "verified": True,
        "capability": "create_record",
        "proposal_id": "p1",
        "data": {"id": "new"},
    }
    req = _request()
    first = facade.prepare_record_change(
        req,
        entity="process",
        operation="create",
        changes={"nome": "x"},
        commit_now=True,
        confirmation=True,
        idempotency_key="same-key",
    )
    second = facade.prepare_record_change(
        req,
        entity="process",
        operation="create",
        changes={"nome": "x"},
        commit_now=True,
        confirmation=True,
        idempotency_key="same-key",
    )
    assert first["persisted"] and second["persisted"]
    assert orch.act.call_count == 1
