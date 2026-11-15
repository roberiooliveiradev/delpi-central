"""Authorization contract: user parity, fresh Core RBAC, fail-closed."""
import asyncio
from types import SimpleNamespace

import pytest

from linux_ops_mcp import server


def _identity(*, permission=True, principal="user", unavailable=False):
    return SimpleNamespace(
        user=SimpleNamespace(id="user-id", principal_type=principal,
                             rbac_unavailable=unavailable),
        authorization="Bearer test-user-token",
    )


def _fake_core(*, permissions=None, identity="user-id", unavailable=False):
    async def lookup(_token, *, force_refresh=False):
        assert force_refresh is True
        if unavailable:
            raise RuntimeError("service unavailable with sensitive payload")
        return {"id": identity, "permissions": list(permissions or ()), "is_superadmin": False}
    return lookup


def _run_auth(monkeypatch, identity, core):
    monkeypatch.setattr(server, "require_mcp_context", lambda: identity)
    monkeypatch.setattr(server, "load_user_rbac", core)
    return asyncio.run(server._context_authorization())


def test_valid_human_with_fresh_permissions(monkeypatch):
    _run_auth(monkeypatch, _identity(), _fake_core(
        permissions=("it-portal.access", "it-portal.servers.view")))


@pytest.mark.parametrize("identity,core", [
    (_identity(principal="service"), _fake_core(permissions=("it-portal.access", "it-portal.servers.view"))),
    (_identity(unavailable=True), _fake_core(permissions=("it-portal.access", "it-portal.servers.view"))),
    (_identity(), _fake_core(permissions=("it-portal.access",))),
    (_identity(), _fake_core(permissions=("it-portal.servers.view",))),
    (_identity(), _fake_core(permissions=("it-portal.access", "it-portal.servers.view"), identity="other-user")),
])
def test_denied_principal_permissions_and_identity(monkeypatch, identity, core):
    with pytest.raises(server.ReadError, match="forbidden"):
        _run_auth(monkeypatch, identity, core)


def test_core_outage_is_fail_closed(monkeypatch):
    with pytest.raises(RuntimeError):
        _run_auth(monkeypatch, _identity(), _fake_core(unavailable=True))


def test_error_envelope_never_exposes_upstream_or_token():
    assert server._safe_error(RuntimeError("Bearer private-secret")) == {
        "ok": False, "error": "read_unavailable"}
