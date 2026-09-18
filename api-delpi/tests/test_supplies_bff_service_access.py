from types import SimpleNamespace
from unittest.mock import patch

from app.interface.http.routes.supplies.purchase_orders_branch_access import (
    branch_access_error,
)
from app.interface.http.supplies_bff_service_access import (
    is_trusted_supplies_bff_call,
    require_any_permission_or_supplies_bff,
)


def _request(*, caller: str, token: str, department_id: str | None = None):
    params = {}
    if department_id is not None:
        params["department_id"] = department_id
    return SimpleNamespace(
        headers={
            "X-Delpi-Caller-App": caller,
            "X-Delpi-Service-Token": token,
        },
        query_params=params,
    )


def test_trusted_call_requires_service_token_and_supplies_caller(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    trusted = _request(caller="supplies-api", token="svc-secret", department_id="supplies")
    other_caller = _request(caller="production-control-api", token="svc-secret")
    bad_token = _request(caller="supplies-api", token="nope")

    with patch(
        "app.interface.http.supplies_bff_service_access.get_request",
        return_value=trusted,
    ), patch(
        "app.interface.http.supplies_bff_service_access.get_caller_app",
        return_value="supplies-api",
    ):
        assert is_trusted_supplies_bff_call() is True
        assert is_trusted_supplies_bff_call(supplies_department_only=True) is True

    with patch(
        "app.interface.http.supplies_bff_service_access.get_request",
        return_value=other_caller,
    ), patch(
        "app.interface.http.supplies_bff_service_access.get_caller_app",
        return_value="production-control-api",
    ):
        assert is_trusted_supplies_bff_call() is False

    with patch(
        "app.interface.http.supplies_bff_service_access.get_request",
        return_value=bad_token,
    ), patch(
        "app.interface.http.supplies_bff_service_access.get_caller_app",
        return_value="supplies-api",
    ):
        assert is_trusted_supplies_bff_call() is False


def test_department_indicators_trust_does_not_cover_other_departments(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    financial = _request(
        caller="supplies-api",
        token="svc-secret",
        department_id="financial",
    )
    with patch(
        "app.interface.http.supplies_bff_service_access.get_request",
        return_value=financial,
    ), patch(
        "app.interface.http.supplies_bff_service_access.get_caller_app",
        return_value="supplies-api",
    ):
        assert is_trusted_supplies_bff_call(supplies_department_only=True) is False


def test_purchase_order_branch_gate_skips_only_for_trusted_bff():
    with patch(
        "app.interface.http.routes.supplies.purchase_orders_branch_access.is_trusted_supplies_bff_call",
        return_value=True,
    ):
        assert branch_access_error("01") is None
        assert branch_access_error("02") is None

    user = SimpleNamespace(is_superadmin=False, permissions=["supplies.access", "supplies.unit.filial-01"])
    with patch(
        "app.interface.http.routes.supplies.purchase_orders_branch_access.is_trusted_supplies_bff_call",
        return_value=False,
    ), patch(
        "app.interface.http.branch_access_gate.get_current_user",
        return_value=user,
    ), patch(
        "app.interface.http.branch_access_gate.has_permission",
        side_effect=lambda current_user, perm: perm in user.permissions,
    ):
        denied = branch_access_error("01")
        assert denied is not None
        assert denied.status_code == 403


def test_permission_decorator_runs_handler_for_trusted_bff_only():
    called = {"n": 0}

    @require_any_permission_or_supplies_bff(["api-delpi.access"])
    def handler():
        called["n"] += 1
        return "ok"

    with patch(
        "app.interface.http.supplies_bff_service_access.is_trusted_supplies_bff_call",
        return_value=True,
    ):
        assert handler() == "ok"
    assert called["n"] == 1

    user = SimpleNamespace(is_superadmin=False, permissions=[])
    with patch(
        "app.interface.http.supplies_bff_service_access.is_trusted_supplies_bff_call",
        return_value=False,
    ), patch(
        "delpi_auth.authorization.resolve_user_context",
        return_value=user,
    ):
        try:
            handler()
            raised = False
        except Exception as exc:
            raised = str(exc) == "Forbidden"
        assert raised is True
    assert called["n"] == 1
