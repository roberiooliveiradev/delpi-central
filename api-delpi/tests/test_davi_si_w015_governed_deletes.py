"""W015 — DAVI delete tool: governed PREPARE/ACT for destructive SI ops.

Unit-level coverage with a fake owner client enforcing the same contracts
the SI API now enforces: in-transaction expected_xmin OCC, dependent-count
guards (409 on drift), hard-delete cascades, audited replace apply — plus
the sealed-proposal single-use/cross-actor/confirmation guarantees and
the execute/delete tool boundary (families are disjoint).
"""

from __future__ import annotations

import pytest

from strategic_indicators_client import StrategicIndicatorsApiError

from app.application.external_capabilities.governed_writes.errors import (
    CAPABILITY_NOT_ALLOWED,
    CONFIRMATION_REQUIRED,
    NOT_FOUND,
    PROPOSAL_ACTOR_MISMATCH,
    PROPOSAL_NOT_FOUND,
    PROPOSAL_STALE,
    VALIDATION,
    GovernedWriteError,
)
from app.application.external_capabilities.governed_writes.orchestrator import (
    DELETE_CAPABILITIES,
    WRITE_CAPABILITIES,
    DaviGovernedWriteOrchestrator,
    davi_execute,
    davi_delete,
)
from app.application.external_capabilities.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from app.application.external_capabilities.governed_writes.si_w015_capabilities import (
    SI_W015_DELETE_CAPABILITIES,
    SI_W015_WRITE_CAPABILITIES,
    SiW015WriteStack,
)

AUTH_OK = "Bearer user-a"
AUTH_OTHER = "Bearer user-b"
AUTH_DENIED = "Bearer user-denied"
ACTOR = "user-a@delpi"
ACTOR_B = "user-b@delpi"


def _goal(**kw):
    row = {
        "id": "g-1",
        "indicator_id": "ind-1",
        "department_id": "fin",
        "goal_year": 2025,
        "goal_label": "Meta",
        "goal_scope_branch": "",
        "version": 1,
        "is_active": True,
        "monthly_targets": [{"month": m, "value": 10} for m in range(1, 13)],
        "copied_from_goal_id": None,
        "row_xmin": "1001",
    }
    row.update(kw)
    return row


class FakeSiClient:
    """Owner double enforcing the W015 delete/replace contracts."""

    def __init__(self) -> None:
        self.goals: list[dict] = []
        self.departments = [
            {"department_id": "fin", "department_name": "Financeiro",
             "is_active": True, "row_xmin": "2001"},
        ]
        self.indicators = [
            {"indicator_id": "ind-1", "department_id": "fin",
             "indicator_name": "Margem", "is_active": True,
             "row_xmin": "3001"},
        ]
        self.delete_calls: list[dict] = []

    def _check(self, authorization: str) -> None:
        if authorization == AUTH_DENIED:
            raise StrategicIndicatorsApiError("denied", status_code=403)

    # ---- reads ----------------------------------------------------------
    def list_user_indicator_goals(
        self,
        *,
        authorization: str,
        indicator_id=None,
        goal_year=None,
        department_id=None,
        active_only=None,
    ):
        self._check(authorization)
        items = [
            dict(g)
            for g in self.goals
            if (indicator_id is None or g["indicator_id"] == indicator_id)
            and (goal_year is None or g["goal_year"] == goal_year)
            and (department_id is None or g["department_id"] == department_id)
            and (active_only is not True or g["is_active"])
        ]
        return {"items": items}

    def export_user_admin_config(self, *, authorization: str):
        self._check(authorization)
        return {
            "departments": [
                {k: v for k, v in d.items() if k != "row_xmin"}
                for d in self.departments
            ],
            "department_indicators": [
                {k: v for k, v in i.items() if k != "row_xmin"}
                for i in self.indicators
            ],
            "indicator_goals": [dict(g) for g in self.goals if g["is_active"]],
        }

    def list_user_admin_departments(self, *, authorization: str):
        self._check(authorization)
        return {"items": [dict(d) for d in self.departments]}

    def list_user_admin_department_indicators(
        self, *, authorization: str, department_id: str
    ):
        self._check(authorization)
        return {
            "items": [
                dict(i)
                for i in self.indicators
                if i["department_id"] == department_id
            ]
        }

    # ---- deletes (owner contract: xmin + dependent-count OCC) ----------
    def delete_user_indicator_goal(
        self, *, authorization: str, goal_id: str, expected_xmin=None,
        write_origin=None, correlation_id=None,
    ):
        self._check(authorization)
        self.delete_calls.append(
            {"kind": "goal", "id": goal_id, "expected_xmin": expected_xmin,
             "write_origin": write_origin, "correlation_id": correlation_id}
        )
        goal = next((g for g in self.goals if g["id"] == goal_id), None)
        if goal is None:
            raise StrategicIndicatorsApiError("not found", status_code=404)
        if expected_xmin is not None and goal["row_xmin"] != expected_xmin:
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        self.goals.remove(goal)
        for g in self.goals:
            if g.get("copied_from_goal_id") == goal_id:
                g["copied_from_goal_id"] = None
        return {"deleted": goal_id}

    def delete_user_admin_indicator(
        self, *, authorization: str, indicator_id: str, expected_xmin=None,
        expected_goal_count=None, write_origin=None, correlation_id=None,
    ):
        self._check(authorization)
        ind = next(
            (i for i in self.indicators if i["indicator_id"] == indicator_id),
            None,
        )
        if ind is None:
            raise StrategicIndicatorsApiError("not found", status_code=404)
        if expected_xmin is not None and ind["row_xmin"] != expected_xmin:
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        goals = [g for g in self.goals if g["indicator_id"] == indicator_id]
        if (expected_goal_count is not None
                and len(goals) != expected_goal_count):
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        self.goals = [
            g for g in self.goals if g["indicator_id"] != indicator_id
        ]
        self.indicators.remove(ind)
        return {"deleted": indicator_id}

    def delete_user_admin_department(
        self, *, authorization: str, department_id: str, expected_xmin=None,
        expected_indicator_count=None, expected_goal_count=None,
        write_origin=None, correlation_id=None,
    ):
        self._check(authorization)
        dept = next(
            (d for d in self.departments
             if d["department_id"] == department_id),
            None,
        )
        if dept is None:
            raise StrategicIndicatorsApiError("not found", status_code=404)
        if expected_xmin is not None and dept["row_xmin"] != expected_xmin:
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        inds = [i for i in self.indicators
               if i["department_id"] == department_id]
        goals = [g for g in self.goals if g["department_id"] == department_id]
        if (expected_indicator_count is not None
                and len(inds) != expected_indicator_count):
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        if (expected_goal_count is not None
                and len(goals) != expected_goal_count):
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        self.indicators = [
            i for i in self.indicators
            if i["department_id"] != department_id
        ]
        self.goals = [
            g for g in self.goals if g["department_id"] != department_id
        ]
        self.departments.remove(dept)
        return {"deleted": department_id}

    # ---- import replace ---------------------------------------------------
    def preview_user_admin_config_import(
        self, *, authorization: str, body
    ):
        self._check(authorization)
        bundle = (body or {}).get("bundle") or {}
        if "departments" not in bundle:
            return {"valid": False, "errors": ["departments ausente"],
                    "current_counts": {}, "planned": {}}
        current = {
            "departments": len(self.departments),
            "department_indicators": len(self.indicators),
            "indicator_goals": len(self.goals),
        }
        planned = {
            "departments": {
                "delete": current["departments"],
                "insert": len(bundle.get("departments") or []),
            },
            "department_indicators": {
                "delete": current["department_indicators"],
                "insert": len(bundle.get("department_indicators") or []),
            },
            "indicator_goals": {
                "delete": current["indicator_goals"],
                "insert": len(bundle.get("indicator_goals") or []),
            },
        }
        return {"valid": True, "errors": [],
                "current_counts": current, "planned": planned}

    def apply_user_admin_config_import(
        self, *, authorization: str, body,
        expected_counts=None, write_origin=None, correlation_id=None,
    ):
        self._check(authorization)
        bundle = (body or {}).get("bundle") or {}
        current = {
            "departments": len(self.departments),
            "department_indicators": len(self.indicators),
            "indicator_goals": len(self.goals),
        }
        if expected_counts and current != dict(expected_counts):
            raise StrategicIndicatorsApiError("conflict", status_code=409)
        self.departments = [
            {"department_id": d["department_id"],
             "department_name": d.get("department_name"),
             "is_active": True, "row_xmin": "5000"}
            for d in bundle.get("departments") or []
        ]
        self.indicators = [
            {"indicator_id": i["indicator_id"],
             "department_id": i["department_id"],
             "indicator_name": i.get("indicator_name"),
             "is_active": True, "row_xmin": "6000"}
            for i in bundle.get("department_indicators") or []
        ]
        self.goals = [
            _goal(id=g.get("id", f"g-{n}"),
                  indicator_id=g["indicator_id"],
                  department_id=g.get("department_id", "fin"),
                  row_xmin="7000")
            for n, g in enumerate(bundle.get("indicator_goals") or [])
        ]
        return {"applied": True}


@pytest.fixture()
def client(monkeypatch) -> FakeSiClient:
    monkeypatch.setenv("DAVI_GOVERNED_WRITE_HMAC_SECRET", "w015-test-secret")
    reset_proposal_store_for_tests()
    fake = FakeSiClient()
    yield fake
    reset_proposal_store_for_tests()


@pytest.fixture()
def orch(client: FakeSiClient) -> DaviGovernedWriteOrchestrator:
    return DaviGovernedWriteOrchestrator(
        w015_stack=SiW015WriteStack(client=client)
    )


def _prepare(orch, capability, args, *, allowed=DELETE_CAPABILITIES):
    return orch.prepare(
        capability=capability,
        args=args,
        actor_id=ACTOR,
        actor_email=ACTOR,
        authorization=AUTH_OK,
        allowed=allowed,
    )


def _act(orch, capability, proposal, *, allowed=DELETE_CAPABILITIES,
         actor_id=ACTOR):
    return orch.act(
        capability=capability,
        proposal_handle=proposal["proposal_handle"],
        proposal_id=None,
        confirm=True,
        actor_id=actor_id,
        authorization=AUTH_OK,
        allowed=allowed,
    )


# ------------------------------------------------------------------ sets


def test_delete_and_write_families_are_disjoint() -> None:
    assert not (SI_W015_DELETE_CAPABILITIES & WRITE_CAPABILITIES)
    assert SI_W015_DELETE_CAPABILITIES == set(DELETE_CAPABILITIES)
    assert SI_W015_WRITE_CAPABILITIES <= WRITE_CAPABILITIES
    assert "si.config.import_replace" in WRITE_CAPABILITIES


def test_execute_tool_rejects_delete_capability(orch) -> None:
    with pytest.raises(GovernedWriteError) as exc:
        orch.prepare(
            capability="si.goal.delete",
            args={"goal_id": "g-1"},
            actor_id=ACTOR,
            actor_email=ACTOR,
            authorization=AUTH_OK,
            allowed=WRITE_CAPABILITIES,
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED


def test_delete_tool_rejects_write_capability(orch) -> None:
    with pytest.raises(GovernedWriteError) as exc:
        _prepare(orch, "si.goal.update", {"goal_id": "g-1"})
    assert exc.value.code == CAPABILITY_NOT_ALLOWED


def test_delete_tool_rejects_import_replace() -> None:
    # Bounded execute capability — not a delete.
    assert "si.config.import_replace" not in DELETE_CAPABILITIES


# ------------------------------------------------------------- goal delete


def test_goal_delete_prepare_shows_impact_then_act(client, orch) -> None:
    client.goals = [
        _goal(id="g-1"),
        _goal(id="g-2", indicator_id="ind-2",
              copied_from_goal_id="g-1"),
    ]
    prepared = _prepare(orch, "si.goal.delete", {"goal_id": "g-1"})
    assert prepared["phase"] == "prepare"
    impact = prepared["consequential_impact"]
    assert impact["dependents"]["monthly_targets"] == 12
    assert impact["dependents"]["copied_from_references"] == 1
    assert "IRREVERSIBLE" in impact["reversibility"]
    assert prepared["confirmation_requirement"]["destructive"] is True

    result = _act(orch, "si.goal.delete", prepared)
    assert result["verified"] is True
    assert result["data"]["postcondition"] == "goal_absent"
    assert all(g["id"] != "g-1" for g in client.goals)
    # copied_from link cleared, not cascaded
    assert client.goals[0]["copied_from_goal_id"] is None
    call = client.delete_calls[0]
    assert call["expected_xmin"] == "1001"
    assert call["write_origin"] == "davi-mcp"


def test_goal_delete_unknown_target_prepare_fails(client, orch) -> None:
    with pytest.raises(GovernedWriteError) as exc:
        _prepare(orch, "si.goal.delete", {"goal_id": "g-none"})
    assert exc.value.code == NOT_FOUND


def test_goal_delete_act_requires_confirmation(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    prepared = _prepare(orch, "si.goal.delete", {"goal_id": "g-1"})
    with pytest.raises(GovernedWriteError) as exc:
        orch.act(
            capability="si.goal.delete",
            proposal_handle=prepared["proposal_handle"],
            proposal_id=None,
            confirm=None,
            actor_id=ACTOR,
            authorization=AUTH_OK,
            allowed=DELETE_CAPABILITIES,
        )
    assert exc.value.code == CONFIRMATION_REQUIRED
    assert client.goals  # nothing deleted


def test_goal_delete_stale_after_concurrent_update(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    prepared = _prepare(orch, "si.goal.delete", {"goal_id": "g-1"})
    client.goals[0]["row_xmin"] = "1002"  # concurrent update
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.delete", prepared)
    assert exc.value.code == PROPOSAL_STALE
    assert client.goals  # preserved


def test_goal_delete_stale_after_concurrent_delete(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    prepared = _prepare(orch, "si.goal.delete", {"goal_id": "g-1"})
    client.goals.clear()  # concurrent delete
    # fingerprint recompute sees absent row → stale, never reaches owner
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.delete", prepared)
    assert exc.value.code == PROPOSAL_STALE


def test_goal_delete_cross_actor_rejected(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    prepared = _prepare(orch, "si.goal.delete", {"goal_id": "g-1"})
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.delete", prepared, actor_id=ACTOR_B)
    assert exc.value.code == PROPOSAL_ACTOR_MISMATCH


def test_goal_delete_single_use_replay_rejected(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    prepared = _prepare(orch, "si.goal.delete", {"goal_id": "g-1"})
    _act(orch, "si.goal.delete", prepared)
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.delete", prepared)
    assert exc.value.code == PROPOSAL_NOT_FOUND


def test_delete_rejects_unknown_arguments(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    with pytest.raises(GovernedWriteError) as exc:
        _prepare(orch, "si.goal.delete",
                 {"goal_id": "g-1", "force": True})
    assert exc.value.code == VALIDATION


# -------------------------------------------------------- indicator delete


def test_indicator_delete_cascade_impact_and_act(client, orch) -> None:
    client.goals = [
        _goal(id="g-1"),
        _goal(id="g-2", indicator_id="ind-2", department_id="ops"),
    ]
    prepared = _prepare(orch, "si.indicator.delete",
                        {"indicator_id": "ind-1"})
    impact = prepared["consequential_impact"]
    assert impact["dependents"]["indicator_goals"] == 1
    assert impact["dependents"]["monthly_targets"] == 12
    assert impact["dependents"]["goal_versions"] == ["g-1"]

    result = _act(orch, "si.indicator.delete", prepared)
    assert result["data"]["postcondition"] == "indicator_and_goals_absent"
    assert not client.indicators
    assert [g["id"] for g in client.goals] == ["g-2"]


def test_indicator_delete_dependent_drift_is_stale(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    prepared = _prepare(orch, "si.indicator.delete",
                        {"indicator_id": "ind-1"})
    # New goal created on the indicator after PREPARE.
    client.goals.append(_goal(id="g-new", row_xmin="1009"))
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.indicator.delete", prepared)
    assert exc.value.code == PROPOSAL_STALE
    assert client.indicators and len(client.goals) == 2


def test_indicator_delete_owner_conflict_maps_typed(client, orch) -> None:
    """Owner-side count guard still fires when the BFF fingerprint can't
    see the change (e.g. xmin only) — maps to a typed conflict."""
    client.goals = [_goal(id="g-1")]
    stack = SiW015WriteStack(client=client)
    with pytest.raises(StrategicIndicatorsApiError) as exc:
        stack.execute(
            AUTH_OK,
            "si.indicator.delete",
            {"indicator_id": "ind-1", "expected_xmin": "3001",
             "expected_goal_count": 5},
            correlation_id="p-1",
        )
    assert exc.value.status_code == 409


# -------------------------------------------------------- department delete


def test_department_delete_cascade_impact_and_act(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    prepared = _prepare(orch, "si.department.delete",
                        {"department_id": "fin"})
    impact = prepared["consequential_impact"]
    assert impact["dependents"]["indicators"] == 1
    assert impact["dependents"]["indicator_goals"] == 1
    assert impact["dependents"]["indicator_ids"] == ["ind-1"]
    assert "kpi_impact" in impact

    result = _act(orch, "si.department.delete", prepared)
    assert result["data"]["postcondition"] == "department_and_indicators_absent"
    assert not client.departments and not client.indicators
    assert not client.goals


def test_department_delete_indicator_drift_is_stale(client, orch) -> None:
    prepared = _prepare(orch, "si.department.delete",
                        {"department_id": "fin"})
    client.indicators.append(
        {"indicator_id": "ind-2", "department_id": "fin",
         "indicator_name": "Novo", "is_active": True, "row_xmin": "3002"}
    )
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.department.delete", prepared)
    assert exc.value.code == PROPOSAL_STALE
    assert client.departments


# ------------------------------------------------------------- import replace


def test_import_replace_prepare_seals_export_and_planned(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    bundle = {
        "departments": [{"department_id": "com"}],
        "department_indicators": [
            {"indicator_id": "ind-9", "department_id": "com"}
        ],
        "indicator_goals": [{"id": "g-9", "indicator_id": "ind-9"}],
    }
    prepared = orch.prepare(
        capability="si.config.import_replace",
        args={"bundle": bundle},
        actor_id=ACTOR,
        actor_email=ACTOR,
        authorization=AUTH_OK,
        allowed=WRITE_CAPABILITIES,
    )
    impact = prepared["consequential_impact"]
    assert impact["mode"] == "replace"
    assert impact["current_counts"]["departments"] == 1
    assert impact["planned"]["departments"]["delete"] == 1
    ec = prepared["exact_change"]
    assert ec["body"]["mode"] == "replace"
    # recovery artifact sealed: pre-state export present in the proposal
    assert ec["recovery_export"]["departments"][0]["department_id"] == "fin"
    assert len(ec["recovery_export"]["indicator_goals"]) == 1

    result = orch.act(
        capability="si.config.import_replace",
        proposal_handle=prepared["proposal_handle"],
        proposal_id=None,
        confirm=True,
        actor_id=ACTOR,
        authorization=AUTH_OK,
        allowed=WRITE_CAPABILITIES,
    )
    assert result["data"]["postcondition"] == "catalog_counts_match_plan"
    assert client.departments[0]["department_id"] == "com"


def test_import_replace_rejects_invalid_bundle(client, orch) -> None:
    with pytest.raises(GovernedWriteError) as exc:
        orch.prepare(
            capability="si.config.import_replace",
            args={"bundle": "not-a-dict"},
            actor_id=ACTOR,
            actor_email=ACTOR,
            authorization=AUTH_OK,
            allowed=WRITE_CAPABILITIES,
        )
    assert exc.value.code == VALIDATION


def test_import_replace_owner_preview_rejection(client, orch) -> None:
    with pytest.raises(GovernedWriteError) as exc:
        orch.prepare(
            capability="si.config.import_replace",
            args={"bundle": {"department_indicators": []}},
            actor_id=ACTOR,
            actor_email=ACTOR,
            authorization=AUTH_OK,
            allowed=WRITE_CAPABILITIES,
        )
    assert exc.value.code == VALIDATION
    assert "departments ausente" in str(exc.value)


def test_import_replace_act_refuses_non_replace_body(client, orch) -> None:
    stack = SiW015WriteStack(client=client)
    with pytest.raises(GovernedWriteError) as exc:
        stack.execute(
            AUTH_OK,
            "si.config.import_replace",
            {"body": {"bundle": {}, "mode": "merge"}},
            correlation_id="p-1",
        )
    assert exc.value.code == VALIDATION


def test_import_replace_catalog_drift_stales_proposal(client, orch) -> None:
    bundle = {
        "departments": [{"department_id": "com"}],
        "department_indicators": [],
        "indicator_goals": [],
    }
    prepared = orch.prepare(
        capability="si.config.import_replace",
        args={"bundle": bundle},
        actor_id=ACTOR,
        actor_email=ACTOR,
        authorization=AUTH_OK,
        allowed=WRITE_CAPABILITIES,
    )
    # Concurrent catalog change between PREPARE and ACT.
    client.departments.append(
        {"department_id": "ops", "department_name": "Ops",
         "is_active": True, "row_xmin": "2002"}
    )
    with pytest.raises(GovernedWriteError) as exc:
        orch.act(
            capability="si.config.import_replace",
            proposal_handle=prepared["proposal_handle"],
            proposal_id=None,
            confirm=True,
            actor_id=ACTOR,
            authorization=AUTH_OK,
            allowed=WRITE_CAPABILITIES,
        )
    assert exc.value.code == PROPOSAL_STALE


# -------------------------------------------------------------- wiring entry


def test_davi_execute_entry_rejects_delete_cap(orch) -> None:
    with pytest.raises(GovernedWriteError) as exc:
        davi_execute(
            capability="si.department.delete",
            arguments={"department_id": "fin"},
            actor_id=ACTOR,
            authorization=AUTH_OK,
            orchestrator=orch,
        )
    assert exc.value.code == CAPABILITY_NOT_ALLOWED


def test_davi_delete_entry_routes_to_w015(client, orch) -> None:
    client.goals = [_goal(id="g-1")]
    prepared = davi_delete(
        capability="si.goal.delete",
        arguments={"goal_id": "g-1"},
        actor_id=ACTOR,
        authorization=AUTH_OK,
        orchestrator=orch,
    )
    assert prepared["phase"] == "prepare"
    result = davi_delete(
        capability="si.goal.delete",
        proposal_handle=prepared["proposal_handle"],
        confirm=True,
        actor_id=ACTOR,
        authorization=AUTH_OK,
        orchestrator=orch,
    )
    assert result["verified"] is True


def test_denied_actor_blocked_at_prepare(orch) -> None:
    with pytest.raises(GovernedWriteError) as exc:
        orch.prepare(
            capability="si.goal.delete",
            args={"goal_id": "g-1"},
            actor_id=ACTOR,
            actor_email=ACTOR,
            authorization=AUTH_DENIED,
            allowed=DELETE_CAPABILITIES,
        )
    assert exc.value.code == "forbidden"
