from types import SimpleNamespace
from unittest.mock import patch

from app.interface.http.routes.supplies.purchase_orders_branch_access import (
    branch_view_allowed,
)


def _patches(user):
    side = lambda current_user, perm: perm in user.permissions
    return (
        patch(
            "app.interface.http.branch_access_gate.get_current_user",
            return_value=user,
        ),
        patch(
            "app.interface.http.branch_access_gate.has_permission",
            side_effect=side,
        ),
        patch(
            "app.interface.http.routes.supplies.purchase_orders_branch_access.get_current_user",
            return_value=user,
        ),
        patch(
            "app.interface.http.routes.supplies.purchase_orders_branch_access.has_permission",
            side_effect=side,
        ),
    )


def test_canonical_access_is_not_global_branch():
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["supplies.access", "supplies.unit.filial-01"],
    )
    contexts = _patches(user)
    with contexts[0], contexts[1], contexts[2], contexts[3]:
        assert branch_view_allowed("01") is True
        assert branch_view_allowed("02") is False


def test_access_without_unit_denied():
    user = SimpleNamespace(is_superadmin=False, permissions=["supplies.access"])
    contexts = _patches(user)
    with contexts[0], contexts[1], contexts[2], contexts[3]:
        assert branch_view_allowed("01") is False
