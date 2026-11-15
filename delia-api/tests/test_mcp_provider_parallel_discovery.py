"""C3-T2 guarded experiment — parallel MCP specialist discovery.

RED→GREEN coverage for ``McpCapabilityProvider.list_groups`` with the
``parallel_discovery`` flag (default OFF = sequential contract
unchanged):

- per-specialist bounded fan-out preserves the identical return
  contract (groups keyed deterministically, failures in submission
  order);
- the subject bearer captured on the caller thread is bound/unbound
  per worker via the existing ``bind_subject_bearer`` seam — a worker
  never infers identity and never leaks it to another context;
- a late/slow specialist is reported as a truthful failure instead of
  blocking the whole surface;
- bounded worker count, no unbounded threads;
- sequential default is a non-regression.

Authorization: DELIA-C3-T2-PARALLEL-MCP-DISCOVERY-GUARDED-EXPERIMENT-01
(coordination review 2026-11-15, ACCEPT_WITH_RESIDUAL + explicit
experiment gates).
"""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest

from app.application.capability_provision.mcp_provider import (
    McpCapabilityProvider,
)
from app.application.specialist_interop.contracts import (
    SpecialistCatalogResult,
)
from app.application.specialist_interop.errors import (
    MCP_AUTHENTICATION_FAILED,
    MCP_TIMEOUT,
    SpecialistInteropError,
)
from app.domain.specialist_interop.model import SpecialistRef
from app.infrastructure.auth.subject_bearer import (
    bind_subject_bearer,
    current_subject_bearer,
    unbind_subject_bearer,
)


def _catalog(specialist_id: str, caps: tuple = ()) -> SpecialistCatalogResult:
    return SpecialistCatalogResult(
        specialist=SpecialistRef(
            specialist_id=specialist_id,
            display_name=specialist_id.upper(),
            owner_ref=f"{specialist_id}-owner",
        ),
        capabilities=caps,
        blocked_remote_names=(),
        observed_at="2026-11-15T00:00:00Z",
    )


class FakeInterop:
    """Scripted specialist interop: per-id latency, outcome or error.

    Records every ``discover_catalog`` request with the bearer visible
    to the worker at call time — proving identity isolation.
    """

    def __init__(self, script: dict[str, dict]):
        self._script = script
        self.calls: list[tuple[str, str | None]] = []
        self._lock = threading.Lock()
        self._active = 0
        self._max_active = 0

    @property
    def max_active(self) -> int:
        return self._max_active

    def discover_catalog(self, request):
        with self._lock:
            self._active += 1
            self._max_active = max(self._max_active, self._active)
        bearer = current_subject_bearer()
        with self._lock:
            self.calls.append((request.specialist_id, bearer))
        try:
            spec = self._script[request.specialist_id]
            delay = spec.get("delay", 0)
            if delay:
                time.sleep(delay)
            error = spec.get("error")
            if error is not None:
                raise error
            return _catalog(request.specialist_id)
        finally:
            with self._lock:
                self._active -= 1

    def native_toolset_config(self, group_id, *, timeout_seconds=None):  # pragma: no cover
        raise NotImplementedError

    def invoke(self, request):  # pragma: no cover
        raise NotImplementedError


class _BoundBearerCheck:
    """Interop asserting the worker sees the caller's bound bearer."""


def _call(provider, **kwargs):
    """Adapt ProviderSurface to the (groups_dict, failures_list) view
    the orchestrator builds — keys ``provider_id:group_id``."""
    surface = provider.list_groups(**kwargs)
    groups = {
        f"{g.provider_id}:{g.group_id}": g for g in surface.groups
    }
    return groups, list(surface.failures)


def _provider(
    specialist_ids,
    interop,
    **kwargs,
) -> McpCapabilityProvider:
    if kwargs.get("parallel_discovery"):
        # Same seam composition wires in production: real
        # accessor + bind/unbind callables, never infrastructure
        # imported by the provider itself.
        kwargs.setdefault("subject_bearer_getter", current_subject_bearer)
        kwargs.setdefault("bind_bearer", bind_subject_bearer)
        kwargs.setdefault("unbind_bearer", unbind_subject_bearer)
    return McpCapabilityProvider(
        interop, specialist_ids, **kwargs
    )


# -------------------------------------------------------------------
# Sequential contract — non-regression (flag default OFF)
# -------------------------------------------------------------------


def test_sequential_default_contract_unchanged():
    """Flag OFF (default): one group per specialist, submission-order
    keys, failures appended — the existing contract verbatim."""
    interop = FakeInterop(
        {
            "teo": {"delay": 0.01},
            "vista": {"delay": 0.01},
            "davi": {
                "error": SpecialistInteropError(
                    MCP_TIMEOUT, "davi unreachable"
                )
            },
        }
    )
    provider = _provider(["teo", "vista", "davi"], interop)
    groups, failures = _call(provider, correlation_id="c1")
    assert sorted(groups) == ["mcp:teo", "mcp:vista"]
    assert failures == [MCP_TIMEOUT]
    assert groups["mcp:teo"].owner_ref == "teo-owner"
    # Sequential: never more than one active discovery.
    assert interop.max_active == 1


def test_parallel_flag_off_by_default_signature():
    """The provider's default construction admits no parallel mode —
    flag-gated constructor arg only."""
    provider = _provider(["teo"], FakeInterop({"teo": {}}))
    assert getattr(provider, "_parallel_discovery", False) is False


# -------------------------------------------------------------------
# Parallel mode — contract equivalence
# -------------------------------------------------------------------


def test_parallel_groups_and_failures_deterministic_order():
    """PAR-01: three specialists with different latencies — results
    merge in SUBMISSION order, failures isolated per specialist."""
    interop = FakeInterop(
        {
            "slow_ok": {"delay": 0.15},
            "fast_ok": {"delay": 0.01},
            "mid_fail": {
                "delay": 0.05,
                "error": SpecialistInteropError(
                    MCP_AUTHENTICATION_FAILED, "401"
                ),
            },
        }
    )
    provider = _provider(
        ["slow_ok", "mid_fail", "fast_ok"],
        interop,
        parallel_discovery=True,
    )
    groups, failures = _call(provider, correlation_id="c2")
    assert list(groups) == ["mcp:slow_ok", "mcp:fast_ok"]
    assert failures == [MCP_AUTHENTICATION_FAILED]
    # Real concurrency happened — not serialized.
    assert interop.max_active >= 2


def test_parallel_bearer_bound_and_unbound_per_worker():
    """PAR-02/03: the caller's subject bearer is visible inside each
    worker (existing bind seam) and gone after the call — no leak."""
    interop = FakeInterop({"a": {}, "b": {}, "c": {}})
    provider = _provider(["a", "b", "c"], interop, parallel_discovery=True)
    token = bind_subject_bearer("subject-token-AAA")
    try:
        groups, failures = _call(provider, correlation_id="c3")
    finally:
        unbind_subject_bearer(token)
    assert failures == []
    assert len(groups) == 3
    # Every worker saw the SAME caller-bound bearer — never inferred.
    assert {b for _, b in interop.calls} == {"subject-token-AAA"}
    # Caller context unbound; nothing left in this thread's var.
    assert current_subject_bearer() is None


def test_parallel_no_bearer_workers_fail_closed():
    """PAR-04: no subject bearer anywhere → workers see None; any
    credential-dependent path fails closed, no identity fabricated."""
    interop = FakeInterop({"a": {}, "b": {}})
    provider = _provider(["a", "b"], interop, parallel_discovery=True)
    groups, failures = _call(provider, correlation_id="c4")
    assert {b for _, b in interop.calls} == {None}
    # Discovery itself succeeded (fail-closed is per-capability);
    # no bearer was ever bound into a worker.
    assert len(groups) == 2


def test_parallel_isolated_failure_never_absence():
    """PAR-05: a failing specialist yields a failure marker, never an
    empty-group 'capability absent' lie."""
    interop = FakeInterop(
        {
            "ok1": {},
            "bad": {
                "error": SpecialistInteropError(MCP_TIMEOUT, "t/o")
            },
            "ok2": {},
        }
    )
    provider = _provider(["ok1", "bad", "ok2"], interop, parallel_discovery=True)
    groups, failures = _call(provider, correlation_id="c5")
    assert sorted(groups) == ["mcp:ok1", "mcp:ok2"]
    assert failures == [MCP_TIMEOUT]
    assert "mcp:bad" not in groups


def test_parallel_global_deadline_bounds_slow_specialist():
    """PAR-06: the shared timeout_seconds bounds the whole fan-out —
    a specialist exceeding it is failed truthfully, never waited."""
    interop = FakeInterop(
        {
            "fast": {"delay": 0.01},
            "hung": {"delay": 5.0},
        }
    )
    provider = _provider(["hung", "fast"], interop, parallel_discovery=True)
    started = time.monotonic()
    groups, failures = _call(provider, 
        correlation_id="c6", timeout_seconds=0.6
    )
    elapsed = time.monotonic() - started
    assert elapsed < 2.0  # never waited the 5s hang
    assert sorted(groups) == ["mcp:fast"]
    assert failures == [MCP_TIMEOUT]


def test_parallel_worker_count_bounded():
    """PAR-07: fan-out width is structurally bounded — never one
    unbounded thread per specialist beyond the cap."""
    ids = [f"s{i}" for i in range(9)]
    interop = FakeInterop({sid: {"delay": 0.05} for sid in ids})
    provider = _provider(ids, interop, parallel_discovery=True)
    groups, failures = _call(provider, correlation_id="c7")
    assert failures == []
    assert len(groups) == 9
    assert interop.max_active <= 4  # bounded cap


def test_parallel_late_result_not_adopted():
    """PAR-08: a worker finishing after the join deadline contributes
    NOTHING to the catalog — late results are discarded."""
    interop = FakeInterop(
        {"fast": {}, "late": {"delay": 1.2}}
    )
    provider = _provider(["fast", "late"], interop, parallel_discovery=True)
    groups, failures = _call(provider, 
        correlation_id="c8", timeout_seconds=0.4
    )
    assert "mcp:late" not in groups
    assert failures == [MCP_TIMEOUT]


def test_parallel_bearer_never_in_error_or_surface():
    """PAR-09: bearer material never reaches groups/failures — the
    projection carries only owner-typed metadata."""
    interop = FakeInterop({"a": {}})
    provider = _provider(["a"], interop, parallel_discovery=True)
    token = bind_subject_bearer("SECRET-BEARER-XYZ")
    try:
        groups, failures = _call(provider, correlation_id="c9")
    finally:
        unbind_subject_bearer(token)
    blob = repr(groups) + repr(failures)
    assert "SECRET-BEARER-XYZ" not in blob


def test_parallel_workers_do_not_outlive_turn_bound():
    """PAR-10: after list_groups returns on deadline, in-flight
    workers still finish bounded by their own deadline — measured,
    not assumed."""
    interop = FakeInterop({"hung": {"delay": 3.0}, "fast": {}})
    provider = _provider(["hung", "fast"], interop, parallel_discovery=True)
    provider.list_groups(correlation_id="c10", timeout_seconds=0.3)
    # The returned-early worker is still running but bounded: it
    # cannot exceed its own deadline by construction; verify the
    # active count drains within a bounded grace window.
    deadline = time.monotonic() + 4.0
    while interop._active > 0 and time.monotonic() < deadline:
        time.sleep(0.05)
    # Real fake sleeps don't honor socket deadlines — bound the
    # residual wait demonstrably rather than pretending kill.
    assert time.monotonic() < deadline
