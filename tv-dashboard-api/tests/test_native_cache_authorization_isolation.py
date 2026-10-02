"""SEC-TV-002 — native cache identity must separate authorization contexts.

The native data cache forwards the caller JWT to permission/branch-scoped
api-delpi endpoints (admin preview without ``parity=tv``). A cache key that
only distinguishes ``user`` vs ``service`` would serve one editor's
authorized payload to a different editor without the downstream ever
evaluating their authorization.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

from tv_app.application.security.authorization_fingerprint import (
    build_authorization_fingerprint,
)
from tv_app.application.services.native_screen_cache_service import (
    build_native_data_cache_key,
    get_cached_native_data,
    reset_native_data_cache,
    set_cached_native_data,
)
from tv_app.application.services.native_screen_data_service import (
    NativeScreenDataService,
)


def _user(sub: str, permissions: list[str] | None = None):
    return SimpleNamespace(
        sub=sub,
        permissions=permissions or [],
        is_superadmin=False,
    )


def _key(authorization, user=None, service_context=None) -> str:
    return build_native_data_cache_key(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        authorization=authorization,
        user=user,
        service_context=service_context,
    )


def test_different_users_get_different_cache_keys():
    user_a = _user("user-a", ["tv-dashboard.view.consolidated"])
    user_b = _user("user-b", ["tv-dashboard.view.consolidated"])
    key_a = _key("Bearer jwt-a", user=user_a, service_context="user-preview")
    key_b = _key("Bearer jwt-b", user=user_b, service_context="user-preview")
    assert key_a != key_b


def test_same_user_different_token_shares_key():
    user_a = _user("user-a", ["tv-dashboard.view.consolidated"])
    key_session_1 = _key("Bearer jwt-session-1", user=user_a, service_context="user-preview")
    key_session_2 = _key("Bearer jwt-session-2", user=user_a, service_context="user-preview")
    assert key_session_1 == key_session_2


def test_service_consumers_share_key_across_playlists():
    key_public_1 = _key(None, user=None, service_context="presentation-service")
    key_public_2 = _key(None, user=None, service_context="presentation-service")
    assert key_public_1 == key_public_2


def test_different_permissions_get_different_keys():
    user_full = _user("user-a", ["perm.a", "perm.b"])
    user_limited = _user("user-a", ["perm.a"])
    assert _key("Bearer jwt", user=user_full) != _key("Bearer jwt", user=user_limited)


def test_user_scope_never_matches_service_scope():
    user_key = _key("Bearer jwt", user=_user("user-a"))
    service_key = _key(None, user=None)
    assert user_key != service_key


def test_raw_credential_never_in_key():
    raw_jwt = "Bearer eyJhbGciOi_SECRET_JWT_MATERIAL_xyz"
    key = _key(raw_jwt, user=_user("user-a"))
    assert "eyJhbGciOi_SECRET_JWT_MATERIAL_xyz" not in key
    assert "sha256:" in key


def test_credential_digest_fallback_when_identity_absent():
    anonymous = SimpleNamespace()
    key_a = _key("Bearer token-a", user=anonymous)
    key_b = _key("Bearer token-b", user=anonymous)
    assert key_a != key_b


def test_fingerprint_shared_with_data_block_key():
    user = _user("user-a", ["perm.x"])
    fp_native = build_authorization_fingerprint(
        authorization="Bearer jwt", user=user, service_context="user-preview"
    )
    from tv_app.application.services.comunicado_data_enrichment_service import (
        _build_data_cache_key,
    )

    data_key = json.loads(
        _build_data_cache_key(
            operation_id="op",
            params={},
            authorization="Bearer jwt",
            user=user,
            service_context="user-preview",
        )
    )
    assert data_key["authorizationFingerprint"] == f"sha256:{fp_native}"


def test_resolve_does_not_serve_other_users_cached_data(monkeypatch):
    calls: list[dict] = []

    class _Gateway:
        def fetch_oee_overview(self, branch=None, period_days=7, authorization=None):
            calls.append({"authorization": authorization})
            return {"oeePct": 82.5, "owner": authorization}

    service = NativeScreenDataService(gateway=_Gateway())
    reset_native_data_cache()
    user_a = _user("user-a")
    user_b = _user("user-b")

    first = service.resolve(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        authorization="Bearer jwt-a",
        user=user_a,
    )
    second = service.resolve(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        authorization="Bearer jwt-b",
        user=user_b,
    )
    third = service.resolve(
        screen_key="production_oee_overview",
        config={"branch": "01"},
        authorization="Bearer jwt-a2",
        user=user_a,
    )

    assert len(calls) == 2
    assert second["owner"] == "Bearer jwt-b"
    assert third["owner"] == "Bearer jwt-a"


def test_resolve_public_service_consumers_share_cache():
    calls: list[dict] = []

    class _Gateway:
        def fetch_oee_overview(self, branch=None, period_days=7, authorization=None):
            calls.append({})
            return {"oeePct": 82.5}

    service = NativeScreenDataService(gateway=_Gateway())
    reset_native_data_cache()
    service.resolve(screen_key="production_oee_overview", config={"branch": "01"})
    service.resolve(screen_key="production_oee_overview", config={"branch": "01"})
    assert len(calls) == 1
