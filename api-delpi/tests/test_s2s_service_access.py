from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import HTTPException

from delpi_auth.service_errors import (
    ServiceAuthConfigError,
    ServiceClientDeniedError,
    ServiceScopeDeniedError,
    ServiceTokenInvalidError,
)
from delpi_auth.service_identity import ServiceIdentity

from app.interface.http import s2s_service_access
from app.interface.http.s2s_service_access import (
    require_s2s_or_any_permission,
    require_s2s_service,
)

IDENTITY = ServiceIdentity(
    client_id="supplies-api",
    subject="service-account-subject",
    scopes=frozenset({"suppliers.read"}),
    audience=("api-delpi",),
    issuer="https://portal.example/auth/realms/delpi",
)


def _request(*, s2s_header: str | None = None, extra_headers=None):
    headers = dict(extra_headers or {})
    if s2s_header is not None:
        headers["X-Delpi-Service-Authorization"] = s2s_header
    return SimpleNamespace(headers=headers, state=SimpleNamespace())


def _validator(*, identity=IDENTITY, error=None):
    validator = Mock()
    if error is not None:
        validator.validate.side_effect = error
    else:
        validator.validate.return_value = identity
    return validator


def _use(request, validator=None):
    patches = [
        patch.object(s2s_service_access, "get_request", return_value=request),
    ]
    if validator is not None:
        patches.append(
            patch.object(
                s2s_service_access.ServiceTokenValidator,
                "from_env",
                return_value=validator,
            )
        )
    return patches


class _PatchAll:
    def __init__(self, patches):
        self._patches = patches

    def __enter__(self):
        for patcher in self._patches:
            patcher.start()
        return self

    def __exit__(self, *exc):
        for patcher in reversed(self._patches):
            patcher.stop()


def _call(handler):
    try:
        return ("ok", handler())
    except HTTPException as exc:
        return ("http", exc.status_code)
    except Exception as exc:
        return ("exc", str(exc))


def test_strict_allows_valid_service_credential():
    @require_s2s_service(required_scopes=("suppliers.read",))
    def handler():
        return "done"

    request = _request(s2s_header="Bearer svc-jwt")
    validator = _validator()
    with _PatchAll(_use(request, validator)):
        assert handler() == "done"
    validator.validate.assert_called_once_with(
        "svc-jwt", required_scopes=("suppliers.read",), allowed_clients=None
    )
    assert request.state.service_identity is IDENTITY


def test_strict_rejects_missing_header():
    @require_s2s_service()
    def handler():
        return "done"

    with _PatchAll(_use(_request())):
        assert _call(handler) == ("http", 401)


def test_strict_rejects_malformed_header():
    @require_s2s_service()
    def handler():
        return "done"

    request = _request(s2s_header="opaque-shared-secret")
    with _PatchAll(_use(request)):
        assert _call(handler) == ("http", 401)


def test_strict_maps_client_and_scope_denials_to_403():
    @require_s2s_service(required_scopes=("suppliers.read",))
    def handler():
        return "done"

    request = _request(s2s_header="Bearer svc-jwt")
    for error in (ServiceClientDeniedError(), ServiceScopeDeniedError()):
        with _PatchAll(_use(request, _validator(error=error))):
            assert _call(handler) == ("http", 403)


def test_strict_maps_invalid_token_to_401():
    @require_s2s_service()
    def handler():
        return "done"

    request = _request(s2s_header="Bearer svc-jwt")
    with _PatchAll(_use(request, _validator(error=ServiceTokenInvalidError()))):
        assert _call(handler) == ("http", 401)


def test_strict_maps_missing_config_to_503_fail_closed():
    @require_s2s_service()
    def handler():
        return "done"

    request = _request(s2s_header="Bearer svc-jwt")
    with _PatchAll(_use(request, _validator(error=ServiceAuthConfigError("missing")))):
        assert _call(handler) == ("http", 503)


def test_strict_rejects_request_without_context():
    @require_s2s_service()
    def handler():
        return "done"

    with _PatchAll(_use(None)):
        assert _call(handler) == ("http", 401)


def test_dual_allows_service_credential_and_records_identity():
    @require_s2s_or_any_permission(
        ["api-delpi.access"], required_scopes=("suppliers.read",)
    )
    def handler():
        return "done"

    request = _request(
        s2s_header="Bearer svc-jwt",
        extra_headers={"X-Delpi-Caller-App": "anything"},
    )
    with _PatchAll(_use(request, _validator())):
        assert handler() == "done"
    assert request.state.service_identity is IDENTITY


def test_dual_rejects_wrong_service_client():
    @require_s2s_or_any_permission(["api-delpi.access"])
    def handler():
        return "done"

    request = _request(s2s_header="Bearer svc-jwt")
    with _PatchAll(_use(request, _validator(error=ServiceClientDeniedError()))):
        assert _call(handler) == ("http", 403)


def test_dual_rejects_legacy_service_principal_without_s2s_header():
    @require_s2s_or_any_permission(["api-delpi.access"])
    def handler():
        return "done"

    legacy_principal = SimpleNamespace(principal_type="service", is_superadmin=True)
    with _PatchAll(_use(_request())), patch.object(
        s2s_service_access, "resolve_user_context", return_value=legacy_principal
    ):
        assert _call(handler) == ("http", 403)


def test_dual_user_path_uses_permission_guard():
    @require_s2s_or_any_permission(["api-delpi.access"])
    def handler():
        return "done"

    allowed_user = SimpleNamespace(
        principal_type="user",
        is_superadmin=False,
        permissions=["api-delpi.access"],
        rbac_unavailable=False,
    )
    denied_user = SimpleNamespace(
        principal_type="user",
        is_superadmin=False,
        permissions=[],
        rbac_unavailable=False,
    )
    with _PatchAll(
        _use(_request())
        + [
            patch.object(
                s2s_service_access, "resolve_user_context", return_value=allowed_user
            ),
            patch("delpi_auth.authorization.resolve_user_context", return_value=allowed_user),
        ]
    ):
        assert handler() == "done"

    with _PatchAll(
        _use(_request())
        + [
            patch.object(
                s2s_service_access, "resolve_user_context", return_value=denied_user
            ),
            patch("delpi_auth.authorization.resolve_user_context", return_value=denied_user),
        ]
    ):
        assert _call(handler) == ("exc", "Forbidden")


def test_dual_unauthenticated_request_denied():
    @require_s2s_or_any_permission(["api-delpi.access"])
    def handler():
        return "done"

    with _PatchAll(
        _use(_request())
        + [
            patch.object(s2s_service_access, "resolve_user_context", return_value=None),
            patch("delpi_auth.authorization.resolve_user_context", return_value=None),
        ]
    ):
        assert _call(handler) == ("exc", "Unauthorized")


def test_dual_supports_async_handlers():
    @require_s2s_or_any_permission(["api-delpi.access"])
    async def handler():
        return "done"

    request = _request(s2s_header="Bearer svc-jwt")
    with _PatchAll(_use(request, _validator())):
        import asyncio

        assert asyncio.run(handler()) == "done"
