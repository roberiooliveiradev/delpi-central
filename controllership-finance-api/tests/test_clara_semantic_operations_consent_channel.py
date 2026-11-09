"""CF-UX-053: operations batch must reflect active consent policy.

No business mutation: governed writes and planning are mocked.
"""

from unittest.mock import MagicMock

import pytest

from controllership_finance_app.application.clara import consent_channel as cc
from controllership_finance_app.interface.mcp import semantic_bridge as sb


@pytest.mark.parametrize(
    "channel,ack,portal_required",
    [
        ("portal", "", True),
        ("conversational", "", True),
        ("conversational", cc.SECURITY_ACK_VALUE, False),
    ],
)
def test_operations_batch_advertises_actual_consent_channel(
    monkeypatch, channel, ack, portal_required
):
    monkeypatch.setattr(cc.settings, "CLARA_CONSENT_CHANNEL", channel)
    monkeypatch.setattr(cc.settings, "CLARA_CONVERSATIONAL_SECURITY_ACK", ack)
    gw = MagicMock()
    gw._capability_table.return_value = {
        "checklist.version_publish": {"direct": False}
    }
    gw.prepare.return_value = {
        "operation": "publish v2",
        "proposal_id": "proposal-1",
        "proposal_handle": "sealed-1",
        "confirmation_url": "/apps/controllership-finance/closing/clara-consent?proposal=proposal-1",
        "expires_at": "2026-11-09T18:00:00Z",
    }
    orch = MagicMock()
    orch.plan_batch.return_value = {
        "plan_hash": "plan-1",
        "operations": [
            {
                "index": 0,
                "capability": "checklist.version_publish",
                "resource_type": "checklist_template_version",
                "params": {"template_id": "template", "version": 2},
                "status": "viable",
                "depends_on": [],
            }
        ],
    }
    monkeypatch.setattr(sb, "_governed_writes", lambda: gw)
    monkeypatch.setattr(sb, "_batch_orchestrator", lambda: orch)
    monkeypatch.setattr(sb, "_ok", lambda payload: payload)

    result = sb._run_operations(
        {
            "operations": [
                {
                    "capability": "checklist.version_publish",
                    "params": {"template_id": "template", "version": 2},
                }
            ]
        },
        "user-1",
    )

    operation = result["operations"][0]
    assert operation["status"] == "pending_confirmation"
    assert operation["proposal_handle"] == "sealed-1"
    assert operation["portal_consent_required"] is portal_required
    assert operation["conversational_act_armed"] is (
        channel == "conversational" and bool(ack)
    )
    assert ("confirmation_url" in operation) is portal_required
    if portal_required:
        assert "Portal" in result["note"]
    else:
        assert "confirmation=true" in result["note"]
        assert "aguarde confirmação explícita" in result["note"]
    gw.prepare.assert_called_once()
    gw.execute_direct.assert_not_called()
