"""Lifecycle supervisor library tests; no services started."""
from __future__ import annotations

import pytest

from linux_ops_mcp.atlas_hml_b_lifecycle import (
    HMLLifecycleError,
    HMLLifecycleLimits,
    HMLLifecycleState,
    HMLLifecycleSupervisor,
)


def test_happy_path_available_observe_and_stop():
    supervisor = HMLLifecycleSupervisor()
    assert supervisor.state is HMLLifecycleState.INIT
    diag = supervisor.mark_available()
    assert diag.status == "blocked" and diag.state is HMLLifecycleState.AVAILABLE
    assert not diag.fallback_to_raw_docker and not diag.can_execute
    supervisor.begin_observe()
    supervisor.end_observe()
    stopped = supervisor.request_stop()
    assert stopped.reason == "SHUTDOWN"
    assert supervisor.state is HMLLifecycleState.STOPPED


def test_backpressure_and_timeout_limits():
    supervisor = HMLLifecycleSupervisor(HMLLifecycleLimits(max_inflight=1))
    supervisor.mark_available()
    supervisor.begin_observe()
    with pytest.raises(HMLLifecycleError) as err:
        supervisor.begin_observe()
    assert err.value.code == "HML_LIFECYCLE_BACKPRESSURE"
    supervisor.end_observe()


def test_integrity_compromise_blocks_recovery_permanently():
    supervisor = HMLLifecycleSupervisor()
    supervisor.mark_available()
    diag = supervisor.mark_integrity_compromised()
    assert diag.state is HMLLifecycleState.RECOVERY_BLOCKED
    assert diag.reason == "INTEGRITY_COMPROMISED"
    assert not diag.privileged_recovery
    with pytest.raises(HMLLifecycleError) as err:
        supervisor.attempt_recovery()
    assert err.value.code == "HML_LIFECYCLE_RECOVERY_BLOCKED"
    with pytest.raises(HMLLifecycleError):
        supervisor.mark_available()


def test_failure_does_not_enable_prepare_or_docker_fallback():
    supervisor = HMLLifecycleSupervisor()
    supervisor.mark_available()
    failed = supervisor.mark_failure("PRODUCER_FAILED")
    assert failed.state is HMLLifecycleState.FAILED
    assert not failed.fallback_to_raw_docker
    assert not failed.fallback_to_prod
    assert not failed.prepare_eligible and not failed.can_execute
