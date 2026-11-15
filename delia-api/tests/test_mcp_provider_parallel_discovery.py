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


# -------------------------------------------------------------------
# REAL-BOUNDARY security oracle — DELIA-C3-T2-PARALLEL-DISCOVERY-
# SECURITY-AND-FULL-SET-REPROOF-01 (review residual:
# NEGATIVE_BEARER_AUTH_ORACLE PARTIAL + WORKER_TOTAL_LIFETIME PARTIAL).
#
# These tests cross the REAL chain —
#   McpCapabilityProvider → SpecialistInterop → McpSpecialistAdapter
#   → KeycloakDelegatedCredentialProvider → (stubbed wire edges only)
# — so "no bearer → no authenticated discovery" is proven at the same
# boundary production enforces, not inside a friendly interop fake.
# Only the two wire edges are stubbed: the exchange ``http_post``
# (records, never opens a socket) and the MCP ``transport_factory``.
# -------------------------------------------------------------------

import base64 as _b64
import json as _json

from app.application.specialist_interop.specialist_interop import (
    SpecialistInterop,
)
from app.infrastructure.http.deadline_transport import (
    deadline_http_post,
)
from app.infrastructure.interoperability.config import (
    SpecialistConnectionProfile,
)
from app.infrastructure.interoperability.delegation import (
    InMemoryDelegatedTokenCache,
    KeycloakDelegatedCredentialProvider,
)
from app.infrastructure.interoperability.mcp.adapter import (
    McpSpecialistAdapter,
)


def _jwt(sub: str, *, exp=None, **extra) -> str:
    payload = {
        "sub": sub,
        "exp": exp or int(time.time()) + 3600,
        "azp": "delpi-central",
    }
    payload.update(extra)

    def _b(d):
        return _b64.urlsafe_b64encode(
            _json.dumps(d).encode()
        ).rstrip(b"=").decode()

    return f"{_b({'alg': 'none'})}.{_b(payload)}.x"


def _decode(token: str):
    return _json.loads(
        _b64.urlsafe_b64decode(token.split(".")[1] + "==")
    )


class _Resp:
    """Wire-level stub response consumed by ``bounded_request`` —
    materialized content, headers and close, like a drained
    ``requests`` response."""

    status_code = 200
    headers: dict = {}

    def __init__(self, body):
        self._body = body
        self.content = _json.dumps(body).encode()

    def json(self):
        return self._body

    def close(self):
        return None


class _RecordingExchange:
    """Stubbed ``http_post`` for the REAL delegation provider.

    Records (subject_token_sent, audience, caller-visible bearer at
    call time); fabricates a delegated JWT whose ``sub`` mirrors the
    subject it received — exactly what the exchange contract returns,
    so a swapped subject would produce a detectably wrong delegated
    identity.
    """

    def __init__(self, subject_sub: str):
        self.subject_sub = subject_sub
        self.calls: list[dict] = []

    def __call__(self, url, headers=None, data=None, **send_kwargs):
        subject = (data or {}).get("subject_token", "")
        self.calls.append(
            {
                "subject_token": subject,
                "audience": (data or {}).get("audience"),
                "contextvar_bearer": current_subject_bearer(),
            }
        )
        # The delegated token's aud is the RESOURCE audience bound to
        # the requested exchange audience (mcp-<sid> → its resource
        # URL) — mirroring what the real exchange returns.
        exchange_aud = (data or {}).get("audience") or ""
        sid = exchange_aud.removeprefix("mcp-")
        return _Resp(
            {
                "access_token": _jwt(
                    self.subject_sub,
                    aud=f"https://aud.test/{sid}/mcp",
                    azp="delia-api",
                    scope="openid mcp:tools",
                )
            }
        )


class _RecordingTransport:
    """Stub transport edge: records the bearer it was constructed
    with, then serves a static tools/list."""

    def __init__(self, registry: list, profile, bearer):
        registry.append(
            {"specialist": profile.resource_audience, "bearer": bearer}
        )

    def initialize(self, timeout_seconds=None):
        return None

    def list_tools(self, timeout_seconds=None):
        return [
            {
                "name": "read",
                "_meta": {"delpi/toolClass": "read"},
                "description": "x",
                "inputSchema": {},
            }
        ]


def _real_chain(specialist_ids, *, exchange):
    """Real interop + real adapter + real delegation provider; wire
    edges stubbed. Returns (provider_inputs, transport_registry)."""
    profiles = {
        sid: SpecialistConnectionProfile(
            endpoint="http://transformometro-api:8000/mcp",
            enabled=True,
            timeout_seconds=5.0,
            exchange_audience=f"mcp-{sid}",
            resource_audience=f"https://aud.test/{sid}/mcp",
        )
        for sid in specialist_ids
    }
    transports: list = []
    cred = KeycloakDelegatedCredentialProvider(
        token_url="http://kc.test/token",
        client_id="delia-api",
        client_secret="test-secret",
        timeout_seconds=5.0,
        http_post=exchange,
        subject_bearer_getter=current_subject_bearer,
        token_validator=_decode,
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=60.0),
        known_resource_audiences=frozenset(
            p.resource_audience for p in profiles.values()
        ),
    )
    adapter = McpSpecialistAdapter(
        profiles,
        credential_provider=cred,
        transport_factory=lambda profile, bearer: _RecordingTransport(
            transports, profile, bearer
        ),
    )
    return (
        SpecialistInterop(adapter),
        profiles,
        transports,
        cred,
    )


def _parallel_provider(specialist_ids, interop, **kw):
    kw.setdefault("parallel_discovery", True)
    kw.setdefault("subject_bearer_getter", current_subject_bearer)
    kw.setdefault("bind_bearer", bind_subject_bearer)
    kw.setdefault("unbind_bearer", unbind_subject_bearer)
    return McpCapabilityProvider(interop, specialist_ids, **kw)


# --- A1.1: no bearer → real boundary fails closed -----------------


def test_real_no_bearer_fails_closed_zero_wire():
    """No subject anywhere: every specialist resolves to
    mcp_authentication_failed, ZERO exchange calls, ZERO transport
    constructions, ZERO groups — no fabricated identity, no
    unauthenticated discovery, no authorized capability."""
    exchange = _RecordingExchange("subj")
    interop, _p, transports, _c = _real_chain(
        ["teo", "vista", "davi"], exchange=exchange
    )
    provider = _parallel_provider(["teo", "vista", "davi"], interop)
    surface = provider.list_groups(correlation_id="rb1")
    assert surface.groups == ()
    assert list(surface.failures) == [
        MCP_AUTHENTICATION_FAILED
    ] * 3
    assert exchange.calls == []  # exchange never attempted
    assert transports == []  # transport never opened


# --- A1.2: valid bearer → delegated identity reaches the worker ---


def test_real_bearer_exchanged_in_worker_delegated_at_transport():
    """Caller-bound subject A: workers run the REAL exchange with A's
    token, transport receives the DELEGATED token (aud=resource),
    never the subject bearer itself."""
    subject = _jwt("user-A")
    exchange = _RecordingExchange("user-A")
    interop, _p, transports, _c = _real_chain(
        ["teo", "vista"], exchange=exchange
    )
    provider = _parallel_provider(["teo", "vista"], interop)
    tok = bind_subject_bearer(subject)
    try:
        surface = provider.list_groups(correlation_id="rb2")
    finally:
        unbind_subject_bearer(tok)
    assert len(surface.groups) == 2
    assert surface.failures == ()
    # Every exchange sent THIS subject's token — worker-bound, never
    # fabricated — and the worker ContextVar saw the same bearer.
    assert len(exchange.calls) == 2
    for call in exchange.calls:
        assert call["subject_token"] == subject
        assert call["contextvar_bearer"] == subject
    # Transport got the delegated credential, not the subject bearer.
    for entry in transports:
        assert entry["bearer"] != subject
        claims = _decode(entry["bearer"])
        assert claims["sub"] == "user-A"
        assert claims["aud"] == entry["specialist"]


# --- A1.3: two users concurrent → zero identity mixing ------------


def test_real_two_users_concurrent_no_mixing():
    """CALLER_A→SUBJECT_A and CALLER_B→SUBJECT_B overlapping: every
    exchange carries the correct subject, every transport receives the
    correct delegated sub, nothing crosses."""
    subjects = {"A": _jwt("user-A"), "B": _jwt("user-B")}
    # One shared credential provider would still isolate by
    # fingerprint; here each user gets its own provider AND we assert
    # the wire evidence anyway (defense in depth).
    results: dict[str, object] = {}
    barrier = threading.Barrier(3)
    exchanges = {}

    def _run(tag):
        exchange = _RecordingExchange(f"user-{tag}")
        exchanges[tag] = exchange
        interop, _p, transports, _c = _real_chain(
            ["teo", "vista"], exchange=exchange
        )
        results[f"transports_{tag}"] = transports
        provider = _parallel_provider(["teo", "vista"], interop)
        tok = bind_subject_bearer(subjects[tag])
        try:
            barrier.wait(timeout=10)
            surface = provider.list_groups(
                correlation_id=f"rb3-{tag}"
            )
        finally:
            unbind_subject_bearer(tok)
        results[tag] = surface

    threads = [
        threading.Thread(target=_run, args=(tag,))
        for tag in ("A", "B")
    ]
    for t in threads:
        t.start()
    barrier.wait(timeout=10)  # release both callers together
    for t in threads:
        t.join(timeout=20)

    for tag in ("A", "B"):
        surface = results[tag]
        assert len(surface.groups) == 2
        for call in exchanges[tag].calls:
            assert call["subject_token"] == subjects[tag]
            assert call["contextvar_bearer"] == subjects[tag]
        for entry in results[f"transports_{tag}"]:
            assert _decode(entry["bearer"])["sub"] == f"user-{tag}"


# --- A1.4/1.5: unbind on exception + no stale identity on reuse ---


def test_real_unbind_in_finally_on_worker_exception():
    """A specialist whose exchange blows up mid-flight still unbinds —
    bind/unbind spy counts must match exactly, and the next call with
    a different subject must not inherit anything."""
    events: list[str] = []
    real_bind, real_unbind = bind_subject_bearer, unbind_subject_bearer

    def spy_bind(bearer):
        events.append("bind")
        return real_bind(bearer)

    def spy_unbind(token):
        events.append("unbind")
        return real_unbind(token)

    class _Boom:
        calls = 0

        def __call__(self, url, headers=None, data=None, timeout_seconds=None):
            _Boom.calls += 1
            raise RuntimeError("exchange exploded")

    exchange = _Boom()
    interop, _p, _t, _c = _real_chain(
        ["teo", "vista"], exchange=exchange
    )
    provider = _parallel_provider(
        ["teo", "vista"],
        interop,
        bind_bearer=spy_bind,
        unbind_bearer=spy_unbind,
    )
    tok = bind_subject_bearer(_jwt("user-A"))
    try:
        surface = provider.list_groups(correlation_id="rb4")
    finally:
        unbind_subject_bearer(tok)
    assert list(surface.failures) == [
        MCP_AUTHENTICATION_FAILED
    ] * 2
    assert events.count("bind") == events.count("unbind") == 2
    # Thread reuse: a second call under user B sees only B.
    exchange2 = _RecordingExchange("user-B")
    interop2, _p2, transports2, _c2 = _real_chain(
        ["teo", "vista"], exchange=exchange2
    )
    provider2 = _parallel_provider(["teo", "vista"], interop2)
    tok2 = bind_subject_bearer(_jwt("user-B"))
    try:
        surface2 = provider2.list_groups(correlation_id="rb5")
    finally:
        unbind_subject_bearer(tok2)
    assert len(surface2.groups) == 2
    assert exchange2.calls[0]["contextvar_bearer"] != _jwt("user-A")
    assert _decode(exchange2.calls[0]["subject_token"])["sub"] == "user-B"


# --- A1.1b: empty bearer after a cached call never gets served ----


def test_real_anonymous_worker_never_reads_cache():
    """After user A's delegated tokens are cached, a call with NO
    bearer gets auth_failed with ZERO exchange attempts — the
    fingerprint-keyed cache is unreachable without a subject."""
    exchange = _RecordingExchange("user-A")
    interop, _p, transports, _c = _real_chain(
        ["teo", "vista"], exchange=exchange
    )
    provider = _parallel_provider(["teo", "vista"], interop)
    tok = bind_subject_bearer(_jwt("user-A"))
    try:
        assert len(provider.list_groups(correlation_id="rb6").groups) == 2
    finally:
        unbind_subject_bearer(tok)
    assert len(exchange.calls) == 2  # cache now warm
    # Anonymous call: fail-closed, no exchange, no cache hit, no group.
    anon = provider.list_groups(correlation_id="rb7")
    assert anon.groups == ()
    assert list(anon.failures) == [MCP_AUTHENTICATION_FAILED] * 2
    assert len(exchange.calls) == 2
    assert len(transports) == 2  # only the authenticated call's


# --- A1.6: no credential material in the produced surface ---------


def test_real_surface_carries_no_credential_material():
    subject = _jwt("user-A")
    marker_secret = "SUBJECT-TOKEN-NEVER-LEAK"
    exchange = _RecordingExchange("user-A")
    interop, _p, transports, _c = _real_chain(
        ["teo", "vista"], exchange=exchange
    )
    provider = _parallel_provider(["teo", "vista"], interop)
    tok = bind_subject_bearer(subject)
    try:
        surface = provider.list_groups(correlation_id="rb8")
    finally:
        unbind_subject_bearer(tok)
    blob = repr(surface)
    assert subject not in blob
    assert "access_token" not in blob
    assert "Authorization" not in blob
    # The delegated token itself must never appear either.
    for entry in transports:
        assert entry["bearer"] not in blob


# --- A2.4/A2.5: exchange slow → real absolute deadline + lifetime -


def test_real_exchange_trickle_killed_at_absolute_deadline():
    """REAL socket: a local HTTP server that drips the exchange
    response forever must be killed at the request's absolute
    deadline — not granted a fresh window per fragment."""
    import http.server
    import socketserver

    class _Trickle(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            # Drip bytes forever — an absolute deadline, not a
            # per-recv window, is the only thing that can stop this.
            try:
                while True:
                    self.wfile.write(b" ")
                    self.wfile.flush()
                    time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *a):
            pass

    server = socketserver.TCPServer(
        ("127.0.0.1", 0), _Trickle
    )
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        cred = KeycloakDelegatedCredentialProvider(
            token_url=f"http://127.0.0.1:{port}/token",
            client_id="delia-api",
            client_secret="x",
            timeout_seconds=30.0,  # configured far above the bound
            http_post=deadline_http_post,
            subject_bearer_getter=current_subject_bearer,
            token_validator=_decode,
            cache=InMemoryDelegatedTokenCache(max_ttl_seconds=60.0),
            known_resource_audiences=frozenset({"a"}),
        )
        profile = SpecialistConnectionProfile(
            endpoint="http://transformometro-api:8000/mcp",
            enabled=True,
            timeout_seconds=5.0,
            exchange_audience="mcp-teo",
            resource_audience="https://aud.test/teo/mcp",
        )
        tok = bind_subject_bearer(_jwt("user-A"))
        started = time.monotonic()
        try:
            with pytest.raises(SpecialistInteropError) as exc:
                cred.credential_for(profile, timeout_seconds=0.7)
        finally:
            unbind_subject_bearer(tok)
        elapsed = time.monotonic() - started
        assert exc.value.code == MCP_TIMEOUT
        # Killed at ~0.7s absolute, not after the (infinite) drip.
        assert elapsed < 3.0
    finally:
        server.shutdown()
        server.server_close()


def test_parallel_worker_dies_at_deadline_real_socket():
    """A2.5: caller returns at deadline while the worker's real
    socket read is in-flight — the WORKER thread (not just the
    caller) is measured to terminate at its absolute deadline."""
    import http.server
    import socketserver

    done_event = threading.Event()

    class _Trickle(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            try:
                while not done_event.is_set():
                    self.wfile.write(b" ")
                    self.wfile.flush()
                    time.sleep(0.05)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *a):
            pass

    server = socketserver.TCPServer(("127.0.0.1", 0), _Trickle)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        # Interop whose discover runs the REAL exchange against the
        # trickle server — thread must die at deadline by socket kill.
        cred = KeycloakDelegatedCredentialProvider(
            token_url=f"http://127.0.0.1:{port}/token",
            client_id="delia-api",
            client_secret="x",
            timeout_seconds=30.0,
            http_post=deadline_http_post,
            subject_bearer_getter=current_subject_bearer,
            token_validator=_decode,
            cache=InMemoryDelegatedTokenCache(max_ttl_seconds=60.0),
            known_resource_audiences=frozenset({"a"}),
        )
        profile = SpecialistConnectionProfile(
            endpoint="http://transformometro-api:8000/mcp",
            enabled=True,
            timeout_seconds=5.0,
            exchange_audience="mcp-teo",
            resource_audience="https://aud.test/teo/mcp",
        )

        class _ExchangeInterop:
            def discover_catalog(self, request):
                cred.credential_for(
                    profile,
                    timeout_seconds=request.timeout_seconds,
                )
                return _catalog(request.specialist_id)

            def native_toolset_config(self, group_id, *, timeout_seconds=None):
                raise NotImplementedError

            def invoke(self, request):
                raise NotImplementedError

        provider = _parallel_provider(
            ["teo"], _ExchangeInterop()
        )
        tok = bind_subject_bearer(_jwt("user-A"))
        started = time.monotonic()
        try:
            surface = provider.list_groups(
                correlation_id="rb9", timeout_seconds=0.6
            )
        finally:
            unbind_subject_bearer(tok)
        caller_elapsed = time.monotonic() - started
        assert caller_elapsed < 2.0
        assert list(surface.failures) == [MCP_TIMEOUT]
        # Measure the WORKER's termination: its socket was killed at
        # the same absolute deadline (plus scheduling slack) — the
        # drip would otherwise run forever.
        threads_now = {
            t.ident: t
            for t in threading.enumerate()
            if t.name.startswith("delia-mcp-disc")
        }
        for t in threads_now.values():
            t.join(timeout=5.0)
        total = time.monotonic() - started
        assert all(not t.is_alive() for t in threads_now.values())
        assert total < 5.0
    finally:
        done_event.set()
        server.shutdown()
        server.server_close()


# --- A2.9: repeated timeouts — no thread/resource accumulation ----


def test_repeated_timeout_turns_no_thread_accumulation():
    before = {
        t.ident
        for t in threading.enumerate()
        if t.name.startswith("delia-mcp-disc")
    }
    interop = FakeInterop(
        {"slow": {"delay": 0.4}, "ok": {}}
    )
    provider = _parallel_provider(["slow", "ok"], interop)
    for i in range(3):
        provider.list_groups(correlation_id=f"rt{i}", timeout_seconds=0.15)
        time.sleep(0.5)  # let bounded workers drain
    after = {
        t.ident
        for t in threading.enumerate()
        if t.name.startswith("delia-mcp-disc")
    }
    # No net growth of lingering worker threads across turns.
    assert len(after - before) == 0


# --- A3 extra contract cases --------------------------------------


def test_parallel_deadline_exhausted_before_dispatch():
    """timeout_seconds=0 → every specialist is a truthful timeout,
    ZERO transport/exchange work attempted."""
    interop = FakeInterop({"a": {}, "b": {}})
    provider = _provider(
        ["a", "b"], interop, parallel_discovery=True
    )
    surface = provider.list_groups(
        correlation_id="a3-zero", timeout_seconds=0.0
    )
    assert surface.groups == ()
    assert list(surface.failures) == [MCP_TIMEOUT, MCP_TIMEOUT]
    assert interop.calls == []


def test_parallel_empty_catalog_is_legit_surface():
    """A specialist listing ZERO tools yields an empty capability
    group (legitimate emptiness) — never a failure marker."""
    interop = FakeInterop({"a": {}, "empty": {}})

    orig = interop.discover_catalog

    def _d(request):
        if request.specialist_id == "empty":
            cat = orig(request)
            return SpecialistCatalogResult(
                specialist=cat.specialist,
                capabilities=(),
                blocked_remote_names=(),
                observed_at=cat.observed_at,
            )
        return orig(request)

    interop.discover_catalog = _d
    provider = _provider(
        ["a", "empty"], interop, parallel_discovery=True
    )
    surface = provider.list_groups(correlation_id="a3-empty")
    assert len(surface.groups) == 2
    assert surface.failures == ()
    empty_group = [
        g for g in surface.groups if g.group_id == "empty"
    ][0]
    assert empty_group.capabilities == ()
