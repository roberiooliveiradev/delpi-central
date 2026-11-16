"""W012 — DAVI semantic execute tool: governed PREPARE/ACT for SI goals.

Unit-level coverage with a fake owner client enforcing permission,
optimistic preconditions and authoritative state — mirrors the real SI
API semantics (409 conflict, 403 deny, single-use proposals).
"""

from __future__ import annotations

import time
from typing import Any

import pytest

from strategic_indicators_client import StrategicIndicatorsApiError

from app.application.external_capabilities.governed_writes.errors import (
    CAPABILITY_NOT_ALLOWED,
    CONFLICT,
    CONFIRMATION_REQUIRED,
    FORBIDDEN,
    PROPOSAL_ACTOR_MISMATCH,
    PROPOSAL_EXPIRED,
    PROPOSAL_NOT_FOUND,
    PROPOSAL_STALE,
    UNAUTHENTICATED,
    UNKNOWN_RESULT,
    VALIDATION,
    GovernedWriteError,
)
from app.application.external_capabilities.governed_writes.orchestrator import (
    DaviGovernedWriteOrchestrator,
    davi_execute,
)
from app.application.external_capabilities.governed_writes.proposal_store import (
    get_proposal_store,
    mint_proposal_handle,
    reset_proposal_store_for_tests,
)
from app.application.external_capabilities.governed_writes.si_goal_capabilities import (
    SiGoalWriteStack,
)


AUTH_OK = "Bearer user-a"
AUTH_OTHER = "Bearer user-b"
AUTH_DENIED = "Bearer user-denied"


def _goal_row(
    goal_id: str = "g-1",
    *,
    version: int = 1,
    is_active: bool = False,
    xmin: str = "100",
    **overrides: Any,
) -> dict[str, Any]:
    row = {
        "id": goal_id,
        "indicator_id": "ind-1",
        "goal_year": 2027,
        "goal_label": "Meta 2027",
        "goal_value": 100.0,
        "goal_periodicity": "monthly",
        "goal_mode": "standard",
        "goal_scope_branch": "01",
        "monthly_targets": [],
        "version": version,
        "is_active": is_active,
        "valid_from": None,
        "valid_to": None,
        "notes": None,
        "row_xmin": xmin,
    }
    row.update(overrides)
    return row


class FakeSiClient:
    """Owner double: permission map + xmin OCC + create-scope guard."""

    def __init__(self, rows: list[dict] | None = None) -> None:
        self.rows = {r["id"]: dict(r) for r in (rows or [])}
        self.writes: list[tuple[str, str | None, dict]] = []
        self.fail_write_with: Exception | None = None
        self.fail_read_after_write = False
        self._xmin_seq = 200
        self._create_seq = 0

    # -- reads ----------------------------------------------------------
    def list_user_indicator_goals(
        self,
        *,
        authorization: str,
        indicator_id: str | None = None,
        goal_year: int | None = None,
    ) -> dict[str, Any]:
        if authorization == AUTH_DENIED:
            raise StrategicIndicatorsApiError("denied", status_code=403)
        items = [
            dict(r)
            for r in self.rows.values()
            if (indicator_id is None or r["indicator_id"] == indicator_id)
            and (goal_year is None or r["goal_year"] == goal_year)
        ]
        return {"items": items}

    # -- writes ---------------------------------------------------------
    def _check_auth(self, authorization: str) -> None:
        if authorization == AUTH_DENIED:
            raise StrategicIndicatorsApiError("denied", status_code=403)

    def _bump(self, row: dict) -> dict:
        self._xmin_seq += 1
        row["row_xmin"] = str(self._xmin_seq)
        return row

    def create_user_indicator_goal(
        self, *, authorization: str, body: dict
    ) -> dict[str, Any]:
        self._check_auth(authorization)
        if self.fail_write_with:
            raise self.fail_write_with
        expected_max = body.get("expected_max_version")
        scope = [
            r
            for r in self.rows.values()
            if r["indicator_id"] == body["indicator_id"]
            and r["goal_year"] == body["goal_year"]
            and r["goal_scope_branch"] == body["goal_scope_branch"]
        ]
        current_max = max((int(r["version"]) for r in scope), default=0)
        if expected_max is not None and expected_max != current_max:
            raise StrategicIndicatorsApiError("stale scope", status_code=409)
        self._create_seq += 1
        new_id = f"g-new-{self._create_seq}"
        for r in scope:
            if r["is_active"]:
                r["is_active"] = False
                self._bump(r)
        row = _goal_row(
            new_id,
            version=current_max + 1,
            is_active=True,
            indicator_id=body["indicator_id"],
            goal_year=body["goal_year"],
            goal_label=body["goal_label"],
            goal_value=body["goal_value"],
            goal_periodicity=body["goal_periodicity"],
            goal_mode=body["goal_mode"],
            goal_scope_branch=body["goal_scope_branch"],
            monthly_targets=list(body.get("monthly_targets") or []),
            notes=body.get("notes"),
        )
        self._bump(row)
        self.rows[new_id] = row
        self.writes.append(("create", authorization, dict(body)))
        return dict(row)

    def update_user_indicator_goal(
        self, *, authorization: str, goal_id: str, body: dict
    ) -> dict[str, Any]:
        self._check_auth(authorization)
        if self.fail_write_with:
            raise self.fail_write_with
        row = self.rows.get(goal_id)
        if row is None:
            raise StrategicIndicatorsApiError("not found", status_code=404)
        expected = body.get("expected_row_xmin")
        if expected is not None and expected != row["row_xmin"]:
            raise StrategicIndicatorsApiError("stale row", status_code=409)
        for key in (
            "goal_label",
            "goal_value",
            "goal_periodicity",
            "goal_mode",
            "goal_scope_branch",
            "notes",
            "valid_from",
            "valid_to",
        ):
            if key in body:
                row[key] = body[key]
        if "monthly_targets" in body:
            row["monthly_targets"] = list(body["monthly_targets"])
        self._bump(row)
        self.writes.append(("update", authorization, dict(body)))
        return dict(row)

    def activate_user_indicator_goal(
        self, *, authorization: str, goal_id: str, expected_xmin: str | None = None
    ) -> dict[str, Any]:
        self._check_auth(authorization)
        if self.fail_write_with:
            raise self.fail_write_with
        return self._toggle(authorization, goal_id, True, expected_xmin, "activate")

    def deactivate_user_indicator_goal(
        self, *, authorization: str, goal_id: str, expected_xmin: str | None = None
    ) -> dict[str, Any]:
        self._check_auth(authorization)
        if self.fail_write_with:
            raise self.fail_write_with
        return self._toggle(authorization, goal_id, False, expected_xmin, "deactivate")

    def _toggle(self, authorization, goal_id, active, expected_xmin, tag):
        row = self.rows.get(goal_id)
        if row is None:
            raise StrategicIndicatorsApiError("not found", status_code=404)
        if expected_xmin is not None and expected_xmin != row["row_xmin"]:
            raise StrategicIndicatorsApiError("stale row", status_code=409)
        if active:
            for r in self.rows.values():
                if (
                    r is not row
                    and r["is_active"]
                    and r["indicator_id"] == row["indicator_id"]
                    and r["goal_year"] == row["goal_year"]
                    and r["goal_scope_branch"] == row["goal_scope_branch"]
                ):
                    r["is_active"] = False
                    self._bump(r)
        row["is_active"] = active
        self._bump(row)
        self.writes.append((tag, authorization, {"goal_id": goal_id}))
        return dict(row)


@pytest.fixture(autouse=True)
def _clean_store(monkeypatch):
    # The proposal HMAC is fail-closed without a real secret — provide a
    # dedicated test secret so PREPARE can mint handles.
    monkeypatch.setenv("DAVI_GOVERNED_WRITE_HMAC_SECRET", "w012-test-secret")
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


def _orchestrator(client: FakeSiClient) -> DaviGovernedWriteOrchestrator:
    return DaviGovernedWriteOrchestrator(si_stack=SiGoalWriteStack(client=client))


# ---------------------------------------------------------------------------
# PREPARE
# ---------------------------------------------------------------------------


def test_prepare_create_seals_proposal_without_write() -> None:
    client = FakeSiClient(rows=[_goal_row("g-1", version=3, is_active=True)])
    orch = _orchestrator(client)
    out = orch.prepare(
        capability="si.goal.create",
        args={
            "indicator_id": "ind-1",
            "goal_year": 2027,
            "goal_label": "Nova meta",
            "goal_value": 42.0,
            "goal_periodicity": "monthly",
            "goal_scope_branch": "01",
        },
        actor_id="user-a",
        actor_email="a@x",
        authorization=AUTH_OK,
    )
    assert out["phase"] == "prepare"
    assert out["act_allowed"] is True
    assert out["proposal_handle"].startswith("")
    assert out["expected_postcondition"]["version"] == 4
    assert out["consequential_impact"]["deactivates_existing_versions"] == [
        {"id": "g-1", "version": 3}
    ]
    assert client.writes == []  # PREPARE never mutates business state


def test_prepare_rejects_unknown_capability_and_delete() -> None:
    orch = _orchestrator(FakeSiClient())
    for cap in ("si.goal.delete", "si.department.update", "http.post", "read"):
        with pytest.raises(GovernedWriteError) as exc:
            orch.prepare(
                capability=cap,
                args={},
                actor_id="user-a",
                actor_email=None,
                authorization=AUTH_OK,
            )
        assert exc.value.code == CAPABILITY_NOT_ALLOWED


def test_prepare_validates_curve_and_args() -> None:
    orch = _orchestrator(FakeSiClient())
    bad = {
        "indicator_id": "ind-1",
        "goal_year": 2027,
        "goal_label": "x",
        "goal_periodicity": "monthly",
        "goal_mode": "monthly_curve",
        "monthly_targets": [{"month_number": 1, "target_value": 10}],
    }
    with pytest.raises(GovernedWriteError) as exc:
        orch.prepare(
            capability="si.goal.create",
            args=bad,
            actor_id="user-a",
            actor_email=None,
            authorization=AUTH_OK,
        )
    assert exc.value.code == VALIDATION


def test_prepare_denied_by_owner_authz() -> None:
    orch = _orchestrator(FakeSiClient())
    with pytest.raises(GovernedWriteError) as exc:
        orch.prepare(
            capability="si.goal.create",
            args={
                "indicator_id": "ind-1",
                "goal_year": 2027,
                "goal_label": "x",
                "goal_periodicity": "monthly",
            },
            actor_id="user-denied",
            actor_email=None,
            authorization=AUTH_DENIED,
        )
    assert exc.value.code == FORBIDDEN
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# ACT — happy path + postcondition
# ---------------------------------------------------------------------------


def _prepare(orch, capability, args, actor="user-a", auth=AUTH_OK):
    return orch.prepare(
        capability=capability,
        args=args,
        actor_id=actor,
        actor_email=None,
        authorization=auth,
    )


def _act(orch, capability, out, actor="user-a", auth=AUTH_OK):
    return orch.act(
        capability=capability,
        proposal_handle=out["proposal_handle"],
        proposal_id=None,
        confirm=True,
        actor_id=actor,
        authorization=auth,
    )


def test_act_create_executes_and_verifies() -> None:
    client = FakeSiClient()
    orch = _orchestrator(client)
    out = _prepare(
        orch,
        "si.goal.create",
        {
            "indicator_id": "ind-1",
            "goal_year": 2027,
            "goal_label": "Meta teste",
            "goal_value": 10.0,
            "goal_periodicity": "annual",
        },
    )
    result = _act(orch, "si.goal.create", out)
    assert result["verified"] is True
    assert result["phase"] == "act"
    assert len(client.writes) == 1
    tag, auth, body = client.writes[0]
    assert tag == "create" and auth == AUTH_OK
    assert body["expected_max_version"] == 0


def test_act_update_sealed_payload_not_model_payload() -> None:
    client = FakeSiClient(rows=[_goal_row("g-1", xmin="100")])
    orch = _orchestrator(client)
    out = _prepare(
        orch,
        "si.goal.update",
        {"goal_id": "g-1", "goal_label": "Novo rótulo"},
    )
    # PREPARE hydrated the full-form PUT body from the owner row.
    assert out["exact_change"]["goal_periodicity"] == "monthly"
    assert out["exact_change"]["expected_row_xmin"] == "100"
    result = _act(orch, "si.goal.update", out)
    assert result["verified"] is True
    assert result["data"]["goal"]["goal_label"] == "Novo rótulo"


def test_act_update_single_curve_month_preserves_other_11() -> None:
    curve = [{"month_number": m, "target_value": float(m)} for m in range(1, 13)]
    client = FakeSiClient(
        rows=[
            _goal_row(
                "g-1",
                goal_mode="monthly_curve",
                goal_value=0.0,
                monthly_targets=curve,
            )
        ]
    )
    orch = _orchestrator(client)
    out = _prepare(
        orch,
        "si.goal.update",
        {
            "goal_id": "g-1",
            "set_monthly_target": {"month_number": 5, "target_value": 999.0},
        },
    )
    sealed = out["exact_change"]["monthly_targets"]
    assert len(sealed) == 12
    assert sealed[4]["target_value"] == 999.0
    for t in sealed:
        if t["month_number"] != 5:
            assert t["target_value"] == float(t["month_number"])
    result = _act(orch, "si.goal.update", out)
    assert result["verified"] is True


def test_act_activate_supersedes_active_sibling() -> None:
    client = FakeSiClient(
        rows=[
            _goal_row("g-1", version=1, is_active=True),
            _goal_row("g-2", version=2, is_active=False),
        ]
    )
    orch = _orchestrator(client)
    out = _prepare(orch, "si.goal.activate", {"goal_id": "g-2"})
    assert out["consequential_impact"]["supersedes_active_versions"] == [
        {"id": "g-1", "version": 1}
    ]
    result = _act(orch, "si.goal.activate", out)
    assert result["verified"] is True
    assert client.rows["g-1"]["is_active"] is False
    assert client.rows["g-2"]["is_active"] is True


def test_act_deactivate_goal() -> None:
    client = FakeSiClient(rows=[_goal_row("g-1", is_active=True)])
    orch = _orchestrator(client)
    out = _prepare(orch, "si.goal.deactivate", {"goal_id": "g-1"})
    result = _act(orch, "si.goal.deactivate", out)
    assert result["verified"] is True
    assert result["data"]["goal"]["is_active"] is False


# ---------------------------------------------------------------------------
# ACT — safety gates
# ---------------------------------------------------------------------------


def test_act_requires_confirm_true() -> None:
    client = FakeSiClient()
    orch = _orchestrator(client)
    out = _prepare(
        orch,
        "si.goal.create",
        {
            "indicator_id": "i",
            "goal_year": 2027,
            "goal_label": "x",
            "goal_periodicity": "annual",
        },
    )
    for bad in (None, False):
        with pytest.raises(GovernedWriteError) as exc:
            orch.act(
                capability="si.goal.create",
                proposal_handle=out["proposal_handle"],
                proposal_id=None,
                confirm=bad,
                actor_id="user-a",
                authorization=AUTH_OK,
            )
        assert exc.value.code == CONFIRMATION_REQUIRED
    assert client.writes == []


def test_act_cross_user_proposal_rejected() -> None:
    orch = _orchestrator(FakeSiClient())
    out = _prepare(
        orch,
        "si.goal.create",
        {
            "indicator_id": "i",
            "goal_year": 2027,
            "goal_label": "x",
            "goal_periodicity": "annual",
        },
        actor="user-a",
    )
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.create", out, actor="user-b", auth=AUTH_OTHER)
    assert exc.value.code == PROPOSAL_ACTOR_MISMATCH


def test_act_tampered_handle_rejected() -> None:
    orch = _orchestrator(FakeSiClient())
    out = _prepare(
        orch,
        "si.goal.create",
        {
            "indicator_id": "i",
            "goal_year": 2027,
            "goal_label": "x",
            "goal_periodicity": "annual",
        },
    )
    handle = out["proposal_handle"]
    tampered = handle[:-2] + ("AA" if not handle.endswith("AA") else "BB")
    with pytest.raises(GovernedWriteError) as exc:
        orch.act(
            capability="si.goal.create",
            proposal_handle=tampered,
            proposal_id=None,
            confirm=True,
            actor_id="user-a",
            authorization=AUTH_OK,
        )
    assert exc.value.code == PROPOSAL_NOT_FOUND


def test_act_expired_proposal_rejected() -> None:
    orch = _orchestrator(FakeSiClient())
    out = _prepare(
        orch,
        "si.goal.create",
        {
            "indicator_id": "i",
            "goal_year": 2027,
            "goal_label": "x",
            "goal_periodicity": "annual",
        },
    )
    store = get_proposal_store()
    item = store.get(out["proposal_id"])
    assert item is not None
    item.expires_at = time.time() - 1
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.create", out)
    assert exc.value.code == PROPOSAL_EXPIRED


def test_act_stale_fingerprint_blocks_write() -> None:
    client = FakeSiClient(rows=[_goal_row("g-1", xmin="100")])
    orch = _orchestrator(client)
    out = _prepare(
        orch, "si.goal.update", {"goal_id": "g-1", "goal_label": "novo"}
    )
    # Concurrent writer changes the row between PREPARE and ACT.
    client.rows["g-1"]["goal_label"] = "raced"
    client.rows["g-1"]["row_xmin"] = "999"
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.update", out)
    assert exc.value.code == PROPOSAL_STALE
    assert client.writes == []


def test_act_owner_conflict_maps_409() -> None:
    """Race lands between the DAVI fingerprint re-check and the owner write:
    the owner-side xmin precondition is the authoritative gate → 409."""
    client = FakeSiClient(rows=[_goal_row("g-1", xmin="100")])
    stack = SiGoalWriteStack(client=client)
    orch = DaviGovernedWriteOrchestrator(si_stack=stack)
    out = _prepare(
        orch, "si.goal.update", {"goal_id": "g-1", "goal_label": "novo"}
    )
    # Mid-flight mutation after the fp re-check: recompute still sees the
    # PREPARE snapshot, but the owner row already moved.
    orig_recompute = stack.recompute_fingerprint
    sealed_fp = out["current_state_fingerprint"]

    def recompute_then_race(authorization, capability, exact_change):
        client.rows["g-1"]["row_xmin"] = "999"
        return sealed_fp

    stack.recompute_fingerprint = recompute_then_race  # type: ignore[method-assign]
    try:
        with pytest.raises(GovernedWriteError) as exc:
            _act(orch, "si.goal.update", out)
    finally:
        stack.recompute_fingerprint = orig_recompute  # type: ignore[method-assign]
    assert exc.value.code == CONFLICT


def test_act_consumed_proposal_replay_rejected() -> None:
    client = FakeSiClient(rows=[_goal_row("g-1", xmin="100")])
    orch = _orchestrator(client)
    out = _prepare(
        orch, "si.goal.update", {"goal_id": "g-1", "goal_label": "novo"}
    )
    first = _act(orch, "si.goal.update", out)
    assert first["verified"] is True
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.update", out)
    assert exc.value.code == PROPOSAL_NOT_FOUND
    assert len(client.writes) == 1  # replay never writes again


def test_act_unknown_result_when_transport_fails() -> None:
    client = FakeSiClient()
    orch = _orchestrator(client)
    out = _prepare(
        orch,
        "si.goal.create",
        {
            "indicator_id": "i",
            "goal_year": 2027,
            "goal_label": "x",
            "goal_periodicity": "annual",
        },
    )
    client.fail_write_with = StrategicIndicatorsApiError(
        "network timeout", status_code=None
    )
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.create", out)
    assert exc.value.code == UNKNOWN_RESULT
    # Consume-before-write: the consumed proposal cannot resubmit.
    with pytest.raises(GovernedWriteError) as exc2:
        _act(orch, "si.goal.create", out)
    assert exc2.value.code == PROPOSAL_NOT_FOUND


def test_act_owner_forbidden_propagates_as_typed_error() -> None:
    client = FakeSiClient(rows=[_goal_row("g-1", xmin="100")])
    orch = _orchestrator(client)
    out = _prepare(
        orch, "si.goal.update", {"goal_id": "g-1", "goal_label": "novo"}
    )
    # Permission revoked between PREPARE and ACT (authorization revalidated
    # at ACT through the owner call).
    with pytest.raises(GovernedWriteError) as exc:
        _act(orch, "si.goal.update", out, auth=AUTH_DENIED)
    assert exc.value.code == FORBIDDEN


def test_act_capability_mismatch_rejected() -> None:
    orch = _orchestrator(FakeSiClient(rows=[_goal_row("g-1")]))
    out = _prepare(
        orch, "si.goal.update", {"goal_id": "g-1", "goal_label": "novo"}
    )
    with pytest.raises(GovernedWriteError) as exc:
        orch.act(
            capability="si.goal.activate",
            proposal_handle=out["proposal_handle"],
            proposal_id=None,
            confirm=True,
            actor_id="user-a",
            authorization=AUTH_OK,
        )
    from app.application.external_capabilities.governed_writes.errors import (
        PROPOSAL_MISMATCH,
    )

    assert exc.value.code == PROPOSAL_MISMATCH


# ---------------------------------------------------------------------------
# entry point + proposal id recovery
# ---------------------------------------------------------------------------


def test_davi_execute_dispatches_prepare_and_act() -> None:
    client = FakeSiClient()
    orch = _orchestrator(client)
    out = davi_execute(
        capability="si.goal.create",
        arguments={
            "indicator_id": "i",
            "goal_year": 2027,
            "goal_label": "x",
            "goal_periodicity": "annual",
        },
        actor_id="user-a",
        authorization=AUTH_OK,
        orchestrator=orch,
    )
    assert out["phase"] == "prepare"
    # ACT via proposal_id recovery key (handle is re-minted internally).
    result = davi_execute(
        capability="si.goal.create",
        proposal_id=out["proposal_id"],
        confirm=True,
        actor_id="user-a",
        authorization=AUTH_OK,
        orchestrator=orch,
    )
    assert result["verified"] is True


def test_read_tool_rejects_act_fields() -> None:
    """ACT must not be reachable through the read tool: the closed read
    schema forbids proposal_handle/proposal_id/confirm outright."""
    from pydantic import ValidationError

    from app.interface.mcp.schemas import ReadInput

    for extra in (
        {"proposal_handle": "gp_x.sig"},
        {"proposal_id": "gp_x"},
        {"confirm": True},
    ):
        with pytest.raises(ValidationError):
            ReadInput(
                capability="get_si_indicators",
                arguments=None,
                **extra,
            )


def test_execute_schema_rejects_unknown_fields() -> None:
    from pydantic import ValidationError

    from app.interface.mcp.schemas import ExecuteInput

    with pytest.raises(ValidationError):
        ExecuteInput(capability="si.goal.update", url="http://x", method="POST")
    with pytest.raises(ValidationError):
        ExecuteInput(capability="si.goal.update", sql="DELETE FROM goals")


def test_proposal_handle_is_opaque_and_hmac_bound() -> None:
    from app.application.external_capabilities.governed_writes.proposal_store import (
        parse_proposal_handle,
    )

    handle = mint_proposal_handle("gp_abc123")
    # The raw id is not recoverable by inspection — only via HMAC-verified decode.
    assert "gp_abc123" not in handle
    assert parse_proposal_handle(handle) == "gp_abc123"
    # Tampering with the MAC segment fails closed.
    left, right = handle.split(".", 1)
    forged = f"{left}.{'A' if not right.startswith('A') else 'B'}{right[1:]}"
    with pytest.raises(GovernedWriteError):
        parse_proposal_handle(forged)
    # A different id mints a different handle — no cross-proposal reuse.
    assert mint_proposal_handle("gp_other") != handle


# ---------------------------------------------------------------------------
# Independent-review hardening
# ---------------------------------------------------------------------------


def test_concurrent_acts_single_write() -> None:
    """Two threads racing the same proposal: exactly one reaches the owner."""
    import threading

    client = FakeSiClient()
    orch = _orchestrator(client)
    out = _prepare(
        orch,
        "si.goal.create",
        {
            "indicator_id": "i",
            "goal_year": 2027,
            "goal_label": "x",
            "goal_periodicity": "annual",
        },
    )
    results: list = []

    def race():
        try:
            results.append(("ok", _act(orch, "si.goal.create", out)))
        except GovernedWriteError as exc:
            results.append(("err", exc.code))

    t1, t2 = threading.Thread(target=race), threading.Thread(target=race)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    oks = [r for r in results if r[0] == "ok"]
    errs = [r for r in results if r[0] == "err"]
    assert len(oks) + len(errs) == 2
    assert len(oks) == 1
    assert errs and errs[0][1] == PROPOSAL_NOT_FOUND
    assert len(client.writes) == 1


def test_prepare_update_fails_closed_without_occ_token() -> None:
    """Owner row without row_xmin → no unguarded proposal is sealed."""
    row = _goal_row("g-1")
    row.pop("row_xmin")
    client = FakeSiClient(rows=[row])
    orch = _orchestrator(client)
    with pytest.raises(GovernedWriteError) as exc:
        _prepare(
            orch, "si.goal.update", {"goal_id": "g-1", "goal_label": "x"}
        )
    assert exc.value.status_code == 502


def test_prepare_toggle_fails_closed_without_occ_token() -> None:
    row = _goal_row("g-1")
    row.pop("row_xmin")
    client = FakeSiClient(rows=[row])
    orch = _orchestrator(client)
    with pytest.raises(GovernedWriteError) as exc:
        _prepare(orch, "si.goal.activate", {"goal_id": "g-1"})
    assert exc.value.status_code == 502


def test_hmac_secret_missing_fails_closed(monkeypatch) -> None:
    """Dedicated secret is mandatory: legacy fallback env vars must NOT
    rescue the governed-write surface."""
    from app.application.external_capabilities.governed_writes import (
        proposal_store,
    )

    monkeypatch.delenv("DAVI_GOVERNED_WRITE_HMAC_SECRET", raising=False)
    # Fallback secrets present — still must fail closed.
    monkeypatch.setenv("DAVI_CANDIDATE_HMAC_SECRET", "candidate-secret")
    monkeypatch.setenv("JWT_SECRET", "jwt-secret")
    with pytest.raises(GovernedWriteError):
        proposal_store.mint_proposal_handle("gp_x")


def test_proposal_store_bounded_evicts_expired_then_oldest(monkeypatch) -> None:
    """Store is memory-bounded: at MAX_PROPOSALS capacity, expired entries
    are evicted first, then the oldest live proposals."""
    from app.application.external_capabilities.governed_writes import (
        proposal_store,
    )
    from app.application.external_capabilities.governed_writes.proposal import (
        GovernedProposal,
    )

    store = proposal_store.ProposalStore()
    monkeypatch.setattr(proposal_store, "MAX_PROPOSALS", 3)

    def _proposal(pid: str, expires_at: float, created: float) -> GovernedProposal:
        return GovernedProposal(
            proposal_id=pid,
            capability="si.goal.update",
            actor_id="u1",
            actor_email="u1@x",
            resource_type="indicator_goal",
            resource_id="g-1",
            current_state_fingerprint="fp",
            exact_change={"x": 1},
            validation_result={"ready": True},
            consequential_impact={},
            confirmation_requirement={"mode": "explicit"},
            expected_postcondition={},
            created_at=created,
            expires_at=expires_at,
            content_hash="h",
        )

    now = 1000.0
    monkeypatch.setattr(proposal_store.time, "time", lambda: now)
    store.put(_proposal("p-expired", expires_at=now - 1, created=1))
    store.put(_proposal("p-old", expires_at=now + 900, created=2))
    store.put(_proposal("p-mid", expires_at=now + 900, created=3))
    # At capacity → expired evicted first.
    store.put(_proposal("p-new", expires_at=now + 900, created=4))
    assert "p-expired" not in store._items
    assert {"p-old", "p-mid", "p-new"} <= set(store._items)
    # Still at capacity → oldest live entry evicted.
    store.put(_proposal("p-newer", expires_at=now + 900, created=5))
    assert "p-old" not in store._items
    assert len(store._items) <= 3


def test_wire_execute_tool_unauthenticated_returns_typed_error() -> None:
    """MCP wire: execute outside an authenticated context fails closed."""
    import asyncio

    from app.interface.mcp.server import create_mcp_server

    result = asyncio.run(
        create_mcp_server().call_tool(
            "execute",
            {"capability": "si.goal.create", "arguments": {}},
        )
    )
    assert result.is_error is True
    content = getattr(result, "structured_content", None) or {}
    assert content.get("code") == UNAUTHENTICATED


def test_davi_execute_requires_identity() -> None:
    orch = _orchestrator(FakeSiClient())
    with pytest.raises(GovernedWriteError):
        davi_execute(
            capability="si.goal.create",
            arguments={},
            actor_id=None,
            authorization=AUTH_OK,
            orchestrator=orch,
        )
    with pytest.raises(GovernedWriteError):
        davi_execute(
            capability="si.goal.create",
            arguments={},
            actor_id="u",
            authorization="",
            orchestrator=orch,
        )
