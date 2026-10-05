"""Shared test seam for the governed-write authorization gate.

``core.security.require_fresh_write_authorization`` performs a fail-closed
fresh Core RBAC lookup and requires a bearer credential — neither is available
to pre-existing fixtures that construct ``SimpleNamespace`` users in-process.
This autouse fixture preserves the human-principal invariant and the
permission check (no Core call), so existing tests keep asserting their own
contract.

Security regression tests that must exercise freshness restore the real gate
via ``monkeypatch.setattr(sec, "require_fresh_write_authorization", <real>)``
and control ``sec._fetch_fresh_rbac`` directly.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _governed_write_legacy_gate(monkeypatch):
    import tv_app.core.security as sec

    def _legacy_gate(user, *, authorization=None, permission=sec.TV_WRITE):
        if getattr(user, "principal_type", "user") != "user":
            raise sec.GovernedWriteAuthzError(
                "Escrita governada exige principal de usuário final.",
                code="PRINCIPAL_TYPE_DENIED",
                status_code=403,
            )
        try:
            sec.assert_permission(user, permission)
        except PermissionError as exc:
            raise sec.GovernedWriteAuthzError(
                str(exc), code="PERMISSION_DENIED", status_code=403
            ) from exc
        return user

    async def _legacy_gate_async(user, *, authorization=None, permission=sec.TV_WRITE):
        return _legacy_gate(user, authorization=authorization, permission=permission)

    monkeypatch.setattr(sec, "require_fresh_write_authorization", _legacy_gate)
    monkeypatch.setattr(sec, "arequire_fresh_write_authorization", _legacy_gate_async)
