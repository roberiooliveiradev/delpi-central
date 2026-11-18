"""Rollback baseline review and disposable simulation tests."""
from __future__ import annotations

import json

import pytest

from linux_ops_mcp.atlas_hml_b_rollback_review import (
    HMLRollbackReviewError,
    review_untrusted_rollback_baseline,
    simulate_rollback_in_fixture,
)

_COMPONENTS = [
    "atlas-hml-snapshot-presenter.service.review",
    "atlas-hml-snapshot-presenter.socket.review",
    "atlas-hml-snapshot-producer.service.review",
    "atlas-hml-snapshot-producer.timer.review",
    "atlas-hml-readonly.directory.review",
]


def _baseline(**changes):
    document = {
        "schema": "atlas.hml.b.rollback-baseline.v1",
        "source": "operator_supplied_untrusted",
        "host": "srv-api",
        "environment": "hml",
        "architecture": "B",
        "baseline_id": "BASELINE01ATLASB",
        "components": list(_COMPONENTS),
        "non_atlas_services_untouched": True,
        "abort_conditions": [
            "DOCKER_ENGINE_IMPACT_DETECTED",
            "NON_ATLAS_UNIT_MUTATION_DETECTED",
            "PARTIAL_INSTALL_WITHOUT_ROLLBACK_PATH",
            "SEC_GATE_INCOMPLETE",
            "CHANGE_CONTROL_MISSING",
        ],
        "partial_failure_plan": "stop-new-only-leave-existing-services",
        "sec_matrix_refs": [f"SEC-{n:02d}" for n in range(1, 11)],
    }
    document.update(changes)
    return json.dumps(document, separators=(",", ":"), sort_keys=True).encode()


def test_review_always_blocked_even_with_complete_claims():
    review = review_untrusted_rollback_baseline(_baseline())
    assert review.status == "blocked"
    assert not review.host_rollback_attested
    assert not review.operational_authorization_granted
    assert not review.prepare_eligible and not review.can_execute
    assert len(review.baseline.sec_matrix_refs) == 10
    assert "NO_HOST_ROLLBACK_EXECUTED" in review.blocks


def test_simulation_rolls_back_only_atlas_fixture_components():
    review = review_untrusted_rollback_baseline(_baseline())
    installed = frozenset(_COMPONENTS[:2])
    result = simulate_rollback_in_fixture(review, installed=installed)
    assert result.rolled_back_components == tuple(sorted(installed))
    assert not result.host_mutated and not result.can_execute


def test_simulation_aborts_on_docker_impact_without_host_mutation():
    review = review_untrusted_rollback_baseline(_baseline())
    result = simulate_rollback_in_fixture(
        review,
        installed=frozenset(_COMPONENTS),
        abort_reason="DOCKER_ENGINE_IMPACT_DETECTED",
    )
    assert result.aborted and result.abort_reason == "DOCKER_ENGINE_IMPACT_DETECTED"
    assert not result.host_mutated


def test_non_atlas_component_rejected():
    review = review_untrusted_rollback_baseline(_baseline())
    with pytest.raises(HMLRollbackReviewError) as err:
        simulate_rollback_in_fixture(
            review, installed=frozenset({"nginx.service"}),
        )
    assert err.value.code == "HML_ROLLBACK_NON_ATLAS_COMPONENT"
