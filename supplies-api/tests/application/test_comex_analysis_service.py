"""ComexAnalysisService unit tests — lifecycle, RBAC, sync, ownership."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.application.services.comex_analysis_service import (
    ComexAnalysisService,
    ComexConflictError,
    ComexForbiddenError,
    ComexNotFoundError,
    ComexValidationError,
)
from app.domain.entities import EffectiveUser
from app.infrastructure.gateways.market_data_gateway import (
    MarketDataGatewayError,
)

BUYER = "22222222-2222-2222-2222-222222222222"
GOV_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
VIEW_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"


def _user(*, manage=False) -> EffectiveUser:
    perms = {"supplies.access"}
    if manage:
        perms.add("supplies.manage")
    return EffectiveUser(
        id=BUYER, email="buyer@delpi.com.br", name="Buyer", permissions=perms
    )


def _gov(**over):
    base = {
        "governance_id": GOV_ID,
        "ncm_code": "74081190",
        "ncm_version": "NCM 2022",
        "description": "Fios de cobre",
        "family_code": "copper",
        "product_codes": [],
        "status": "pending_fiscal_review",
        "requested_by": BUYER,
        "requested_at": "2026-10-28T00:00:00+00:00",
        "decided_by": None,
        "decided_at": None,
        "revision": 1,
        "created_at": "2026-10-28T00:00:00+00:00",
        "updated_at": "2026-10-28T00:00:00+00:00",
    }
    base.update(over)
    return base


def _service(repo=None, market=None):
    repo = repo or MagicMock()
    market = market or MagicMock()
    return (
        ComexAnalysisService(
            repository=repo,
            delpi_gateway=MagicMock(),
            market_gateway=market,
        ),
        repo,
        market,
    )


# --- request_ncm ---------------------------------------------------------------


def test_request_rejects_non_ncm():
    svc, repo, _ = _service()
    with pytest.raises(ComexValidationError):
        svc.request_ncm(user=_user(), ncm_code="8544.49.00")
    repo.create_governance.assert_not_called()


def test_request_creates_pending():
    svc, repo, _ = _service()
    repo.create_governance.return_value = _gov()
    out = svc.request_ncm(user=_user(), ncm_code="74081190")
    assert out["status"] == "pending_fiscal_review"
    record = repo.create_governance.call_args.kwargs["record"]
    assert record["status"] == "pending_fiscal_review"
    assert record["requested_by"] == BUYER


def test_request_conflict_when_already_pending():
    svc, repo, _ = _service()
    repo.create_governance.return_value = _gov(_existing=True)
    with pytest.raises(ComexConflictError):
        svc.request_ncm(user=_user(), ncm_code="74081190")


def test_request_candidate_add_creates_catalog_row():
    svc, repo, _ = _service()
    repo.create_governance.return_value = _gov(status="candidate")
    out = svc.request_ncm(
        user=_user(), ncm_code="74081190", initial_status="candidate"
    )
    record = repo.create_governance.call_args.kwargs["record"]
    assert record["status"] == "candidate"
    assert out["status"] == "candidate"
    assert "already_registered" not in out


def test_request_candidate_add_is_idempotent_on_existing():
    svc, repo, _ = _service()
    repo.create_governance.return_value = _gov(
        status="approved", _existing=True
    )
    out = svc.request_ncm(
        user=_user(), ncm_code="74081190", initial_status="candidate"
    )
    assert out["already_registered"] is True
    assert out["status"] == "approved"
    repo.transition_governance.assert_not_called()


def test_request_candidate_add_does_not_reactivate_inactive():
    svc, repo, _ = _service()
    repo.create_governance.return_value = _gov(
        status="inactive", _existing=True
    )
    out = svc.request_ncm(
        user=_user(), ncm_code="74081190", initial_status="candidate"
    )
    assert out["already_registered"] is True
    assert out["status"] == "inactive"
    repo.transition_governance.assert_not_called()


def test_request_resubmits_rejected():
    svc, repo, market = _service()
    repo.create_governance.return_value = _gov(
        status="rejected", _existing=True
    )
    repo.get_governance.return_value = _gov(status="rejected")
    repo.transition_governance.return_value = _gov(
        status="pending_fiscal_review", revision=2
    )
    out = svc.request_ncm(user=_user(), ncm_code="74081190")
    assert out["status"] == "pending_fiscal_review"
    call = repo.transition_governance.call_args.kwargs
    assert call["to_status"] == "pending_fiscal_review"


# --- transition RBAC ------------------------------------------------------------


def test_access_cannot_approve():
    svc, repo, market = _service()
    repo.get_governance.return_value = _gov()
    with pytest.raises(ComexForbiddenError):
        svc.transition(
            user=_user(), governance_id=GOV_ID, to_status="approved"
        )
    market.put_ncm_allowlist.assert_not_called()


def test_illegal_transition_conflicts():
    svc, repo, _ = _service()
    repo.get_governance.return_value = _gov(status="approved")
    with pytest.raises(Exception) as exc:
        svc.transition(
            user=_user(manage=True), governance_id=GOV_ID, to_status="rejected"
        )
    assert "not allowed" in str(exc.value)


def test_manage_approves_and_syncs_allowlist():
    svc, repo, market = _service()
    repo.get_governance.return_value = _gov()
    repo.transition_governance.return_value = _gov(
        status="approved", revision=2
    )
    out = svc.transition(
        user=_user(manage=True), governance_id=GOV_ID, to_status="approved"
    )
    assert out["status"] == "approved"
    assert out["allowlist_sync"] == "synced"
    body = market.put_ncm_allowlist.call_args.args[1]
    assert market.put_ncm_allowlist.call_args.args[0] == "74081190"
    assert body["active"] is True
    assert body["ncm_version"] == "NCM 2022"
    repo.record_sync_event.assert_called_once()


def test_manage_deactivates_syncs_inactive():
    svc, repo, market = _service()
    repo.get_governance.return_value = _gov(status="approved")
    repo.transition_governance.return_value = _gov(
        status="inactive", revision=3
    )
    out = svc.transition(
        user=_user(manage=True), governance_id=GOV_ID, to_status="inactive"
    )
    assert out["allowlist_sync"] == "synced"
    assert market.put_ncm_allowlist.call_args.args[1]["active"] is False


def test_sync_failure_is_explicit_not_silent():
    svc, repo, market = _service()
    repo.get_governance.return_value = _gov()
    repo.transition_governance.return_value = _gov(status="approved")
    market.put_ncm_allowlist.side_effect = MarketDataGatewayError(
        "down", status_code=503
    )
    out = svc.transition(
        user=_user(manage=True), governance_id=GOV_ID, to_status="approved"
    )
    assert out["allowlist_sync"] == "failed"
    event = repo.record_sync_event.call_args.kwargs
    assert event["event_type"] == "allowlist_sync_failed"


def test_transition_not_found():
    svc, repo, _ = _service()
    repo.get_governance.return_value = None
    with pytest.raises(ComexNotFoundError):
        svc.transition(
            user=_user(), governance_id=GOV_ID, to_status="approved"
        )


# --- views -----------------------------------------------------------------------


def test_view_payload_validates_metric_and_mode():
    svc, _, _ = _service()
    with pytest.raises(ComexValidationError):
        svc.create_view(
            user=_user(), body={"name": "x", "selected_metrics": ["bogus"]}
        )
    with pytest.raises(ComexValidationError):
        svc.create_view(user=_user(), body={"name": "x", "view_mode": "pie"})
    with pytest.raises(ComexValidationError):
        svc.create_view(user=_user(), body={"selected_metrics": []})


def test_view_validates_ncm_format():
    svc, repo, _ = _service()
    with pytest.raises(ComexValidationError):
        svc.create_view(
            user=_user(),
            body={"name": "x", "approved_ncm_references": ["8544.49"]},
        )
    repo.create_view.assert_not_called()


def test_view_create_stamps_owner():
    svc, repo, _ = _service()
    repo.create_view.return_value = {"view_id": VIEW_ID, "name": "ok"}
    svc.create_view(
        user=_user(),
        body={
            "name": "ok",
            "granularity": "year",
            "date_range": {"date_from": "2025-01-01", "date_to": "2026-01-01"},
        },
    )
    record = repo.create_view.call_args.kwargs["record"]
    assert record["owner_user_id"] == BUYER
    assert record["granularity"] == "year"
    assert record["date_range"]["date_from"] == "2025-01-01"


def test_other_users_view_is_404():
    svc, repo, _ = _service()
    repo.get_view.return_value = None
    with pytest.raises(ComexNotFoundError):
        svc.get_view(VIEW_ID, user=_user())


def test_delete_other_users_view_is_404():
    svc, repo, _ = _service()
    repo.delete_view.return_value = False
    with pytest.raises(ComexNotFoundError):
        svc.delete_view(VIEW_ID, user=_user())


# --- product proxy ----------------------------------------------------------------


def test_products_search_filters_param_keys():
    svc, repo, _ = _service()
    svc._delpi.get.return_value = {"data": {"items": [], "total": 0}}
    user = _user()
    user.access_token = "tok"
    svc.search_products(
        user=user,
        args={"description": "cobre", "product_type": "MP", "evil": "x"},
    )
    params = svc._delpi.get.call_args.kwargs["params"]
    assert params == {"description": "cobre", "product_type": "MP"}
    assert svc._delpi.get.call_args.kwargs["access_token"] == "tok"
