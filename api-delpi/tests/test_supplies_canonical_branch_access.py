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
    )


def test_canonical_access_does_not_open_branches_without_trusted_bff():
    user = SimpleNamespace(is_superadmin=False, permissions=["supplies.access"])
    contexts = _patches(user)
    with contexts[0], contexts[1]:
        assert branch_view_allowed("01") is False
        assert branch_view_allowed("02") is False


def test_unit_code_alone_does_not_open_branch():
    user = SimpleNamespace(is_superadmin=False, permissions=["supplies.unit.filial-01"])
    contexts = _patches(user)
    with contexts[0], contexts[1]:
        assert branch_view_allowed("01") is False
