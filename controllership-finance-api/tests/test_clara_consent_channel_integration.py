"""CF-UX-053 integration regressions: no unused V014 challenge in chat mode.

All writes are mocked. The authorization gate and user are not bypassed.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from controllership_finance_app.application.clara import consent_channel as cc
from controllership_finance_app.application.clara.governed_writes import (
    ClaraGovernedWrites,
)
from controllership_finance_app.interface.http.routes import clara_consent_routes as routes


@pytest.mark.parametrize(
    "channel,ack,expected_challenges",
    [
        ("portal", "", 1),
        ("conversational", "", 1),
        ("conversational", cc.SECURITY_ACK_VALUE, 0),
    ],
)
def test_prepare_only_issues_portal_challenge_when_required(
    monkeypatch, channel, ack, expected_challenges
):
    monkeypatch.setattr(cc.settings, "CLARA_CONSENT_CHANNEL", channel)
    monkeypatch.setattr(cc.settings, "CLARA_CONVERSATIONAL_SECURITY_ACK", ack)
    proposals = MagicMock()
    proposals.create.return_value = {
        "proposal_id": "11111111-1111-1111-1111-111111111111",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    gw = ClaraGovernedWrites(
        proposals=proposals,
        identity_provider=lambda: {"is_manage": True},
    )
    gw._challenges = MagicMock()
    gw._capability_table = lambda: {
        "checklist.version_publish": {
            "required_params": ("version",),
            "resource_type": "checklist_version",
            "resource_key": lambda params: str(params["version"]),
            "describe": lambda params: "Publicar versao",
        },
    }
    gw._check_gate = lambda cap: None
    gw._snapshot = lambda cap, params: {"status": "REVIEW"}
    result = gw.prepare(
        capability="checklist.version_publish",
        params={"version": 2},
        actor_sub="actor-1",
    )
    assert result["portal_consent_required"] is bool(expected_challenges)
    assert gw._challenges.issue_for_proposal.call_count == expected_challenges
    assert bool(result["confirmation_url"]) is bool(expected_challenges)
    proposals.create.assert_called_once()


@pytest.mark.parametrize(
    "channel,ack,expected_portal",
    [
        ("portal", "", True),
        ("conversational", "", True),
        ("conversational", cc.SECURITY_ACK_VALUE, False),
    ],
)
def test_authenticated_policy_endpoint_reflects_backend_gate(
    monkeypatch, channel, ack, expected_portal
):
    monkeypatch.setattr(cc.settings, "CLARA_CONSENT_CHANNEL", channel)
    monkeypatch.setattr(cc.settings, "CLARA_CONVERSATIONAL_SECURITY_ACK", ack)
    monkeypatch.setattr(routes, "_actor", lambda request: "actor-1")
    monkeypatch.setattr(
        routes, "ok", lambda payload, operation_id: {"data": payload}
    )
    result = routes.get_clara_consent_policy(MagicMock())["data"]
    assert set(result) == {
        "consent_channel",
        "portal_consent_required",
        "conversational_act_armed",
    }
    assert result["consent_channel"] == channel
    assert result["portal_consent_required"] is expected_portal
    assert result["conversational_act_armed"] is not expected_portal
    assert cc.SECURITY_ACK_VALUE not in repr(result)


def test_policy_endpoint_rejects_request_without_user():
    class _State:
        user = None

    request = MagicMock()
    request.state = _State()
    with pytest.raises(Exception, match="Unauthorized"):
        routes.get_clara_consent_policy(request)


@pytest.mark.parametrize(
    "channel,ack,expected_challenges",
    [
        ("portal", "", 1),
        ("conversational", "", 1),
        ("conversational", cc.SECURITY_ACK_VALUE, 0),
    ],
)
def test_prepare_batch_only_issues_portal_challenge_when_required(
    monkeypatch, channel, ack, expected_challenges
):
    monkeypatch.setattr(cc.settings, "CLARA_CONSENT_CHANNEL", channel)
    monkeypatch.setattr(cc.settings, "CLARA_CONVERSATIONAL_SECURITY_ACK", ack)
    from controllership_finance_app.application.clara import (
        batch_orchestrator as batch_mod,
    )

    monkeypatch.setattr(batch_mod, "_audit_mcp", lambda **_kwargs: None)
    proposals = MagicMock()
    batches = MagicMock()
    batches.create_batch.return_value = {
        "batch_id": "22222222-2222-2222-2222-222222222222",
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    orchestrator = batch_mod.ClaraBatchOrchestrator(
        proposals=proposals,
        batches=batches,
    )
    orchestrator._challenges = MagicMock()
    orchestrator.plan_batch = lambda **_kwargs: {
        "viable_count": 1,
        "blocked_count": 0,
        "plan_hash": "ab" * 32,
        "operations": [
            {
                "index": 0,
                "status": "viable",
                "capability": "checklist.version_publish",
                "resource_type": "checklist_version",
                "resource_key": "2",
                "params": {"version": 2},
                "expected_state": {"status": "REVIEW"},
                "depends_on": [],
                "description": "Publicar versao",
            }
        ],
    }
    result = orchestrator.prepare_batch(
        operations=[
            {
                "capability": "checklist.version_publish",
                "params": {"version": 2},
            }
        ],
        actor_sub="actor-1",
    )
    assert result["portal_consent_required"] is bool(expected_challenges)
    assert (
        orchestrator._challenges.issue_for_batch.call_count
        == expected_challenges
    )
    assert bool(result["confirmation_url"]) is bool(expected_challenges)
