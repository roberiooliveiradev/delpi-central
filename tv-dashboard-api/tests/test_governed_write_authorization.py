"""Regression: human-governed material writes require an end-user principal
with fresh effective Core RBAC (VISTA/TV AuthZ hardening).

Covers SEC-REPRO-1 (service principal reaches writes), SEC-REPRO-2 (stale
RBAC authorizes revoked writes) and SEC-REPRO-3 (service principal must not
claim orphan playlist ownership).

The autouse conftest seam replaces the gate's fresh-RBAC fetch with a
principal+permission check for legacy fixtures; freshness paths here restore
the real gate and control ``_fetch_fresh_rbac`` directly.
"""

from __future__ import annotations

import asyncio
import logging
from functools import partial
from types import SimpleNamespace
from uuid import uuid4

import anyio
import anyio.to_thread
import httpx
import pytest
from fastapi.testclient import TestClient

import tv_app.core.security as sec
from tv_app.core.security import GovernedWriteAuthzError
from tv_app.core.security import (
    require_fresh_write_authorization as _real_sync_gate,
)
from tv_app.core.security import (
    arequire_fresh_write_authorization as _real_async_gate,
)

SERVICE_TOKEN = "repro-internal-service-token"


def _sync_gate(user, **kwargs):
    """Sync gate in its production runtime: an AnyIO worker thread under the
    app event loop (FastAPI sync route / MCP sync tool)."""
    return anyio.run(
        partial(anyio.to_thread.run_sync, partial(_real_sync_gate, user, **kwargs))
    )


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", SERVICE_TOKEN)
    from tv_app.main import app

    return TestClient(app)


def _svc_headers() -> dict[str, str]:
    return {"X-Delpi-Service-Token": SERVICE_TOKEN}


def _service_user() -> SimpleNamespace:
    return SimpleNamespace(
        id="internal-service",
        email="service@delpi.internal",
        name="Serviço Interno",
        roles=["internal-service"],
        groups=[],
        permissions=[],
        is_superadmin=True,
        rbac_unavailable=False,
        access_token=None,
        principal_type="service",
    )


def _human_user(**over) -> SimpleNamespace:
    base = dict(
        id="user-1",
        email="u@delpi.local",
        name="User",
        roles=[],
        groups=[],
        permissions=["tv-dashboard.write"],
        is_superadmin=False,
        rbac_unavailable=False,
        access_token="tok-user",
        principal_type="user",
    )
    base.update(over)
    return SimpleNamespace(**base)


def _rbac(**over) -> dict:
    base = {
        "id": "user-1",
        "email": "u@delpi.local",
        "name": "User",
        "roles": [],
        "groups": [],
        "permissions": ["tv-dashboard.write"],
        "is_superadmin": False,
    }
    base.update(over)
    return base


class _RecordingWrites:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple, dict]] = []

    def __getattr__(self, name: str):
        def _fake(*args, **kwargs):
            self.calls.append((name, args, kwargs))
            if name.startswith("list_") or name.startswith("get_all"):
                return []
            if name in {"get_revision", "playlist_revision"}:
                return 1
            return {
                "id": str(uuid4()),
                "name": kwargs.get("name") or "repro",
                "publicToken": "repro-token",
                "accessRole": "owner",
            }

        return _fake


def _patch_notify(monkeypatch, *route_modules) -> None:
    for mod in route_modules:
        for attr in (
            "_notify_library",
            "notify_presentation_changed",
            "notify_playlist_library_changed",
        ):
            if hasattr(mod, attr):
                monkeypatch.setattr(mod, attr, lambda *a, **k: None)


# ------------------------------------------------------------------
# Gate unit contract (real implementation, fresh-RBAC seam controlled)
# ------------------------------------------------------------------


def test_gate_denies_service_principal(monkeypatch):
    with pytest.raises(GovernedWriteAuthzError) as exc:
        _sync_gate(_service_user())
    assert exc.value.status_code == 403
    assert exc.value.code == "PRINCIPAL_TYPE_DENIED"


def test_gate_denies_missing_principal():
    with pytest.raises(GovernedWriteAuthzError) as exc:
        _sync_gate(None)
    assert exc.value.status_code == 401


def test_gate_denies_missing_bearer():
    user = _human_user(access_token=None)
    with pytest.raises(GovernedWriteAuthzError) as exc:
        _sync_gate(user)
    assert exc.value.status_code == 401


def test_gate_fetches_fresh_rbac_with_user_token(monkeypatch):
    seen: dict = {}

    async def _fake(token):
        seen["token"] = token
        return _rbac()

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    fresh = _sync_gate(_human_user(), permission=sec.TV_WRITE)
    assert seen["token"] == "tok-user"
    assert fresh.permissions == ["tv-dashboard.write"]
    assert fresh.principal_type == "user"


def test_gate_accepts_bearer_from_authorization_header(monkeypatch):
    async def _fake(token):
        assert token == "hdr-tok"
        return _rbac()

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    user = _human_user(access_token=None)
    fresh = _sync_gate(user, authorization="Bearer hdr-tok")
    assert fresh.id == "user-1"


def test_gate_revoked_permission_denies(monkeypatch):
    """Permission revoked in Core: fresh answer lacks TV_WRITE -> deny even
    though the cached principal still claims it."""

    async def _fake(token):
        return _rbac(permissions=[], is_superadmin=False)

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    with pytest.raises(GovernedWriteAuthzError) as exc:
        _sync_gate(_human_user(permissions=["tv-dashboard.write"]))
    assert exc.value.status_code == 403
    assert exc.value.code == "PERMISSION_DENIED"


def test_gate_revoked_superadmin_denies(monkeypatch):
    """Stale is_superadmin on the cached principal is not honored."""

    async def _fake(token):
        return _rbac(permissions=[], is_superadmin=False)

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    with pytest.raises(GovernedWriteAuthzError):
        _sync_gate(_human_user(is_superadmin=True))


def test_gate_core_unavailable_fails_closed(monkeypatch):
    async def _fake(token):
        raise RuntimeError("core down")

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    with pytest.raises(GovernedWriteAuthzError) as exc:
        _sync_gate(_human_user())
    assert exc.value.status_code == 503
    assert exc.value.code == "AUTHZ_UNAVAILABLE"


def test_gate_human_superadmin_fresh_allowed(monkeypatch):
    async def _fake(token):
        return _rbac(permissions=[], is_superadmin=True)

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    fresh = _sync_gate(_human_user(permissions=[]))
    assert fresh.is_superadmin is True


def test_gate_async_variant(monkeypatch):
    async def _fake(token):
        return _rbac()

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    import asyncio

    fresh = asyncio.run(_real_async_gate(_human_user(), permission=sec.TV_WRITE))
    assert fresh.id == "user-1"


# ------------------------------------------------------------------
# SEC-REPRO-1: service principal denied on every material write surface
# ------------------------------------------------------------------


def test_service_token_gpt_prepare_denied(client, monkeypatch):
    resp = client.post(
        "/gpt-actions/v1/changes/preview",
        headers=_svc_headers(),
        json={"target": {}, "ops": [{"op": "create_playlist", "name": "x"}]},
    )
    assert resp.status_code == 403, resp.json()


def test_service_token_gpt_commit_now_denied(client, monkeypatch):
    resp = client.post(
        "/gpt-actions/v1/changes/preview",
        headers=_svc_headers(),
        json={
            "target": {},
            "ops": [{"op": "create_playlist", "name": "x"}],
            "commit_now": True,
            "confirmation": {"confirmed": True},
            "idempotency_key": "k",
        },
    )
    assert resp.status_code == 403, resp.json()


def test_service_token_gpt_commit_denied(client, monkeypatch):
    resp = client.post(
        "/gpt-actions/v1/changes/commit",
        headers=_svc_headers(),
        json={
            "proposal_handle": "x",
            "confirmation": {"confirmed": True},
            "idempotency_key": "k",
        },
    )
    assert resp.status_code == 403, resp.json()


def test_service_token_playlist_create_denied(client):
    resp = client.post(
        "/playlists", headers=_svc_headers(), json={"name": "svc"}
    )
    assert resp.status_code == 403


def test_service_token_foreign_playlist_delete_denied(client, monkeypatch):
    resp = client.delete(f"/playlists/{uuid4()}", headers=_svc_headers())
    assert resp.status_code == 403


def test_service_token_presentation_mutations_denied(client):
    resp = client.post(
        f"/playlists/{uuid4()}/slides/{uuid4()}/presentation-mutations",
        headers=_svc_headers(),
        json={"ops": [{"op": "noop"}]},
    )
    assert resp.status_code == 403


def test_service_token_template_create_denied(client):
    resp = client.post(
        "/slide-templates",
        headers=_svc_headers(),
        json={"label": "x", "nativeConfig": {}, "nativeScreenKey": "custom_message"},
    )
    assert resp.status_code == 403


def test_service_token_builder_session_denied(client):
    resp = client.post("/data/builder/sessions", headers=_svc_headers())
    assert resp.status_code == 403


# ------------------------------------------------------------------
# SEC-REPRO-2: freshness end-to-end through the real gate + middleware
# ------------------------------------------------------------------


def _patch_jwt_validate(monkeypatch):
    from delpi_auth.middleware import fastapi_auth as fa

    monkeypatch.setattr(
        fa,
        "validate_token",
        lambda token: {"sub": "user-1", "email": "u@delpi.local"},
    )


def _restore_real_gate(monkeypatch):
    monkeypatch.setattr(sec, "require_fresh_write_authorization", _real_sync_gate)
    monkeypatch.setattr(sec, "arequire_fresh_write_authorization", _real_async_gate)


def test_fresh_granted_write_succeeds(client, monkeypatch):
    """Positive control: human + fresh TV_WRITE -> write reaches boundary."""
    from tv_app.interface.http.routes import playlist_routes as routes

    _restore_real_gate(monkeypatch)
    _patch_jwt_validate(monkeypatch)

    async def _fake(token):
        return _rbac()

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    writes = _RecordingWrites()
    monkeypatch.setattr(routes, "_writes", writes)
    _patch_notify(monkeypatch, routes)

    resp = client.post(
        "/playlists",
        headers={"Authorization": "Bearer tok-user"},
        json={"name": "ok"},
    )
    assert resp.status_code == 201, resp.json()
    assert "create_playlist" in [n for n, _, _ in writes.calls]


def test_fresh_revoked_write_denied(client, monkeypatch):
    """Case: cached principal had TV_WRITE; fresh Core says revoked -> 403."""
    from tv_app.interface.http.routes import playlist_routes as routes

    _restore_real_gate(monkeypatch)
    _patch_jwt_validate(monkeypatch)

    async def _fake(token):
        return _rbac(permissions=[])

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    writes = _RecordingWrites()
    monkeypatch.setattr(routes, "_writes", writes)

    resp = client.post(
        "/playlists",
        headers={"Authorization": "Bearer tok-user"},
        json={"name": "denied"},
    )
    assert resp.status_code == 403
    assert not writes.calls


def test_fresh_core_down_write_denied(client, monkeypatch):
    """Core unavailable -> fail closed even if a stale cache would serve."""
    from tv_app.interface.http.routes import playlist_routes as routes

    _restore_real_gate(monkeypatch)
    _patch_jwt_validate(monkeypatch)

    async def _fake(token):
        raise RuntimeError("core down")

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    writes = _RecordingWrites()
    monkeypatch.setattr(routes, "_writes", writes)

    resp = client.post(
        "/playlists",
        headers={"Authorization": "Bearer tok-user"},
        json={"name": "denied"},
    )
    assert resp.status_code == 503
    assert not writes.calls


def test_gpt_commit_revoked_permission_denied(client, monkeypatch):
    """Proposal minted while authorized -> permission revoked -> commit 403."""
    from tv_app.application.gpt_actions.proposal import create_proposal
    from tv_app.application.gpt_actions.proposal_store import get_proposal_store
    from tv_app.interface.http.routes import gpt_actions_routes as routes

    _restore_real_gate(monkeypatch)
    _patch_jwt_validate(monkeypatch)

    calls: list[int] = []

    async def _fake(token):
        calls.append(1)
        return _rbac(permissions=[])

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)

    proposal = create_proposal(
        actor_id="user-1",
        target={},
        ops=[{"op": "create_playlist", "name": "x"}],
        operation_names=["create_playlist"],
        catalog_version="v",
        base_revision=None,
        risk="low",
        confirmation_policy="direct",
        side_effect_hints=[],
    )
    handle = get_proposal_store().put(proposal)

    writes = _RecordingWrites()
    monkeypatch.setattr(routes._dispatch._commit, "_writes", writes)

    resp = client.post(
        "/gpt-actions/v1/changes/commit",
        headers={"Authorization": "Bearer tok-user"},
        json={
            "proposal_handle": handle,
            "confirmation": {"confirmed": True},
            "idempotency_key": "k-revoke",
        },
    )
    assert resp.status_code == 403, resp.json()
    assert calls, "fresh RBAC fetch ran"
    assert not writes.calls


# ------------------------------------------------------------------
# S2S exception + SEC-REPRO-3 (orphan playlist claim)
# ------------------------------------------------------------------


def test_service_token_openapi_sync_still_allowed(client, monkeypatch):
    """INTERNAL ADMIN S2S contract: api-delpi -> /data/openapi/sync."""
    from tv_app.application.services import tv_openapi_catalog_sync_service as mod

    calls: list[bool] = []
    monkeypatch.setattr(
        mod.TvOpenApiCatalogSyncService,
        "sync_from_live_api",
        lambda self: calls.append(True) or {"ok": True},
    )
    resp = client.post("/data/openapi/sync", headers=_svc_headers())
    assert resp.status_code == 200, resp.json()
    assert calls


def test_service_principal_never_claims_orphan_playlist():
    """resolve() must not run try_claim_owner for service principals."""
    from tv_app.application.services.playlist_access_service import (
        PlaylistAccessService,
    )

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "ownerUserId": "", "createdBy": ""}

        def try_claim_owner(self, pid, actor):  # pragma: no cover - must not run
            raise AssertionError("service principal must not claim ownership")

    access = PlaylistAccessService(repo=_Repo()).resolve(uuid4(), _service_user())
    assert access.level == "owner"  # read-level access preserved for admin S2S


def test_human_admin_still_claims_orphan_playlist():
    from tv_app.application.services.playlist_access_service import (
        PlaylistAccessService,
    )

    claimed: list[tuple] = []

    class _Repo:
        def get_by_id(self, pid):
            return {"id": str(pid), "ownerUserId": "", "createdBy": ""}

        def try_claim_owner(self, pid, actor):
            claimed.append((pid, actor))
            return {"id": str(pid), "ownerUserId": actor}

    user = _human_user(is_superadmin=True)
    access = PlaylistAccessService(repo=_Repo()).resolve(uuid4(), user)
    assert claimed, "human admin keeps claim behavior"
    assert access.level == "owner"


# ------------------------------------------------------------------
# AUTHZ_UNAVAILABLE observability: diagnosable, redacted, contract intact
# ------------------------------------------------------------------

_AUTHZ_EVENT = "governed_write_authz_unavailable"
_BEARER_SENTINEL = "SUPER_SECRET_BEARER_SENTINEL"
_ACCESS_TOKEN_SENTINEL = "SUPER_SECRET_ACCESS_TOKEN_SENTINEL"


def _authz_events(caplog) -> list[logging.LogRecord]:
    return [
        r
        for r in caplog.records
        if r.name == sec.__name__ and r.getMessage().startswith(_AUTHZ_EVENT)
    ]


def _raising(exc: Exception):
    async def _fake(token):
        raise exc

    return _fake


def _call_gate(mode: str, user, **kwargs):
    if mode == "sync":
        return _sync_gate(user, **kwargs)
    return asyncio.run(_real_async_gate(user, **kwargs))


def _assert_unavailable_contract(exc: GovernedWriteAuthzError) -> None:
    assert exc.status_code == 503
    assert exc.code == "AUTHZ_UNAVAILABLE"
    assert str(exc) == "Serviço de autorização indisponível."


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_unexpected_rbac_error_emits_structured_event(monkeypatch, caplog, mode):
    caplog.set_level(logging.INFO, logger=sec.__name__)
    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _raising(httpx.ConnectTimeout("timed out")))

    with pytest.raises(GovernedWriteAuthzError) as exc:
        _call_gate(mode, _human_user(), permission=sec.TV_WRITE)

    _assert_unavailable_contract(exc.value)
    assert isinstance(exc.value.__cause__, httpx.ConnectTimeout)
    events = _authz_events(caplog)
    assert len(events) == 1
    record = events[0]
    message = record.getMessage()
    assert record.levelno == logging.ERROR
    assert record.exc_info is None
    for field in (
        "operation=fresh_write_authorization",
        f"mode={mode}",
        "permission=tv-dashboard.write",
        "dependency=core_rbac",
        "outcome=AUTHZ_UNAVAILABLE",
        "error_class=ConnectTimeout",
        "error_module=httpx",
        "downstream_status=-",
    ):
        assert field in message, (field, message)


def test_sync_gate_inside_event_loop_is_distinguishable(monkeypatch, caplog):
    """Incident class fixed by af250bc8d7: sync gate under a running loop."""
    caplog.set_level(logging.INFO, logger=sec.__name__)
    created: list = []

    async def _rbac_lookup():
        return _rbac()

    def _fake(token):
        created.append(_rbac_lookup())
        return created[-1]

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)

    async def _async_handler():
        return _real_sync_gate(_human_user())

    with pytest.raises(GovernedWriteAuthzError) as exc:
        asyncio.run(_async_handler())
    for coro in created:
        coro.close()

    assert created == [], "no RBAC lookup outside the app's worker-thread runtime"
    _assert_unavailable_contract(exc.value)
    message = _authz_events(caplog)[0].getMessage()
    assert "mode=sync" in message
    assert "error_class=NoEventLoopError" in message
    assert "error_module=anyio" in message
    assert "event_loop_running=True" in message


def test_downstream_core_status_is_distinguishable(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger=sec.__name__)
    monkeypatch.setattr(
        sec,
        "_fetch_fresh_rbac",
        _raising(RuntimeError("RBAC lookup failed with status 503")),
    )

    with pytest.raises(GovernedWriteAuthzError) as exc:
        _sync_gate(_human_user())

    _assert_unavailable_contract(exc.value)
    message = _authz_events(caplog)[0].getMessage()
    assert "error_class=RuntimeError" in message
    assert "event_loop_running=False" in message
    assert "downstream_status=503" in message


@pytest.mark.parametrize("mode", ["sync", "async"])
def test_authz_unavailable_log_never_contains_credentials(monkeypatch, caplog, mode):
    caplog.set_level(logging.DEBUG)
    leaky = httpx.LocalProtocolError(
        f"Illegal header value b'Bearer {_BEARER_SENTINEL} {_ACCESS_TOKEN_SENTINEL}'"
    )
    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _raising(leaky))
    user = _human_user(access_token=_ACCESS_TOKEN_SENTINEL)

    with pytest.raises(GovernedWriteAuthzError) as exc:
        _call_gate(mode, user, authorization=f"Bearer {_BEARER_SENTINEL}")

    _assert_unavailable_contract(exc.value)
    assert _authz_events(caplog), "event emitted"
    formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
    rendered = [formatter.format(r) for r in caplog.records]
    for sentinel in (_BEARER_SENTINEL, _ACCESS_TOKEN_SENTINEL):
        assert sentinel not in caplog.text
        assert sentinel not in str(exc.value)
        for record in caplog.records:
            assert sentinel not in record.getMessage()
            assert sentinel not in repr(record.args)
            assert sentinel not in repr(vars(record))
        assert all(sentinel not in line for line in rendered)


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(
    ("user", "authorization", "fresh", "status", "code"),
    [
        (None, None, None, 401, "UNAUTHENTICATED"),
        ("service", None, None, 403, "PRINCIPAL_TYPE_DENIED"),
        ("no_bearer", None, None, 401, "UNAUTHENTICATED"),
        ("human", None, {"permissions": []}, 403, "PERMISSION_DENIED"),
    ],
)
def test_expected_denials_are_not_classified_unavailable(
    monkeypatch, caplog, mode, user, authorization, fresh, status, code
):
    caplog.set_level(logging.DEBUG)
    principal = {
        None: None,
        "service": _service_user(),
        "no_bearer": _human_user(access_token=None),
        "human": _human_user(),
    }[user]

    async def _fake(token):
        return _rbac(**(fresh or {}))

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)

    with pytest.raises(GovernedWriteAuthzError) as exc:
        _call_gate(mode, principal, authorization=authorization)

    assert exc.value.status_code == status
    assert exc.value.code == code
    assert _authz_events(caplog) == []
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
