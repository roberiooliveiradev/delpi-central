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

from types import SimpleNamespace
from uuid import uuid4

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
        _real_sync_gate(_service_user())
    assert exc.value.status_code == 403
    assert exc.value.code == "PRINCIPAL_TYPE_DENIED"


def test_gate_denies_missing_principal():
    with pytest.raises(GovernedWriteAuthzError) as exc:
        _real_sync_gate(None)
    assert exc.value.status_code == 401


def test_gate_denies_missing_bearer():
    user = _human_user(access_token=None)
    with pytest.raises(GovernedWriteAuthzError) as exc:
        _real_sync_gate(user)
    assert exc.value.status_code == 401


def test_gate_fetches_fresh_rbac_with_user_token(monkeypatch):
    seen: dict = {}

    async def _fake(token):
        seen["token"] = token
        return _rbac()

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    fresh = _real_sync_gate(_human_user(), permission=sec.TV_WRITE)
    assert seen["token"] == "tok-user"
    assert fresh.permissions == ["tv-dashboard.write"]
    assert fresh.principal_type == "user"


def test_gate_accepts_bearer_from_authorization_header(monkeypatch):
    async def _fake(token):
        assert token == "hdr-tok"
        return _rbac()

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    user = _human_user(access_token=None)
    fresh = _real_sync_gate(user, authorization="Bearer hdr-tok")
    assert fresh.id == "user-1"


def test_gate_revoked_permission_denies(monkeypatch):
    """Permission revoked in Core: fresh answer lacks TV_WRITE -> deny even
    though the cached principal still claims it."""

    async def _fake(token):
        return _rbac(permissions=[], is_superadmin=False)

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    with pytest.raises(GovernedWriteAuthzError) as exc:
        _real_sync_gate(_human_user(permissions=["tv-dashboard.write"]))
    assert exc.value.status_code == 403
    assert exc.value.code == "PERMISSION_DENIED"


def test_gate_revoked_superadmin_denies(monkeypatch):
    """Stale is_superadmin on the cached principal is not honored."""

    async def _fake(token):
        return _rbac(permissions=[], is_superadmin=False)

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    with pytest.raises(GovernedWriteAuthzError):
        _real_sync_gate(_human_user(is_superadmin=True))


def test_gate_core_unavailable_fails_closed(monkeypatch):
    async def _fake(token):
        raise RuntimeError("core down")

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    with pytest.raises(GovernedWriteAuthzError) as exc:
        _real_sync_gate(_human_user())
    assert exc.value.status_code == 503
    assert exc.value.code == "AUTHZ_UNAVAILABLE"


def test_gate_human_superadmin_fresh_allowed(monkeypatch):
    async def _fake(token):
        return _rbac(permissions=[], is_superadmin=True)

    monkeypatch.setattr(sec, "_fetch_fresh_rbac", _fake)
    fresh = _real_sync_gate(_human_user(permissions=[]))
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
