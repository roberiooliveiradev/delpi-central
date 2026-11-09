"""CF-UX-053 — consent channel policy and TÉO-shaped confirmation gate.

Default remains Portal V014; explicit server-side conversational selection
enables the owner-accepted TÉO policy. The MCP signal is not V014 proof.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from controllership_finance_app.application.clara import consent_channel as cc
from controllership_finance_app.application.clara.governed_writes import (
    ClaraGovernedWrites,
)
from controllership_finance_app.application.clara.step_up_consent import (
    ConsentRequired,
)


@pytest.fixture()
def channel_settings(monkeypatch):
    monkeypatch.setattr(cc.settings, "CLARA_CONSENT_CHANNEL", "portal")
    monkeypatch.setattr(
        cc.settings, "CLARA_CONVERSATIONAL_SECURITY_ACK", ""
    )
    return cc.settings


def test_default_channel_is_portal(channel_settings):
    assert cc.consent_channel() == "portal"
    assert cc.portal_consent_required() is True
    assert cc.conversational_act_enabled() is False
    assert cc.prepare_status() == "proposal_pending_confirmation"


def test_conversational_explicit_channel_needs_no_signature(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    assert cc.conversational_act_enabled() is True
    assert cc.portal_consent_required() is False
    assert "confirmation=true" in cc.confirmation_instruction_for_prepare()
    assert "acknowledgement" not in cc.confirmation_instruction_for_prepare()


def test_legacy_ack_cannot_activate_portal(channel_settings):
    # Obsolete string never turns a Portal deployment into conversational.
    channel_settings.CLARA_CONVERSATIONAL_SECURITY_ACK = (
        "R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED"
    )
    assert cc.conversational_act_enabled() is False
    assert cc.portal_consent_required() is True


def test_dual_keeps_portal_requirement(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "dual"
    assert cc.conversational_act_enabled() is False
    assert cc.portal_consent_required() is True


def test_invalid_channel_falls_back_to_portal(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "whatever"
    assert cc.consent_channel() == "portal"


def test_phase_policy_default_mentions_portal_and_teo(channel_settings):
    policy = cc.phase_policy_for_capability(direct=False)
    assert "proposal_pending_confirmation" in policy
    assert "confirmation_url" in policy or "Portal" in policy
    assert "confirmation=true" in policy
    assert "portal_consent_required=true" in policy


def test_phase_policy_armed_omits_mandatory_portal(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    policy = cc.phase_policy_for_capability(direct=False)
    assert "sem página Portal obrigatória" in policy
    assert "confirmation=true" in policy


def test_phase_policy_direct_unchanged(channel_settings):
    policy = cc.phase_policy_for_capability(direct=True)
    assert "phase=direct" in policy


def _governed_for_consent() -> ClaraGovernedWrites:
    gw = ClaraGovernedWrites(
        proposals=MagicMock(),
        identity_provider=lambda: {"is_manage": True, "is_dre": False},
    )
    gw._challenges = MagicMock()
    gw._check_gate = lambda _cap: None  # type: ignore[method-assign]
    return gw


def _sealed_proposal(**over):
    base = {
        "proposal_id": "11111111-1111-1111-1111-111111111111",
        "actor_sub": "sub-1",
        "capability": "checklist.version_publish",
        "resource_type": "checklist_version",
        "resource_key": "v2",
        "payload": {
            "period": "2026-01",
            "version_id": "v2",
            "reason": "publicar",
        },
        "expected_state": {"status": "DRAFT"},
        "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "consent_record": None,
        "batch_operation_id": None,
        "execution_state": "PREPARED",
    }
    base.update(over)
    return base


def test_portal_commit_confirmation_true_alone_rejected(
    channel_settings, monkeypatch
):
    """Explicit portal mode rejects an MCP-only confirmation."""
    monkeypatch.setattr(
        "controllership_finance_app.application.clara.governed_writes."
        "present_operation",
        lambda cap, params: {
            "displayable": True,
            "summary": "publicar versão",
        },
    )
    gw = _governed_for_consent()
    sealed = _sealed_proposal()
    gw._proposals.load_any_for_actor.return_value = sealed
    with pytest.raises(ConsentRequired):
        gw.commit(
            handle="h-opaque",
            actor_sub="sub-1",
            confirmation=True,
        )
    gw._proposals.record_consent.assert_not_called()
    gw._proposals.claim.assert_not_called()


def test_commit_explicit_conversational_records_mcp_consent(
    channel_settings, monkeypatch
):
    from controllership_finance_app.application.clara.governed_writes import (
        UnknownCapability,
    )
    from controllership_finance_app.application.clara.step_up_consent import (
        proposal_plan_hash,
    )

    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    monkeypatch.setattr(
        "controllership_finance_app.application.clara.governed_writes."
        "present_operation",
        lambda cap, params: {
            "displayable": True,
            "summary": "publicar versão",
        },
    )
    gw = _governed_for_consent()
    sealed = _sealed_proposal()
    plan_hash = proposal_plan_hash(
        sealed["capability"],
        sealed["payload"],
        sealed["expected_state"],
    )

    def _load(*, handle, actor_sub):
        if gw._proposals.record_consent.called:
            return {
                **sealed,
                "consent_record": {
                    "type": "mcp_tool_confirmation",
                    "confirmed_by": "sub-1",
                    "confirmation_policy": cc.CONVERSATIONAL_POLICY_VERSION,
                    "consent_channel": "conversational",
                    "plan_hash": plan_hash,
                },
            }
        return sealed

    gw._proposals.load_any_for_actor = MagicMock(side_effect=_load)
    gw._proposals.claim.return_value = {
        **sealed,
        "consent_record": {
            "type": "mcp_tool_confirmation",
            "confirmed_by": "sub-1",
            "confirmation_policy": cc.CONVERSATIONAL_POLICY_VERSION,
            "consent_channel": "conversational",
            "plan_hash": plan_hash,
        },
    }
    gw._capability_table = lambda: {}  # type: ignore[method-assign]
    gw._proposals.record_result.return_value = None

    with pytest.raises(UnknownCapability):
        # Consent gate passed; empty capability table proves ACT entered.
        gw.commit(
            handle="h-opaque",
            actor_sub="sub-1",
            confirmation=True,
        )

    assert gw._proposals.record_consent.called
    consent = gw._proposals.record_consent.call_args.kwargs["consent_record"]
    assert consent["type"] == "mcp_tool_confirmation"
    assert consent["confirmation_policy"] == cc.CONVERSATIONAL_POLICY_VERSION
    assert consent["consent_channel"] == "conversational"
    assert "security_ack" not in consent
    assert consent["plan_hash"] == plan_hash


def test_commit_conversational_without_confirmation_flag_rejected(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    gw = _governed_for_consent()
    gw._proposals.load_any_for_actor.return_value = _sealed_proposal()
    with pytest.raises(ConsentRequired) as exc:
        gw.commit(handle="h-opaque", actor_sub="sub-1", confirmation=False)
    assert "confirmation=true" in str(exc.value)
    gw._proposals.claim.assert_not_called()



@pytest.mark.parametrize(
    "record_override",
    [
        {"confirmed_by": "another-actor"},
        {"plan_hash": "invalid-hash"},
        {"consent_channel": "portal"},
        {"confirmation_policy": "legacy-ack"},
    ],
)
def test_conversational_record_must_match_sealed_actor_plan_and_policy(
    channel_settings, record_override
):
    from controllership_finance_app.application.clara.step_up_consent import (
        proposal_plan_hash,
    )

    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    proposal = _sealed_proposal()
    record = {
        "type": "mcp_tool_confirmation",
        "confirmed_by": "sub-1",
        "plan_hash": proposal_plan_hash(
            proposal["capability"], proposal["payload"], proposal["expected_state"]
        ),
        "consent_channel": "conversational",
        "confirmation_policy": cc.CONVERSATIONAL_POLICY_VERSION,
    }
    record.update(record_override)
    proposal["consent_record"] = record
    gw = _governed_for_consent()
    with pytest.raises(ConsentRequired):
        gw._require_consent(proposal)
