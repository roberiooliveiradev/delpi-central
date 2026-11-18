"""Pilot readiness matrix parser tests; never authorizes operations."""
from __future__ import annotations

import json

import pytest

from linux_ops_mcp.atlas_hml_b_pilot_readiness import (
    HMLPilotReadinessError,
    review_untrusted_pilot_readiness,
)


def _payload(**changes):
    document = {
        "schema": "atlas.hml.b.pilot-readiness.v1",
        "source": "operator_supplied_untrusted",
        "host": "srv-api",
        "environment": "hml",
        "architecture": "B",
        "matrix": {
            "implemented_and_proven_in_ci": ["local-signer", "envelope-ed25519"],
            "proven_only_in_disposable_fixtures": ["continuity-store", "uds-presenter"],
            "requires_real_linux_observation": ["systemd-uid-fd", "lsm"],
            "requires_explicit_authorization": ["install-units", "create-users"],
            "risk_accepted_by_owner": ["root-docker-producer", "local-key-same-host"],
            "unproven_residual_risk": ["flock-advisory", "bootstrap-ambiguity"],
        },
        "owner_risk_acceptances": [
            "OWNER_GOVERNANCE_DECISIONS",
            "ROOT_DOCKER_PRODUCER_RISK_ACCEPTED",
            "LOCAL_ED25519_SAME_HOST_KEY_RISK_ACCEPTED",
            "EXTERNAL_SIGNER_DEFERRED",
            "ARCHITECTURE_B_FOR_HML_PILOT",
        ],
        "governance_exception_pending": True,
        "prepare_eligible_claim": False,
        "can_execute_claim": False,
    }
    document.update(changes)
    return json.dumps(document, separators=(",", ":"), sort_keys=True).encode()


def test_readiness_always_blocked_and_not_sec01():
    review = review_untrusted_pilot_readiness(_payload())
    assert review.status == "blocked"
    assert review.categories_reviewed == 6
    assert not review.independent_sec01_attested
    assert not review.operational_authorization_granted
    assert not review.prepare_eligible and not review.can_execute
    assert review.governance_exception_pending
    assert "OWNER_RISK_ACCEPTANCE_IS_NOT_INDEPENDENT_SEC01" in review.blocks


def test_prepare_claim_true_is_denied():
    with pytest.raises(HMLPilotReadinessError) as err:
        review_untrusted_pilot_readiness(_payload(prepare_eligible_claim=True))
    assert err.value.code == "HML_PILOT_SCOPE_DENIED"
