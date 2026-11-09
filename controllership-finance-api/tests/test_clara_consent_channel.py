"""CF-UX-053 — consent channel policy and TÉO-shaped confirmation gate.

Default remains Portal V014. confirmation=true alone never authorizes
unless the Security acknowledgement arms conversational ACT.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from controllership_finance_app.application.clara import consent_channel as cc
from controllership_finance_app.application.clara.consent_channel import (
    SECURITY_ACK_VALUE,
)
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


def test_conversational_without_ack_keeps_portal(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    assert cc.conversational_act_enabled() is False
    assert cc.portal_consent_required() is True
    assert "confirmation_url" in cc.confirmation_instruction_for_prepare()


def test_conversational_with_wrong_ack_keeps_portal(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    channel_settings.CLARA_CONVERSATIONAL_SECURITY_ACK = "yes"
    assert cc.conversational_act_enabled() is False
    assert cc.portal_consent_required() is True


def test_conversational_armed_only_with_exact_ack(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    channel_settings.CLARA_CONVERSATIONAL_SECURITY_ACK = SECURITY_ACK_VALUE
    assert cc.conversational_act_enabled() is True
    assert cc.portal_consent_required() is False
    instruction = cc.confirmation_instruction_for_prepare()
    assert "confirmation=true" in instruction
    assert "armado" in instruction.lower() or "acknowledgement" in instruction


def test_dual_with_ack_keeps_portal_url_requirement(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "dual"
    channel_settings.CLARA_CONVERSATIONAL_SECURITY_ACK = SECURITY_ACK_VALUE
    assert cc.conversational_act_enabled() is True
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
    channel_settings.CLARA_CONVERSATIONAL_SECURITY_ACK = SECURITY_ACK_VALUE
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


def test_commit_confirmation_true_alone_rejected_without_ack(
    channel_settings, monkeypatch
):
    """CURRENT_RUNTIME: confirmation=true must not bypass V014."""
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


def test_commit_armed_conversational_records_mcp_consent(
    channel_settings, monkeypatch
):
    from controllership_finance_app.application.clara.governed_writes import (
        UnknownCapability,
    )
    from controllership_finance_app.application.clara.step_up_consent import (
        proposal_plan_hash,
    )

    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    channel_settings.CLARA_CONVERSATIONAL_SECURITY_ACK = SECURITY_ACK_VALUE
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
                    "security_ack": True,
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
            "security_ack": True,
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
    assert consent["security_ack"] is True
    assert consent["plan_hash"] == plan_hash


def test_commit_armed_without_confirmation_flag_rejected(channel_settings):
    channel_settings.CLARA_CONSENT_CHANNEL = "conversational"
    channel_settings.CLARA_CONVERSATIONAL_SECURITY_ACK = SECURITY_ACK_VALUE
    gw = _governed_for_consent()
    gw._proposals.load_any_for_actor.return_value = _sealed_proposal()
    with pytest.raises(ConsentRequired) as exc:
        gw.commit(handle="h-opaque", actor_sub="sub-1", confirmation=False)
    assert "confirmation=true" in str(exc.value)
    gw._proposals.claim.assert_not_called()
