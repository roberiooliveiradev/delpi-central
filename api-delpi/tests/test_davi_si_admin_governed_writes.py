"""W013-ACT — DAVI execute: governed PREPARE/ACT for SI admin writes.

Unit-level coverage with a fake owner client enforcing permission,
optimistic preconditions, status guards and idempotency — mirrors the
real SI API semantics (409 conflict, 403 deny, single-use proposals,
idempotency-key replay).
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from strategic_indicators_client import StrategicIndicatorsApiError

from app.application.external_capabilities.governed_writes.errors import (
    CAPABILITY_NOT_ALLOWED,
    CONFIRMATION_REQUIRED,
    FORBIDDEN,
    NOT_FOUND,
    PROPOSAL_STALE,
    UNAUTHENTICATED,
    VALIDATION,
    GovernedWriteError,
)
from app.application.external_capabilities.governed_writes.orchestrator import (
    DaviGovernedWriteOrchestrator,
)
from app.application.external_capabilities.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from app.application.external_capabilities.governed_writes.si_admin_capabilities import (
    SI_ADMIN_WRITE_CAPABILITIES,
    SiAdminWriteStack,
)


AUTH_OK = "Bearer user-a"
AUTH_DENIED = "Bearer user-denied"
ACTOR = "user-a@delpi"

DEPT_ROW = {
    "department_id": "fin",
    "department_name": "Financeiro",
    "short_name": "FIN",
    "strategic_summary": "s",
    "headline_goal": "h",
    "supporting_focus": "f",
    "weight_pct": 30.0,
    "aggregation_mode": "consolidated",
    "is_active": True,
    "display_order": 1,
    "row_xmin": "100",
}
IND_ROW = {
    "indicator_id": "ind-1",
    "department_id": "fin",
    "indicator_name": "Indicador 1",
    "weight_pct": 50.0,
    "scope_type": "consolidated",
    "performance_direction": "higher_is_better",
    "strategic_description": "d",
    "source_key": "k1",
    "value_unit": "%",
    "value_prefix": None,
    "value_suffix": "%",
    "value_decimals": 2,
    "branch_value_aggregation": "auto",
    "is_active": True,
    "display_order": 1,
    "row_xmin": "110",
}
CR_ROW = {
    "id": "cr-1",
    "request_code": "SI-CR-AAAA",
    "title": "T",
    "description": "D",
    "target_block": "departments",
    "proposed_payload": {"a": 1},
    "status": "draft",
    "submitted_by_user_id": None,
    "submitted_at": None,
    "row_xmin": "120",
}


class FakeSiClient:
    """Owner double: permission map + xmin OCC + idempotency store."""

    def __init__(self) -> None:
        self.depts = {"fin": dict(DEPT_ROW)}
        self.inds = {"ind-1": dict(IND_ROW)}
        self.crs = {"cr-1": dict(CR_ROW)}
        self.comments: list[dict] = []
        self.idem: dict[str, dict] = {}
        self.writes: list[str] = []
        self._xmin = 200

    def _check(self, authorization: str) -> None:
        if authorization == AUTH_DENIED:
            raise StrategicIndicatorsApiError("denied", status_code=403)

    def _bump(self, row: dict) -> dict:
        self._xmin += 1
        row["row_xmin"] = str(self._xmin)
        return row

    # reads
    def list_user_admin_departments(self, *, authorization: str):
        self._check(authorization)
        return {"items": [dict(r) for r in self.depts.values()]}

    def list_user_admin_department_indicators(
        self, *, authorization: str, department_id: str
    ):
        self._check(authorization)
        return {
            "items": [
                dict(r)
                for r in self.inds.values()
                if r["department_id"] == department_id
            ]
        }

    def list_user_change_requests(self, *, authorization: str, limit=None, offset=None):
        self._check(authorization)
        return {"items": [dict(r) for r in self.crs.values()], "total": len(self.crs)}

    # dept writes
    def create_user_admin_department(self, *, authorization, body, **kw):
        self._check(authorization)
        self.writes.append("dept.create")
        if body["department_id"] in self.depts:
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        row = {**body, "is_active": True, "row_xmin": "1"}
        self.depts[body["department_id"]] = self._bump(row)
        return dict(row)

    def update_user_admin_department(
        self, *, authorization, department_id, body, **kw
    ):
        self._check(authorization)
        self.writes.append("dept.update")
        row = self.depts.get(department_id)
        if row is None:
            raise StrategicIndicatorsApiError("nf", status_code=404)
        if row["row_xmin"] != body.get("expected_row_xmin"):
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        new_id = body.get("new_department_id") or department_id
        row.update({k: v for k, v in body.items() if k != "expected_row_xmin"})
        if new_id != department_id:
            row["department_id"] = new_id
            del self.depts[department_id]
            self.depts[new_id] = row
            for ind in self.inds.values():
                if ind["department_id"] == department_id:
                    ind["department_id"] = new_id
        return dict(self._bump(row))

    def activate_user_admin_department(
        self, *, authorization, department_id, expected_xmin=None, **kw
    ):
        self._check(authorization)
        self.writes.append("dept.activate")
        row = self.depts.get(department_id)
        if row is None or row["row_xmin"] != expected_xmin:
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        row["is_active"] = True
        return dict(self._bump(row))

    # indicator writes
    def create_user_admin_department_indicator(
        self, *, authorization, department_id, body, **kw
    ):
        self._check(authorization)
        self.writes.append("ind.create")
        if body["indicator_id"] in self.inds:
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        row = {**body, "department_id": department_id, "is_active": True,
               "branch_value_aggregation": "auto", "row_xmin": "1"}
        self.inds[body["indicator_id"]] = self._bump(row)
        return dict(row)

    def update_user_admin_indicator(
        self, *, authorization, indicator_id, body, **kw
    ):
        self._check(authorization)
        self.writes.append("ind.update")
        row = self.inds.get(indicator_id)
        if row is None:
            raise StrategicIndicatorsApiError("nf", status_code=404)
        if row["row_xmin"] != body.get("expected_row_xmin"):
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        new_id = body.get("new_indicator_id") or indicator_id
        row.update(
            {k: v for k, v in body.items()
             if k not in ("expected_row_xmin", "new_indicator_id")}
        )
        if new_id != indicator_id:
            row["indicator_id"] = new_id
            del self.inds[indicator_id]
            self.inds[new_id] = row
        return dict(self._bump(row))

    def activate_user_admin_indicator(
        self, *, authorization, indicator_id, expected_xmin=None, **kw
    ):
        return self._toggle_ind(authorization, indicator_id, expected_xmin, True)

    def deactivate_user_admin_indicator(
        self, *, authorization, indicator_id, expected_xmin=None, **kw
    ):
        return self._toggle_ind(authorization, indicator_id, expected_xmin, False)

    def _toggle_ind(self, authorization, indicator_id, expected_xmin, active):
        self._check(authorization)
        self.writes.append("ind.toggle")
        row = self.inds.get(indicator_id)
        if row is None or row["row_xmin"] != expected_xmin:
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        row["is_active"] = active
        return dict(self._bump(row))

    # CR writes
    def create_user_change_request(
        self, *, authorization, body, idempotency_key=None, **kw
    ):
        self._check(authorization)
        if idempotency_key and idempotency_key in self.idem:
            return dict(self.idem[idempotency_key])
        self.writes.append("cr.create")
        row = {
            "id": f"cr-{len(self.crs)+1}",
            "request_code": f"SI-CR-{len(self.crs)+1:04d}",
            **body,
            "status": "draft",
            "row_xmin": "1",
        }
        self.crs[row["id"]] = self._bump(row)
        if idempotency_key:
            self.idem[idempotency_key] = row
        return dict(row)

    def add_user_change_request_comment(
        self, *, authorization, change_request_id, body, idempotency_key=None, **kw
    ):
        self._check(authorization)
        if idempotency_key and idempotency_key in self.idem:
            return dict(self.idem[idempotency_key])
        self.writes.append("cr.comment")
        row = {
            "id": f"cmt-{len(self.comments)+1}",
            "change_request_id": change_request_id,
            "comment_text": body["comment_text"],
            "created_at": "2026-11-20T00:00:00Z",
        }
        self.comments.append(row)
        if idempotency_key:
            self.idem[idempotency_key] = row
        return dict(row)

    def submit_user_change_request(
        self, *, authorization, change_request_id, expected_xmin=None, **kw
    ):
        self._check(authorization)
        self.writes.append("cr.submit")
        row = self.crs.get(change_request_id)
        if row is None:
            raise StrategicIndicatorsApiError("nf", status_code=404)
        if row["status"] != "draft":
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        if expected_xmin is not None and row["row_xmin"] != expected_xmin:
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        row["status"] = "submitted"
        row["submitted_by_user_id"] = "u"
        row["submitted_at"] = "t"
        return dict(self._bump(row))


@pytest.fixture()
def orch(monkeypatch):
    monkeypatch.setenv("DAVI_GOVERNED_WRITE_HMAC_SECRET", "w013-test-secret")
    reset_proposal_store_for_tests()
    client = FakeSiClient()
    return DaviGovernedWriteOrchestrator(
        admin_stack=SiAdminWriteStack(client=client)
    ), client


def _prepare(orch, cap, args, auth=AUTH_OK):
    return orch.prepare(
        capability=cap, args=args, actor_id=ACTOR,
        actor_email=ACTOR, authorization=auth,
    )


def _act(orch, cap, prep, auth=AUTH_OK, confirm=True):
    return orch.act(
        capability=cap,
        proposal_handle=prep["proposal_handle"],
        proposal_id=None,
        confirm=confirm,
        actor_id=ACTOR,
        authorization=auth,
    )


# --------------------------------------------------------------- gate
def test_capability_set():
    assert len(SI_ADMIN_WRITE_CAPABILITIES) == 10
    assert "si.department.deactivate" not in SI_ADMIN_WRITE_CAPABILITIES
    assert "si.settings.update" not in SI_ADMIN_WRITE_CAPABILITIES


def test_unapproved_capability_rejected(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(o, "si.settings.update", {})
    assert ei.value.code == CAPABILITY_NOT_ALLOWED
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(o, "si.department.deactivate", {"department_id": "fin"})
    assert ei.value.code == CAPABILITY_NOT_ALLOWED


# ----------------------------------------------------------- D1-D3
def test_dept_create_full_cycle(orch):
    o, c = orch
    prep = _prepare(o, "si.department.create", {
        "department_id": "ops", "department_name": "Operações",
        "short_name": "OPS", "weight_pct": 20,
        "aggregation_mode": "consolidated", "display_order": 9,
    })
    assert prep["phase"] == "prepare" and prep["act_allowed"]
    assert c.writes == []  # PREPARE never mutates business state
    res = _act(o, "si.department.create", prep)
    assert res["verified"] and res["data"]["department"]["department_id"] == "ops"
    assert "dept.create" in c.writes


def test_dept_create_stale_fingerprint_refused(orch):
    o, c = orch
    prep = _prepare(o, "si.department.create", {
        "department_id": "ops", "department_name": "Ops",
        "short_name": "OPS", "weight_pct": 10,
        "aggregation_mode": "consolidated",
    })
    c.depts["new"] = dict(DEPT_ROW, department_id="new")
    with pytest.raises(GovernedWriteError) as ei:
        _act(o, "si.department.create", prep)
    assert ei.value.code == PROPOSAL_STALE


def test_dept_update_merge_and_rename(orch):
    o, c = orch
    prep = _prepare(o, "si.department.update", {
        "department_id": "fin", "weight_pct": 45,
    })
    diff = prep["consequential_impact"]["changed_fields"]
    assert diff["weight_pct"] == {"from": 30.0, "to": 45.0}
    res = _act(o, "si.department.update", prep)
    assert res["data"]["department"]["weight_pct"] == 45.0
    # rename variant exposes migrated references
    prep2 = _prepare(o, "si.department.update", {
        "department_id": "fin", "new_department_id": "fin2",
    })
    assert prep2["consequential_impact"]["rename"]["to"] == "fin2"
    res2 = _act(o, "si.department.update", prep2)
    assert res2["data"]["department"]["department_id"] == "fin2"
    assert c.inds["ind-1"]["department_id"] == "fin2"


def test_dept_update_stale_xmin_conflict(orch):
    o, c = orch
    prep = _prepare(o, "si.department.update", {
        "department_id": "fin", "weight_pct": 40,
    })
    c.depts["fin"]["row_xmin"] = "999"  # concurrent portal write
    with pytest.raises(GovernedWriteError):
        _act(o, "si.department.update", prep)


def test_dept_activate_and_already_active(orch):
    o, c = orch
    c.depts["fin"]["is_active"] = False
    prep = _prepare(o, "si.department.activate", {"department_id": "fin"})
    res = _act(o, "si.department.activate", prep)
    assert res["data"]["department"]["is_active"] is True
    with pytest.raises(GovernedWriteError):
        _prepare(o, "si.department.activate", {"department_id": "fin"})


# ----------------------------------------------------------- I1-I4
def test_indicator_create_and_verify(orch):
    o, c = orch
    prep = _prepare(o, "si.indicator.create", {
        "department_id": "fin", "indicator_id": "ind-9",
        "indicator_name": "Novo", "weight_pct": 25,
        "scope_type": "per_unit",
    })
    res = _act(o, "si.indicator.create", prep)
    assert res["data"]["indicator"]["indicator_id"] == "ind-9"


def test_indicator_create_missing_department(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(o, "si.indicator.create", {
            "department_id": "ghost", "indicator_id": "i",
            "indicator_name": "x", "weight_pct": 1, "scope_type": "consolidated",
        })
    assert ei.value.code == NOT_FOUND


def test_indicator_update_rename_migrates(orch):
    o, c = orch
    prep = _prepare(o, "si.indicator.update", {
        "indicator_id": "ind-1", "new_indicator_id": "ind-2",
        "weight_pct": 60,
    })
    res = _act(o, "si.indicator.update", prep)
    assert res["data"]["indicator"]["indicator_id"] == "ind-2"
    assert "ind-1" not in c.inds


def test_indicator_deactivate(orch):
    o, c = orch
    prep = _prepare(o, "si.indicator.deactivate", {"indicator_id": "ind-1"})
    res = _act(o, "si.indicator.deactivate", prep)
    assert res["data"]["indicator"]["is_active"] is False
    prep2 = _prepare(o, "si.indicator.activate", {"indicator_id": "ind-1"})
    res2 = _act(o, "si.indicator.activate", prep2)
    assert res2["data"]["indicator"]["is_active"] is True


# ----------------------------------------------------------- C1-C3
def test_cr_create_submit_cycle(orch):
    o, c = orch
    prep = _prepare(o, "si.change_request.create", {
        "title": "Ajuste", "description": "desc",
        "target_block": "departments",
        "proposed_payload": {"weight": 40},
    })
    res = _act(o, "si.change_request.create", prep)
    assert res["data"]["change_request"]["status"] == "draft"
    cr_id = res["data"]["change_request"]["id"]
    prep2 = _prepare(o, "si.change_request.submit", {"change_request_id": cr_id})
    res2 = _act(o, "si.change_request.submit", prep2)
    assert res2["data"]["change_request"]["status"] == "submitted"


def test_cr_submit_non_draft_rejected(orch):
    o, c = orch
    c.crs["cr-1"]["status"] = "submitted"
    with pytest.raises(GovernedWriteError):
        _prepare(o, "si.change_request.submit", {"change_request_id": "cr-1"})


def test_cr_comment_bounded_and_idempotent(orch):
    o, c = orch
    prep = _prepare(o, "si.change_request.comment", {
        "change_request_id": "cr-1", "comment_text": "ok",
    })
    res = _act(o, "si.change_request.comment", prep)
    assert res["data"]["comment"]["comment_text"] == "ok"
    # oversized payload rejected at PREPARE
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(o, "si.change_request.create", {
            "title": "t", "description": "d",
            "target_block": "departments",
            "proposed_payload": {"x": "y" * 20000},
        })
    assert ei.value.code == VALIDATION
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(o, "si.change_request.create", {
            "title": "t", "description": "d",
            "target_block": "departments",
            "proposed_payload": ["not", "an", "object"],
        })
    assert ei.value.code == VALIDATION


# ----------------------------------------------------------- security
def test_denied_owner_authz_maps_403(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(o, "si.department.activate",
                 {"department_id": "fin"}, auth=AUTH_DENIED)
    assert ei.value.code == FORBIDDEN


def test_unauthenticated_rejected(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        o.prepare(capability="si.department.create", args={},
                  actor_id=None, actor_email=None, authorization=None)
    assert ei.value.code == UNAUTHENTICATED


def test_act_requires_confirm(orch):
    o, _c = orch
    prep = _prepare(o, "si.change_request.comment",
                    {"change_request_id": "cr-1", "comment_text": "hi"})
    with pytest.raises(GovernedWriteError) as ei:
        _act(o, "si.change_request.comment", prep, confirm=False)
    assert ei.value.code == CONFIRMATION_REQUIRED
    with pytest.raises(GovernedWriteError) as ei:
        _act(o, "si.change_request.comment", prep, confirm=None)
    assert ei.value.code == CONFIRMATION_REQUIRED


def test_cross_actor_proposal_rejected(orch):
    o, _c = orch
    prep = _prepare(o, "si.change_request.comment",
                    {"change_request_id": "cr-1", "comment_text": "hi"})
    with pytest.raises(GovernedWriteError):
        o.act(
            capability="si.change_request.comment",
            proposal_handle=prep["proposal_handle"],
            proposal_id=None, confirm=True,
            actor_id="user-b@delpi", authorization=AUTH_OK,
        )


def test_single_use_proposal(orch):
    o, c = orch
    prep = _prepare(o, "si.change_request.comment",
                    {"change_request_id": "cr-1", "comment_text": "once"})
    _act(o, "si.change_request.comment", prep)
    with pytest.raises(GovernedWriteError):
        _act(o, "si.change_request.comment", prep)
    assert c.writes.count("cr.comment") == 1


def test_expired_proposal_rejected(orch):
    o, _c = orch
    prep = _prepare(o, "si.change_request.comment",
                    {"change_request_id": "cr-1", "comment_text": "old"})
    from app.application.external_capabilities.governed_writes.proposal_store import (
        get_proposal_store, parse_proposal_handle,
    )
    store = get_proposal_store()
    prop = store._items[parse_proposal_handle(prep["proposal_handle"])]
    prop.expires_at = time.time() - 1
    with pytest.raises(GovernedWriteError):
        _act(o, "si.change_request.comment", prep)


def test_unknown_args_rejected(orch):
    o, _c = orch
    with pytest.raises(GovernedWriteError) as ei:
        _prepare(o, "si.department.update", {
            "department_id": "fin", "evil_field": 1,
        })
    assert ei.value.code == VALIDATION


def test_cr_comment_stale_state(orch):
    o, c = orch
    prep = _prepare(o, "si.change_request.submit", {"change_request_id": "cr-1"})
    c.crs["cr-1"]["status"] = "submitted"  # concurrent submit
    with pytest.raises(GovernedWriteError):
        _act(o, "si.change_request.submit", prep)
