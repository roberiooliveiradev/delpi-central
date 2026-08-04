from types import SimpleNamespace

import pytest

from delpi_auth.authorization import require_any_permission
from delpi_auth.middleware.fastapi_auth import map_authz_exception
from delpi_auth.request_context import reset_current_user, set_current_user


def test_map_authz_exception_known_messages():
    assert map_authz_exception(Exception("Forbidden")).status_code == 403
    assert map_authz_exception(Exception("Unauthorized")).status_code == 401
    assert map_authz_exception(Exception("Service Unavailable")).status_code == 503
    assert map_authz_exception(Exception("boom")) is None


def test_require_any_permission_forbidden_when_rbac_ok():
    token = set_current_user(
        SimpleNamespace(
            permissions=[],
            is_superadmin=False,
            rbac_unavailable=False,
        )
    )

    @require_any_permission(["pedidos-venda-abertos.access"])
    def endpoint():
        return "ok"

    with pytest.raises(Exception, match="Forbidden"):
        endpoint()

    reset_current_user(token)


def test_require_any_permission_service_unavailable_when_rbac_down():
    token = set_current_user(
        SimpleNamespace(
            permissions=[],
            is_superadmin=False,
            rbac_unavailable=True,
        )
    )

    @require_any_permission(["pedidos-venda-abertos.access"])
    def endpoint():
        return "ok"

    with pytest.raises(Exception, match="Service Unavailable"):
        endpoint()

    reset_current_user(token)


def test_require_any_permission_allows_when_present():
    token = set_current_user(
        SimpleNamespace(
            permissions=["pedidos-venda-abertos.access"],
            is_superadmin=False,
            rbac_unavailable=False,
        )
    )

    @require_any_permission(["pedidos-venda-abertos.access"])
    def endpoint():
        return "ok"

    assert endpoint() == "ok"
    reset_current_user(token)
