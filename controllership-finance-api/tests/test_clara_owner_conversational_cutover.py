"""CF-UX-053: owner-accepted conversational batch channel, without forged ack.

No business records are touched: persistence and audit are mocked.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from controllership_finance_app.application.clara import consent_channel as cc
from controllership_finance_app.application.clara import batch_orchestrator as batch_mod
from controllership_finance_app.application.clara.step_up_consent import (
    ConsentRequired,
)


@pytest.fixture()
def batch(monkeypatch):
    monkeypatch.setattr(batch_mod, "_audit_mcp", lambda **kw: None)
    proposals = MagicMock()
    batches = MagicMock()
    batches.record_consent.return_value = {
        "batch_id": "22222222-2222-2222-2222-222222222222",
        "status": "CONFIRMED",
        "confirmed_at": datetime.now(timezone.utc),
    }
    batches.load_by_handle.return_value = {
        "batch_id": "22222222-2222-2222-2222-222222222222",
        "status": "PREPARED",
        "actor_sub": "actor-1",
        "consent_record": None,
    }
    orch = batch_mod.ClaraBatchOrchestrator(
        batches=batches, proposals=proposals, writes=MagicMock()
    )
    return orch, batches


def test_conversational_batch_confirm_records_typed_policy(monkeypatch, batch):
    monkeypatch.setattr(cc.settings, "CLARA_CONSENT_CHANNEL", "conversational")
    orch, batches = batch
    outcome = orch.confirm_batch(
        handle="sealed-handle",
        actor_sub="actor-1",
        plan_hash="ab" * 32,
        confirmation=True,
    )
    assert outcome["status"] == "CONFIRMED"
    assert outcome["consent_mode"] == "MCP_CONFIRMATION"
    kw = batches.record_consent.call_args.kwargs
    assert kw["actor_sub"] == "actor-1"
    assert kw["plan_hash"] == "ab" * 32
    assert kw["mode"] == "MCP_CONFIRMATION"
    record = kw["consent_record"]
    assert record["confirmed_by"] == "actor-1"
    assert record["type"] == "mcp_tool_confirmation"
    assert record["confirmation_policy"] == cc.CONVERSATIONAL_POLICY_VERSION
    assert record["consent_channel"] == "conversational"
    assert "security_ack" not in record


@pytest.mark.parametrize("channel,confirmation", [
    ("portal", True),
    ("dual", True),
    ("conversational", False),
])
def test_batch_rejects_missing_or_portal_only_confirmation(
    monkeypatch, batch, channel, confirmation
):
    monkeypatch.setattr(cc.settings, "CLARA_CONSENT_CHANNEL", channel)
    orch, batches = batch
    with pytest.raises(ConsentRequired):
        orch.confirm_batch(
            handle="sealed-handle",
            actor_sub="actor-1",
            plan_hash="ab" * 32,
            confirmation=confirmation,
        )
    batches.record_consent.assert_not_called()
