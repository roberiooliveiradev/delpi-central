"""User-delegated credential provider tests — C3-MCP-INTEROP-01R1A.

Contract-first coverage for the single-requester token exchange:
subject preservation, resource binding, scope/audience validation,
service-principal rejection, fail-closed provider errors, and the
bounded in-memory cache (user/resource isolation, expiry, hard cap).
All negative cases must fail closed with MCP_AUTHENTICATION_FAILED.
"""

from __future__ import annotations

import base64
import json
import time
from typing import Any, Mapping

import pytest

from app.application.specialist_interop.errors import (
    MCP_AUTHENTICATION_FAILED,
    SpecialistInteropError,
)
from app.infrastructure.interoperability.config import (
    SpecialistConnectionProfile,
)
from app.infrastructure.interoperability.delegation import (
    InMemoryDelegatedTokenCache,
    KeycloakDelegatedCredentialProvider,
)

DAVI_RESOURCE = "https://minhadelpi.com.br/apps/api-delpi/mcp"
TEO_RESOURCE = "https://minhadelpi.com.br/apps/transformometro-api/mcp"
VISTA_RESOURCE = "https://minhadelpi.com.br/apps/tv-dashboard-api/mcp"
ALL_RESOURCES = frozenset({DAVI_RESOURCE, TEO_RESOURCE, VISTA_RESOURCE})

SUB = "user-1234"
NOW = int(time.time())


def _jwt(claims: Mapping[str, Any]) -> str:
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "RS256", "typ": "JWT", "kid": "k"}).encode()
    ).rstrip(b"=")
    payload = base64.urlsafe_b64encode(json.dumps(dict(claims)).encode()).rstrip(
        b"="
    )
    return b".".join([header, payload, b"sig"]).decode()


def _subject(sub: str = SUB, exp: int | None = None) -> str:
    return _jwt(
        {
            "sub": sub,
            "aud": ["delpi-central", "delia-api", "account"],
            "exp": exp if exp is not None else NOW + 300,
            "iat": NOW,
        }
    )


def _exchanged(sub: str = SUB, aud=None, scope="openid email mcp:tools", exp=None) -> str:
    return _jwt(
        {
            "sub": sub,
            "aud": aud if aud is not None else ["delpi-central", DAVI_RESOURCE, "account"],
            "scope": scope,
            "azp": "delia-api",
            "exp": exp if exp is not None else NOW + 300,
        }
    )


def _profile(**overrides):
    values = {
        "endpoint": "http://svc:8000/mcp",
        "enabled": True,
        "timeout_seconds": 5.0,
        "exchange_audience": "mcp-api-delpi",
        "resource_audience": DAVI_RESOURCE,
    }
    values.update(overrides)
    return SpecialistConnectionProfile(**values)


class FakeResponse:
    def __init__(self, status: int, body: Any):
        self.status_code = status
        self._body = body
        self.headers: dict = {}
        self.content = (
            b"not-json"
            if isinstance(body, Exception)
            else json.dumps(body).encode()
        )

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


def _provider(
    *,
    subject: str | None = None,
    exchange_status: int = 200,
    exchange_body: Any = None,
    posts: list | None = None,
    validator=None,
    ttl: float = 120.0,
    config_overrides: dict | None = None,
):
    recorded = posts if posts is not None else []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        recorded.append(data)
        return FakeResponse(
            exchange_status,
            {"access_token": _exchanged()} if exchange_body is None else exchange_body,
        )

    def validator_default(token: str) -> Mapping[str, Any]:
        return json.loads(
            base64.urlsafe_b64decode(token.split(".")[1] + "==")
        )

    cfg = {
        "token_url": "http://kc/realms/delpi/protocol/openid-connect/token",
        "client_id": "delia-api",
        "client_secret": "test-secret",
        "timeout_seconds": 5.0,
    }
    cfg.update(config_overrides or {})
    provider = KeycloakDelegatedCredentialProvider(
        **cfg,
        http_post=http_post,
        subject_bearer_getter=lambda: subject
        if subject is not None
        else _subject(),
        token_validator=validator or validator_default,
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=ttl),
        known_resource_audiences=ALL_RESOURCES,
    )
    return provider, recorded


# --- positive path -------------------------------------------------------


def test_valid_exchange_returns_delegated_token():
    provider, posts = _provider()
    token = provider.credential_for(_profile())
    assert isinstance(token, str) and token.count(".") == 2
    sent = posts[0]
    assert sent["grant_type"] == "urn:ietf:params:oauth:grant-type:token-exchange"
    assert sent["client_id"] == "delia-api"
    assert sent["audience"] == "mcp-api-delpi"
    assert "mcp:tools" in sent["scope"]
    # the subject bearer is forwarded verbatim as the exchange input
    assert sent["subject_token"].count(".") == 2


def test_same_subject_and_resource_binding():
    provider, _ = _provider()
    token = provider.credential_for(_profile())
    claims = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))
    assert claims["sub"] == SUB
    assert DAVI_RESOURCE in claims["aud"]
    assert TEO_RESOURCE not in claims["aud"]
    assert VISTA_RESOURCE not in claims["aud"]


def test_cache_reuse_within_ttl():
    provider, posts = _provider()
    profile = _profile()
    first = provider.credential_for(profile)
    second = provider.credential_for(profile)
    assert first == second
    assert len(posts) == 1


def test_invalidate_forces_reexchange():
    provider, posts = _provider()
    profile = _profile()
    provider.credential_for(profile)
    provider.invalidate(profile)
    provider.credential_for(profile)
    assert len(posts) == 2


# --- subject bearer negatives -------------------------------------------


def test_missing_subject_bearer_fails_closed():
    provider, posts = _provider(subject="")
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert posts == []


def test_invalid_subject_bearer_fails_closed():
    provider, posts = _provider(subject="not-a-jwt")
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert posts == []


def test_expired_subject_bearer_fails_closed():
    provider, posts = _provider(subject=_subject(exp=NOW - 10))
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert posts == []


# --- exchange negatives --------------------------------------------------


def test_exchange_denied_fails_closed():
    provider, _ = _provider(
        exchange_status=403,
        exchange_body={"error": "access_denied"},
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_wrong_requester_secret_fails_closed():
    provider, _ = _provider(
        exchange_status=401, exchange_body={"error": "invalid_client"}
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_exchange_transport_failure_fails_closed():
    def raising(url, data=None, timeout=None):
        raise TimeoutError("slow")

    provider = KeycloakDelegatedCredentialProvider(
        token_url="http://kc/token",
        client_id="delia-api",
        client_secret="s",
        timeout_seconds=1.0,
        http_post=raising,
        subject_bearer_getter=_subject,
        token_validator=lambda t: {},
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=120.0),
        known_resource_audiences=ALL_RESOURCES,
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_malformed_exchange_response_fails_closed():
    for body in (
        {"no_access_token": True},
        "not-json",
        FakeResponseError(),
    ):
        provider, _ = _provider(exchange_body=body)
        with pytest.raises(SpecialistInteropError) as exc:
            provider.credential_for(_profile())
        assert exc.value.code == MCP_AUTHENTICATION_FAILED


class FakeResponseError(Exception):
    pass


def test_unconfigured_exchange_fails_closed():
    provider, posts = _provider(
        config_overrides={"client_secret": ""}
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert posts == []


def test_unknown_resource_fails_closed():
    provider, posts = _provider()
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile(resource_audience=""))
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    assert posts == []


# --- exchanged-token claim negatives -------------------------------------


def test_subject_mismatch_fails_closed():
    provider, _ = _provider(
        exchange_body={"access_token": _exchanged(sub="user-9999")}
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_service_principal_rejected():
    provider, _ = _provider(
        exchange_body={
            "access_token": _exchanged(sub="service-account-delia-api")
        },
        subject=_subject(sub="service-account-delia-api"),
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_missing_mcp_scope_rejected():
    provider, _ = _provider(
        exchange_body={
            "access_token": _exchanged(scope="openid email profile")
        }
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_wrong_resource_audience_rejected():
    provider, _ = _provider(
        exchange_body={
            "access_token": _exchanged(aud=["delpi-central", TEO_RESOURCE])
        }
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_multiple_mcp_audiences_rejected():
    provider, _ = _provider(
        exchange_body={
            "access_token": _exchanged(
                aud=["delpi-central", DAVI_RESOURCE, TEO_RESOURCE]
            )
        }
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_expired_exchanged_token_rejected():
    provider, _ = _provider(
        exchange_body={"access_token": _exchanged(exp=NOW - 5)}
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_validator_rejection_fails_closed():
    def bad(token):
        raise ValueError("bad signature")

    provider, _ = _provider(validator=bad)
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


def test_requester_azp_binding_enforced():
    # positive: azp == configured requester client passes (default case)
    provider, _ = _provider()
    token = provider.credential_for(_profile())
    claims = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))
    assert claims["azp"] == "delia-api"

    # negative: foreign requester azp fails closed
    foreign = dict(
        json.loads(
            base64.urlsafe_b64decode(_exchanged().split(".")[1] + "==")
        )
    )
    foreign["azp"] = "other-client"
    provider, _ = _provider(
        exchange_body={"access_token": _jwt(foreign)}
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED

    # negative: missing azp fails closed
    no_azp = dict(foreign)
    no_azp["azp"] = None
    no_azp.pop("azp")
    provider, _ = _provider(
        exchange_body={"access_token": _jwt(no_azp)}
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED


# --- cache isolation ------------------------------------------------------


def test_cross_user_cache_isolation():
    subjects = [_subject(sub="user-a"), _subject(sub="user-b")]

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        posts.append(data)
        return FakeResponse(200, {"access_token": _exchanged(sub="user-a" if len(posts) == 1 else "user-b")})

    posts: list = []
    provider = KeycloakDelegatedCredentialProvider(
        token_url="http://kc/token",
        client_id="delia-api",
        client_secret="s",
        timeout_seconds=5.0,
        http_post=http_post,
        subject_bearer_getter=lambda: subjects.pop(0)
        if subjects
        else _subject(),
        token_validator=lambda t: json.loads(
            base64.urlsafe_b64decode(t.split(".")[1] + "==")
        ),
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=120.0),
        known_resource_audiences=ALL_RESOURCES,
    )
    provider.credential_for(_profile())  # user-a
    provider.credential_for(_profile())  # user-b — different fingerprint
    assert len(posts) == 2


def test_cross_resource_cache_isolation():
    posts: list = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        posts.append(data)
        # bind each exchange to its requested audience
        resource = {
            "mcp-api-delpi": DAVI_RESOURCE,
            "mcp-transformometro": TEO_RESOURCE,
        }[data["audience"]]
        return FakeResponse(
            200,
            {
                "access_token": _exchanged(
                    aud=["delpi-central", resource], scope="openid mcp:tools"
                )
            },
        )

    provider = KeycloakDelegatedCredentialProvider(
        token_url="http://kc/token",
        client_id="delia-api",
        client_secret="s",
        timeout_seconds=5.0,
        http_post=http_post,
        subject_bearer_getter=_subject,
        token_validator=lambda t: json.loads(
            base64.urlsafe_b64decode(t.split(".")[1] + "==")
        ),
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=120.0),
        known_resource_audiences=ALL_RESOURCES,
    )
    davi = provider.credential_for(_profile())
    teo = provider.credential_for(
        _profile(
            exchange_audience="mcp-transformometro",
            resource_audience=TEO_RESOURCE,
        )
    )
    assert len(posts) == 2  # no cross-resource reuse
    assert davi != teo


def test_cached_expired_token_not_reused():
    clock = [0.0]
    cache = InMemoryDelegatedTokenCache(
        max_ttl_seconds=120.0, clock=lambda: clock[0]
    )
    cache.put("fp", DAVI_RESOURCE, "tok", token_exp_epoch=None)
    clock[0] = 200.0  # past TTL
    assert cache.get("fp", DAVI_RESOURCE) is None


def test_cache_hard_cap_enforced():
    cache = InMemoryDelegatedTokenCache(
        max_ttl_seconds=100000.0, clock=lambda: 0.0
    )
    cache.put("fp", DAVI_RESOURCE, "tok", token_exp_epoch=None)
    entry = cache._entries[("fp", DAVI_RESOURCE)]
    assert entry.expires_at <= 300.0


def test_cache_expiry_bounded_by_token_exp():
    clock = [50.0]
    now_wall = 1000.0
    cache = InMemoryDelegatedTokenCache(
        max_ttl_seconds=120.0, clock=lambda: clock[0]
    )
    cache.put(
        "fp",
        DAVI_RESOURCE,
        "tok",
        token_exp_epoch=now_wall + 30,  # expires in 30s
        wall_clock=lambda: now_wall,
    )
    entry = cache._entries[("fp", DAVI_RESOURCE)]
    # 30s remaining minus 15s safety margin → expires at clock+15
    assert entry.expires_at == 50.0 + 15.0


# --- C3-MCP-INTEROP-01R1C: redaction + host binding -----------------


def test_exchange_failure_never_leaks_subject_token_or_secret():
    """Provider errors must surface semantic codes only — no credential
    material may propagate upward through raised exceptions."""
    subject = _subject()
    secret = "super-secret-value-9f8e"

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        raise RuntimeError(f"boom {subject} {secret}")

    provider = KeycloakDelegatedCredentialProvider(
        token_url="http://kc/token",
        client_id="delia-api",
        client_secret=secret,
        timeout_seconds=5.0,
        http_post=http_post,
        subject_bearer_getter=lambda: subject,
        token_validator=lambda t: {},
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=120.0),
        known_resource_audiences=ALL_RESOURCES,
    )
    with pytest.raises(SpecialistInteropError) as exc:
        provider.credential_for(_profile())
    assert exc.value.code == MCP_AUTHENTICATION_FAILED
    rendered = str(exc.value) + str(exc.value.args)
    assert subject not in rendered
    assert secret not in rendered


def test_exchange_uses_configured_host_header_only():
    """The exchange request Host comes from trusted config only —
    never from subject token claims or caller input."""
    recorded: list = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        recorded.append(dict(headers or {}))
        return FakeResponse(200, {"access_token": _exchanged()})

    provider = KeycloakDelegatedCredentialProvider(
        token_url="http://kc/token",
        client_id="delia-api",
        client_secret="s",
        timeout_seconds=5.0,
        http_post=http_post,
        subject_bearer_getter=_subject,
        token_validator=lambda t: json.loads(
            base64.urlsafe_b64decode(t.split(".")[1] + "==")
        ),
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=120.0),
        known_resource_audiences=ALL_RESOURCES,
        host_header="public.example",
    )
    provider.credential_for(_profile())
    assert recorded[0]["Host"] == "public.example"

    recorded.clear()
    provider_no_host = KeycloakDelegatedCredentialProvider(
        token_url="http://kc/token",
        client_id="delia-api",
        client_secret="s",
        timeout_seconds=5.0,
        http_post=http_post,
        subject_bearer_getter=_subject,
        token_validator=lambda t: json.loads(
            base64.urlsafe_b64decode(t.split(".")[1] + "==")
        ),
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=120.0),
        known_resource_audiences=ALL_RESOURCES,
    )
    provider_no_host.credential_for(_profile())
    assert "Host" not in recorded[0]


def test_exchange_audience_comes_from_profile_not_input():
    """The exchange `audience` parameter is bound to the configured
    profile — the subject token cannot steer the target."""
    posted: list = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        posted.append(data)
        return FakeResponse(200, {"access_token": _exchanged()})

    provider = KeycloakDelegatedCredentialProvider(
        token_url="http://kc/token",
        client_id="delia-api",
        client_secret="s",
        timeout_seconds=5.0,
        http_post=http_post,
        subject_bearer_getter=_subject,
        token_validator=lambda t: json.loads(
            base64.urlsafe_b64decode(t.split(".")[1] + "==")
        ),
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=120.0),
        known_resource_audiences=ALL_RESOURCES,
    )
    provider.credential_for(_profile())
    assert posted[0]["audience"] == "mcp-api-delpi"
    assert posted[0]["client_id"] == "delia-api"


# --- LOOP-03R2A-R2: caller bound reaches the exchange ------------------------


def _r2_provider(posts=None, timeouts=None, http_post=None, subjects=None):
    recorded_posts = posts if posts is not None else []
    recorded_timeouts = timeouts if timeouts is not None else []
    subject_queue = list(subjects) if subjects else [_subject()]

    def default_post(url, headers=None, data=None, timeout=None, stream=None):
        recorded_posts.append(data)
        recorded_timeouts.append(timeout)
        return FakeResponse(200, {"access_token": _exchanged()})

    provider = KeycloakDelegatedCredentialProvider(
        token_url="http://kc/token",
        client_id="delia-api",
        client_secret="s",
        timeout_seconds=10.0,
        http_post=http_post or default_post,
        subject_bearer_getter=lambda: subject_queue.pop(0)
        if len(subject_queue) > 1
        else subject_queue[0],
        token_validator=lambda t: json.loads(
            base64.urlsafe_b64decode(t.split(".")[1] + "==")
        ),
        cache=InMemoryDelegatedTokenCache(max_ttl_seconds=120.0),
        known_resource_audiences=ALL_RESOURCES,
    )
    return provider, recorded_posts, recorded_timeouts


def test_r2_exchange_uses_caller_bound_reduction_only():
    """Cache miss: the wire exchange runs under
    min(caller remaining, configured ceiling) — reduction-only."""
    subjects = [_subject(sub="u-a"), _subject(sub="u-b")]
    tokens = iter(
        [
            _exchanged(sub="u-a"),
            _exchanged(sub="u-b"),
        ]
    )
    posts: list = []
    timeouts: list = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        posts.append(data)
        timeouts.append(timeout)
        return FakeResponse(200, {"access_token": next(tokens)})

    provider, _, _ = _r2_provider(http_post=http_post, subjects=subjects)
    provider.credential_for(_profile(), timeout_seconds=0.7)
    provider.credential_for(_profile(), timeout_seconds=99.0)
    # bounded_request passes (connect, read-slice) tuples — the
    # connect leg is the total wall-clock bound.
    assert timeouts[0][0] == 0.7
    assert timeouts[1][0] == 10.0


def test_r2_exchange_explicit_nonpositive_fails_fast():
    """timeout_seconds <= 0 is an exhausted caller budget — zero wire
    calls, timeout semantic; never a fresh configured window."""
    from app.application.specialist_interop.errors import MCP_TIMEOUT

    posts: list = []

    def http_post(url, headers=None, data=None, timeout=None, stream=None):
        posts.append(data)
        return FakeResponse(200, {"access_token": _exchanged()})

    provider, _, _ = _r2_provider(http_post=http_post)
    for bound in (0.0, -3.0):
        with pytest.raises(SpecialistInteropError) as exc:
            provider.credential_for(_profile(), timeout_seconds=bound)
        assert exc.value.code == MCP_TIMEOUT
    assert posts == []


def test_r2_cache_hit_needs_no_budget():
    """A warm cache returns with zero I/O — even a zero bound never
    blocks a cache hit (cache policy unchanged)."""
    provider, posts, _ = _r2_provider()
    provider.credential_for(_profile(), timeout_seconds=5.0)
    assert len(posts) == 1
    token = provider.credential_for(_profile(), timeout_seconds=0.0)
    assert isinstance(token, str) and token
    assert len(posts) == 1


def test_r2_exchange_slow_server_total_wall_clock():
    """Real-socket evidence: a stalled token endpoint cannot outlive
    the caller bound — total wall-clock, not per-recv inactivity."""
    import http.server
    import threading

    from app.application.specialist_interop.errors import MCP_TIMEOUT
    from app.infrastructure.http.deadline_transport import (
        deadline_http_post,
    )

    class SlowHandler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(length)
            time.sleep(3.0)
            try:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b"{}")
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), SlowHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/token"
        provider = KeycloakDelegatedCredentialProvider(
            token_url=url,
            client_id="delia-api",
            client_secret="s",
            timeout_seconds=10.0,
            http_post=deadline_http_post,
            subject_bearer_getter=lambda: _subject(),
            token_validator=lambda t: json.loads(
                base64.urlsafe_b64decode(t.split(".")[1] + "==")
            ),
            cache=InMemoryDelegatedTokenCache(max_ttl_seconds=120.0),
            known_resource_audiences=ALL_RESOURCES,
        )
        started = time.monotonic()
        with pytest.raises(SpecialistInteropError) as exc:
            provider.credential_for(_profile(), timeout_seconds=0.4)
        assert exc.value.code == MCP_TIMEOUT
        assert time.monotonic() - started < 2.0
    finally:
        server.shutdown()
