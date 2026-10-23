from types import SimpleNamespace
from unittest.mock import MagicMock

from purchase_requests_app.application.use_cases.list_purchase_request_cost_centers_use_case import (
    ListPurchaseRequestCostCentersUseCase,
)


def _user(**overrides):
    base = dict(
        id="u1",
        sub="u1",
        is_superadmin=False,
        permissions=[
            "purchase-requests.access",
            "purchase-requests.unit.filial-01",
            "purchase-requests.unit.filial-02",
        ],
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _use_case(gateway=None, scope_repo=None):
    return ListPurchaseRequestCostCentersUseCase(
        gateway=gateway or MagicMock(),
        scope_repository=scope_repo or MagicMock(),
    )


def test_scoped_user_single_branch_forwards_scope_not_self_filter() -> None:
    gateway = MagicMock()
    gateway.list_cost_centers.return_value = {
        "items": [{"branch": "02", "code": "0413", "description": "Produção"}]
    }
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = [
        {"branch": "02", "cost_center_code": "0413"}
    ]
    user = _user(
        permissions=[
            "purchase-requests.access",
            "purchase-requests.unit.filial-02",
        ]
    )
    result = _use_case(gateway, scope_repo).execute(
        user=user,
        branches=["02"],
        date_from="2026-10-01",
        date_to="2026-10-31",
    )
    assert result["items"][0]["code"] == "0413"
    params = gateway.list_cost_centers.call_args.kwargs["params"]
    # Scope carried as plain codes (single branch) — never a cc_scope tuple.
    assert params["cost_centers"] == ["0413"]
    assert "cc_scope" not in params
    # The facet never accepts the user's own cost_center filter.
    assert "cost_center" not in params


def test_scoped_user_multi_branch_uses_cc_scope_tuples() -> None:
    gateway = MagicMock()
    gateway.list_cost_centers.return_value = {"items": []}
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = [
        {"branch": "01", "cost_center_code": "0413"},
        {"branch": "02", "cost_center_code": "0520"},
    ]
    result = _use_case(gateway, scope_repo).execute(
        user=_user(),
        branches=["01", "02"],
    )
    assert result["items"] == []
    params = gateway.list_cost_centers.call_args.kwargs["params"]
    scopes = params.get("cc_scope") or []
    assert {"01:0413", "02:0520"} == set(scopes)


def test_scoped_user_without_scope_rows_gets_empty() -> None:
    gateway = MagicMock()
    scope_repo = MagicMock()
    scope_repo.list_active_cost_centers_for_user.return_value = []
    result = _use_case(gateway, scope_repo).execute(
        user=_user(),
        branches=["01"],
    )
    assert result["items"] == []
    gateway.list_cost_centers.assert_not_called()


def test_unauthorized_user_is_denied() -> None:
    gateway = MagicMock()
    scope_repo = MagicMock()
    user = _user(permissions=["other.permission"])
    try:
        _use_case(gateway, scope_repo).execute(user=user, branches=["01"])
    except PermissionError:
        return
    raise AssertionError("expected PermissionError")
