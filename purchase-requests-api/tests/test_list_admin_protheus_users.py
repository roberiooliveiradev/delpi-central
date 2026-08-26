from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from purchase_requests_app.application.use_cases.list_admin_protheus_users_use_case import (
    ListAdminProtheusUsersUseCase,
)


def test_list_admin_protheus_users_without_cost_center_scope() -> None:
    gateway = MagicMock()
    gateway.list_requesters.return_value = {
        "items": [
            {
                "protheus_user_id": "000102",
                "code": "102",
                "name": "Maria",
            }
        ]
    }
    user = SimpleNamespace(
        id="admin1",
        sub="admin1",
        is_superadmin=False,
        permissions=["purchase-requests.admin", "purchase-requests.unit.filial-01"],
    )
    result = ListAdminProtheusUsersUseCase(gateway=gateway).execute(user=user, branch="01")
    assert result["items"][0]["protheus_user_id"] == "000102"
    params = gateway.list_requesters.call_args.kwargs["params"]
    assert params["branch"] == "01"
    assert "cost_centers" not in params
