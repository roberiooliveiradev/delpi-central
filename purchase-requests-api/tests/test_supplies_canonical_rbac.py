from types import SimpleNamespace

from purchase_requests_app.application.security.purchase_requests_permissions import (
    has_access,
    has_branch_access,
    has_view_all,
)
from purchase_requests_app.application.security.supplies_portal_context import (
    authorize_portal_branches,
    bind_http_request,
    is_trusted_supplies_bff_call,
    reset_http_request,
)
from purchase_requests_app.application.services.purchase_request_scope_resolver import (
    PurchaseRequestScopeResolver,
)


def _user(*codes: str):
    return SimpleNamespace(is_superadmin=False, permissions=set(codes), id="user-1")


def _request(*, caller: str, token: str):
    return SimpleNamespace(
        headers={
            "X-Delpi-Caller-App": caller,
            "X-Delpi-Service-Token": token,
        }
    )


def test_supplies_access_alone_does_not_open_standalone_scope():
    user = _user("supplies.access")
    assert has_access(user) is False
    assert has_view_all(user) is False
    assert has_branch_access(user, "01") is False
    assert has_branch_access(user, "02") is False


def test_standalone_access_still_needs_unit_permission():
    user = _user("purchase-requests.access")
    assert has_access(user) is True
    assert has_branch_access(user, "01") is False
    user_unit = _user("purchase-requests.access", "purchase-requests.unit.filial-01")
    assert has_branch_access(user_unit, "01") is True
    assert has_branch_access(user_unit, "02") is False


def test_standalone_view_all_widens_cost_centers_only():
    user = _user("purchase-requests.view-all")
    assert has_view_all(user) is True
    assert has_access(user) is False


def test_manage_only_is_not_sc_access():
    user = _user("supplies.manage")
    assert has_access(user) is False
    assert has_view_all(user) is False
    assert has_branch_access(user, "01") is False


def test_deleted_supplies_view_all_does_not_grant_scope():
    user = _user("supplies.purchase-requests.view-all", "supplies.unit.filial-01")
    assert has_view_all(user) is False
    assert has_access(user) is False
    assert has_branch_access(user, "01") is False


def test_trusted_bff_requires_caller_and_service_token(monkeypatch):
    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    trusted = bind_http_request(_request(caller="supplies-api", token="svc-secret"))
    try:
        assert is_trusted_supplies_bff_call() is True
    finally:
        reset_http_request(trusted)

    wrong_caller = bind_http_request(_request(caller="commercial-api", token="svc-secret"))
    try:
        assert is_trusted_supplies_bff_call() is False
    finally:
        reset_http_request(wrong_caller)

    bad_token = bind_http_request(_request(caller="supplies-api", token="nope"))
    try:
        assert is_trusted_supplies_bff_call() is False
    finally:
        reset_http_request(bad_token)

    monkeypatch.delenv("API_DELPI_INTERNAL_SERVICE_TOKEN", raising=False)
    missing = bind_http_request(_request(caller="supplies-api", token="svc-secret"))
    try:
        assert is_trusted_supplies_bff_call() is False
    finally:
        reset_http_request(missing)


def test_portal_branches_accept_product_scope_and_reject_unknown():
    assert authorize_portal_branches(["01"]) == ["01"]
    assert authorize_portal_branches(["02", "01"]) == ["02", "01"]
    try:
        authorize_portal_branches(["99"])
        raised = False
    except ValueError:
        raised = True
    assert raised is True


def test_portal_global_skips_cost_center_fail_closed():
    user = _user("supplies.access")
    resolver = PurchaseRequestScopeResolver()
    resolution = resolver.resolve(
        user=user,
        branch="01",
        scope_rows=[],
        portal_global=True,
    )
    assert resolution.view_all is True
    assert resolver.effective_cost_centers(resolution, branch="01") is None

    standalone = resolver.resolve(
        user=_user("purchase-requests.access"),
        branch="01",
        scope_rows=[],
        portal_global=False,
    )
    assert standalone.view_all is False
    assert resolver.effective_cost_centers(standalone, branch="01") == []


def test_direct_supplies_access_does_not_activate_portal_list():
    from purchase_requests_app.application.use_cases.list_purchase_requests_use_case import (
        ListPurchaseRequestsUseCase,
    )

    use_case = ListPurchaseRequestsUseCase(
        gateway=SimpleNamespace(),
        scope_repository=SimpleNamespace(list_active_cost_centers_for_user=lambda _user_id: []),
    )
    try:
        use_case.execute(user=_user("supplies.access"), branches=["01"])
        raised = False
    except PermissionError:
        raised = True
    assert raised is True


def test_trusted_bff_lists_without_cost_center_scope(monkeypatch):
    from purchase_requests_app.application.use_cases.list_purchase_requests_use_case import (
        ListPurchaseRequestsUseCase,
    )

    monkeypatch.setenv("API_DELPI_INTERNAL_SERVICE_TOKEN", "svc-secret")
    captured: dict = {}

    class Gateway:
        def list_lines(self, *, params):
            captured["params"] = dict(params)
            return {"lines": [], "total": 0}

    use_case = ListPurchaseRequestsUseCase(
        gateway=Gateway(),
        scope_repository=SimpleNamespace(list_active_cost_centers_for_user=lambda _user_id: []),
    )
    token = bind_http_request(_request(caller="supplies-api", token="svc-secret"))
    try:
        result = use_case.execute(user=_user("supplies.access"), branches=["01", "02"])
    finally:
        reset_http_request(token)
    assert result["total"] == 0
    assert "cost_centers" not in captured["params"]
    assert "cc_scope" not in captured["params"]
