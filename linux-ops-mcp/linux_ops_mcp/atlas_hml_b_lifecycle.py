"""Reusable lifecycle/supervision contracts for ATLAS B (library only).

Models initialization, availability, failure, stop and recovery-blocked
states with timeouts, concurrency limits and sanitized diagnostics.
No launcher, systemd unit, MCP tool or host service is created here.
Failures never fall back to raw Docker, PROD or privileged operations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HMLLifecycleState(str, Enum):
    INIT = "init"
    AVAILABLE = "available"
    DEGRADED = "degraded"
    FAILED = "failed"
    STOPPED = "stopped"
    RECOVERY_BLOCKED = "recovery_blocked"


_ALLOWED = {
    HMLLifecycleState.INIT: frozenset({
        HMLLifecycleState.AVAILABLE, HMLLifecycleState.FAILED,
        HMLLifecycleState.STOPPED,
    }),
    HMLLifecycleState.AVAILABLE: frozenset({
        HMLLifecycleState.DEGRADED, HMLLifecycleState.FAILED,
        HMLLifecycleState.STOPPED, HMLLifecycleState.RECOVERY_BLOCKED,
    }),
    HMLLifecycleState.DEGRADED: frozenset({
        HMLLifecycleState.AVAILABLE, HMLLifecycleState.FAILED,
        HMLLifecycleState.STOPPED, HMLLifecycleState.RECOVERY_BLOCKED,
    }),
    HMLLifecycleState.FAILED: frozenset({
        HMLLifecycleState.STOPPED, HMLLifecycleState.RECOVERY_BLOCKED,
    }),
    HMLLifecycleState.STOPPED: frozenset({
        HMLLifecycleState.RECOVERY_BLOCKED,
    }),
    HMLLifecycleState.RECOVERY_BLOCKED: frozenset(),
}

_INTEGRITY_CODES = frozenset({
    "HML_SESSION_REPLAY_OR_REGRESSION",
    "HML_SESSION_INPLACE_MUTATION",
    "HML_TRUST_SIGNATURE_INVALID",
    "HML_CONTINUITY_STORE_CORRUPT",
    "HML_CONTINUITY_STORE_REPLAY",
    "HML_CONTINUITY_STORE_COUNTER_REGRESSION",
    "HML_PRESENTER_FD_BOUNDARY_DENIED",
    "HML_LIFECYCLE_INTEGRITY_COMPROMISED",
})

_SANITIZED = frozenset({
    "TIMEOUT", "BACKPRESSURE", "PRODUCER_FAILED", "SNAPSHOT_INVALID",
    "SNAPSHOT_MISSING", "SNAPSHOT_EXPIRED", "COMMUNICATION_FAILED",
    "INTEGRITY_COMPROMISED", "SHUTDOWN", "POLICY_DENIED", "INTERNAL",
})


class HMLLifecycleError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True, slots=True)
class HMLLifecycleLimits:
    observe_timeout_ms: int = 2_000
    communicate_timeout_ms: int = 2_000
    max_inflight: int = 1
    max_queue: int = 0

    def validate(self) -> None:
        if (
            type(self.observe_timeout_ms) is not int
            or not 1 <= self.observe_timeout_ms <= 60_000
            or type(self.communicate_timeout_ms) is not int
            or not 1 <= self.communicate_timeout_ms <= 60_000
            or type(self.max_inflight) is not int
            or not 1 <= self.max_inflight <= 8
            or type(self.max_queue) is not int
            or not 0 <= self.max_queue <= 8
        ):
            raise HMLLifecycleError("HML_LIFECYCLE_LIMITS_INVALID")


@dataclass(frozen=True, slots=True)
class HMLLifecycleDiagnostic:
    state: HMLLifecycleState
    reason: str
    status: str = "blocked"
    prepare_eligible: bool = False
    can_execute: bool = False
    fallback_to_raw_docker: bool = False
    fallback_to_prod: bool = False
    privileged_recovery: bool = False


class HMLLifecycleSupervisor:
    """Deterministic state machine for review/CI fixtures, not a runtime daemon."""

    def __init__(self, limits: HMLLifecycleLimits | None = None) -> None:
        self._limits = limits or HMLLifecycleLimits()
        self._limits.validate()
        self._state = HMLLifecycleState.INIT
        self._inflight = 0
        self._fault: str | None = None

    @property
    def state(self) -> HMLLifecycleState:
        return self._state

    @property
    def limits(self) -> HMLLifecycleLimits:
        return self._limits

    def diagnose(self, reason: str = "OK") -> HMLLifecycleDiagnostic:
        if type(reason) is not str or reason not in _SANITIZED and reason != "OK":
            reason = "INTERNAL"
        return HMLLifecycleDiagnostic(state=self._state, reason=reason)

    def _transition(self, target: HMLLifecycleState) -> None:
        if target not in _ALLOWED[self._state]:
            raise HMLLifecycleError("HML_LIFECYCLE_TRANSITION_DENIED")
        self._state = target

    def mark_available(self) -> HMLLifecycleDiagnostic:
        if self._fault is not None:
            raise HMLLifecycleError(self._fault)
        self._transition(HMLLifecycleState.AVAILABLE)
        return self.diagnose("OK")

    def begin_observe(self) -> None:
        if self._fault is not None:
            raise HMLLifecycleError(self._fault)
        if self._state not in {
            HMLLifecycleState.AVAILABLE, HMLLifecycleState.DEGRADED,
        }:
            raise HMLLifecycleError("HML_LIFECYCLE_NOT_AVAILABLE")
        if self._inflight >= self._limits.max_inflight:
            raise HMLLifecycleError("HML_LIFECYCLE_BACKPRESSURE")
        self._inflight += 1

    def end_observe(self) -> None:
        if self._inflight <= 0:
            raise HMLLifecycleError("HML_LIFECYCLE_CONCURRENCY_INVALID")
        self._inflight -= 1

    def mark_degraded(self, reason: str) -> HMLLifecycleDiagnostic:
        if reason not in _SANITIZED:
            reason = "INTERNAL"
        if self._fault is not None:
            raise HMLLifecycleError(self._fault)
        self._transition(HMLLifecycleState.DEGRADED)
        return self.diagnose(reason)

    def mark_failure(self, reason: str) -> HMLLifecycleDiagnostic:
        if reason not in _SANITIZED:
            reason = "INTERNAL"
        if reason == "INTEGRITY_COMPROMISED" or reason in {
            "SNAPSHOT_INVALID",
        }:
            return self.mark_integrity_compromised(reason)
        self._transition(HMLLifecycleState.FAILED)
        return self.diagnose(reason)

    def mark_integrity_compromised(
        self, code: str = "INTEGRITY_COMPROMISED",
    ) -> HMLLifecycleDiagnostic:
        """Latch permanently; no automatic recovery path grants PREPARE/ACT."""
        if code not in _SANITIZED and code not in _INTEGRITY_CODES:
            code = "INTEGRITY_COMPROMISED"
        self._fault = "HML_LIFECYCLE_INTEGRITY_COMPROMISED"
        self._state = HMLLifecycleState.RECOVERY_BLOCKED
        self._inflight = 0
        return self.diagnose("INTEGRITY_COMPROMISED")

    def request_stop(self) -> HMLLifecycleDiagnostic:
        if self._state is HMLLifecycleState.RECOVERY_BLOCKED:
            return self.diagnose("INTEGRITY_COMPROMISED")
        if self._state is HMLLifecycleState.STOPPED:
            return self.diagnose("SHUTDOWN")
        self._transition(HMLLifecycleState.STOPPED)
        self._inflight = 0
        return self.diagnose("SHUTDOWN")

    def attempt_recovery(self) -> HMLLifecycleDiagnostic:
        """Recovery after integrity compromise remains blocked by design."""
        if self._state is HMLLifecycleState.RECOVERY_BLOCKED or self._fault:
            raise HMLLifecycleError("HML_LIFECYCLE_RECOVERY_BLOCKED")
        raise HMLLifecycleError("HML_LIFECYCLE_RECOVERY_UNSUPPORTED")
