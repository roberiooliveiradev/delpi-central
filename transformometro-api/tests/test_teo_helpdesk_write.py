"""R4 Governed Helpdesk Writes — PREPARE/ACT/verify contract tests.

Helpdesk BFF stays the owner of the Helpdesk contract, business
revalidation, GLPI writes and idempotency. These tests use fake ports —
no HTTP, no GLPI.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from starlette.requests import Request

from tm_app.application.governed_writes.confirmation_policy import (
    AUTO_ACT,
    CONFIRM_BEFORE_ACT,
    execution_policy_for_capability,
)
from tm_app.application.governed_writes.errors import (
    OUTCOME_VERIFICATION_FAILED,
    PROPOSAL_STALE,
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import (
    GovernedWriteOrchestrator,
)
from tm_app.application.helpdesk.helpdesk_write_capabilities import (
    HELPDESK_ACTION_TO_CAPABILITY,
)
from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.application.gpt_actions.errors import GptActionsError
from tm_app.application.gpt_actions.governed_actions_facade import (
    GovernedActionsFacade,
)
from tm_app.application.helpdesk.helpdesk_write_port import (
    HelpdeskWriteStack,
)


# --------------------------------------------------------------------------
# Fake ports
# --------------------------------------------------------------------------


def _ticket(**over) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": 500,
        "title": "Painel",
        "status": "open",
        "status_id": 2,
        "updated_at": "2026-10-09T10:00:00",
        "assigned_user_id": 8,
        "can_assign": True,
        "can_followup": True,
        "can_create_task": True,
        "can_create_solution": True,
        "can_request_approval": True,
        "can_accept_solution": False,
        "can_reject_solution": False,
        "can_submit_satisfaction": False,
        "can_decide_validation": False,
        "satisfaction": None,
        "validations": [],
        "timeline": [],
    }
    base.update(over)
    return base


class _FakeHelpdeskPorts:
    """Implements both HelpdeskReadPort.ticket and HelpdeskWritePort."""

    def __init__(self) -> None:
        self.ticket_state = _ticket()
        self.write_calls: list[tuple] = []
        self.last_idempotency_key: str | None = None
        self.created_ticket: dict[str, Any] | None = None

    # read port
    def _state(self, ticket_id: int) -> dict[str, Any]:
        if self.created_ticket is not None and int(ticket_id) == int(
            self.created_ticket["id"]
        ):
            return self.created_ticket
        return self.ticket_state

    def ticket(self, authorization: str, ticket_id: int) -> dict[str, Any]:
        return dict(self._state(ticket_id))

    # write port — records the call, mutates the fake state like the BFF
    def _key(self, kwargs: dict[str, Any]) -> None:
        self.last_idempotency_key = kwargs.get("idempotency_key")

    def create_ticket(self, authorization, body, **kw):
        self.write_calls.append(("create_ticket", dict(body)))
        self._key(kw)
        self.created_ticket = {
            **_ticket(),
            "id": 999,
            "title": body.get("title"),
        }
        return {"id": 999}

    def set_assignee(self, authorization, ticket_id, **kw):
        self.write_calls.append(("set_assignee", ticket_id, kw["user_id"]))
        self._key(kw)
        self._state(ticket_id)["assigned_user_id"] = kw["user_id"]
        return {"user_id": kw["user_id"], "assigned_display_name": "Robério"}

    def add_followup(self, authorization, ticket_id, **kw):
        self.write_calls.append(("add_followup", ticket_id))
        self._key(kw)
        state = self._state(ticket_id)
        state["timeline"] = [
            *state["timeline"],
            {"id": 41, "kind": "followup", "content": kw["content"]},
        ]
        return {"id": 41}

    def create_task(self, authorization, ticket_id, body, **kw):
        self.write_calls.append(("create_task", ticket_id, dict(body)))
        self._key(kw)
        state = self._state(ticket_id)
        state["timeline"] = [
            *state["timeline"],
            {"id": 55, "kind": "task", "content": body.get("content")},
        ]
        return {"id": 55, "state": 1}

    def add_solution(self, authorization, ticket_id, **kw):
        self.write_calls.append(("add_solution", ticket_id))
        self._key(kw)
        state = self._state(ticket_id)
        state["timeline"] = [
            *state["timeline"],
            {"id": 77, "kind": "solution", "content": kw["content"]},
        ]
        state["status_id"] = 5
        return {"id": 77, "status_id": 5}

    def request_validation(self, authorization, ticket_id, body, **kw):
        self.write_calls.append(("request_validation", ticket_id, dict(body)))
        self._key(kw)
        self._state(ticket_id)["validations"] = [
            {"id": 9, "status": 2, "requested_approver_id": body.get("approver_id")}
        ]
        return {"id": 9, "status": 2}

    def decide_solution(self, authorization, ticket_id, **kw):
        self.write_calls.append(("decide_solution", ticket_id, kw["decision"]))
        self._key(kw)
        state = self._state(ticket_id)
        state["status_id"] = 6 if kw["decision"] == "accept" else 2
        return {"id": ticket_id, "status_id": state["status_id"]}

    def submit_satisfaction(self, authorization, ticket_id, **kw):
        self.write_calls.append(("submit_satisfaction", ticket_id, kw["satisfaction"]))
        self._key(kw)
        self._state(ticket_id)["satisfaction"] = kw["satisfaction"]
        return {"satisfaction": kw["satisfaction"], "comment": kw.get("comment")}

    def decide_validation(self, authorization, ticket_id, validation_id, **kw):
        self.write_calls.append(
            ("decide_validation", ticket_id, validation_id, kw["decision"])
        )
        self._key(kw)
        for v in self._state(ticket_id)["validations"]:
            if int(v["id"]) == int(validation_id):
                v["status"] = 3 if kw["decision"] == "accept" else 4
        return {"id": validation_id, "status": 3 if kw["decision"] == "accept" else 4}


def _stack() -> tuple[HelpdeskWriteStack, _FakeHelpdeskPorts]:
    ports = _FakeHelpdeskPorts()
    return HelpdeskWriteStack(read=ports, write=ports), ports


def _auth_user():
    return SimpleNamespace(
        id="u1", email="teo@example.com", name="Téo",
        roles=[], groups=[], permissions=["transformometro.access"],
        is_superadmin=False,
    )


def _request() -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/mcp",
        "raw_path": b"/mcp",
        "query_string": b"",
        "headers": [(b"authorization", b"Bearer test")],
        "client": ("127.0.0.1", 0),
        "server": ("test", 443),
    }
    request = Request(scope)
    request.state.user = _auth_user()
    return request


@pytest.fixture(autouse=True)
def _clean_proposals():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


def _facade() -> tuple[GovernedActionsFacade, _FakeHelpdeskPorts]:
    stack, ports = _stack()
    return (
        GovernedActionsFacade(
            orchestrator=GovernedWriteOrchestrator(helpdesk_stack=stack)
        ),
        ports,
    )


def _prepare(facade, action: str, **kwargs) -> dict[str, Any]:
    capability = HELPDESK_ACTION_TO_CAPABILITY[action]
    return facade.prepare_capability(
        _request(),
        capability=capability,
        args=kwargs,
        operation_label=f"prepare_helpdesk_change:{action}",
    )


def _commit(facade, public: dict[str, Any], *, confirmation: bool) -> dict[str, Any]:
    return facade.commit_proposal(
        _request(),
        proposal_handle=public["proposal"]["handle"]
        if "proposal" in public
        else public["proposal_handle"],
        confirmation=confirmation,
    )


def _handle_of(public: dict[str, Any]) -> str:
    if isinstance(public.get("proposal"), dict):
        return public["proposal"]["handle"]
    return public["proposal_handle"]


# --------------------------------------------------------------------------
# PREPARE
# --------------------------------------------------------------------------


def test_prepare_create_ticket_never_writes():
    facade, ports = _facade()
    out = _prepare(
        facade,
        "create_ticket",
        title="Dashboard não carrega",
        description="Erro ao abrir painel.",
        category_id=3,
        urgency_id=2,
    )
    prop = out["proposal"]
    assert prop["capability"] == "helpdesk_create_ticket"
    assert prop["ready"] is True
    assert out["persisted"] is False
    # PREPARE never performed a write
    assert ports.write_calls == []


def test_prepare_missing_required_fields_not_ready():
    facade, ports = _facade()
    out = _prepare(facade, "create_ticket", title="x")
    prop = out["proposal"]
    assert prop["ready"] is False
    assert prop["act_allowed"] is False
    vr = out["validation_result"]
    assert sorted(vr["missing"]) == ["category_id", "description", "urgency_id"]
    assert ports.write_calls == []


def test_prepare_ticket_scoped_reads_current_state_and_flag():
    facade, ports = _facade()
    ports.ticket_state["can_assign"] = False
    out = _prepare(facade, "set_assignee", ticket_id=500, user_id=11)
    prop = out["proposal"]
    assert prop["ready"] is False
    assert "can_assign" in out["validation_result"]["blocked"]
    assert ports.write_calls == []


def test_prepare_add_followup_ready_with_fingerprint():
    facade, _ports = _facade()
    out = _prepare(facade, "add_followup", ticket_id=500, content="ok")
    prop = out["proposal"]
    assert prop["ready"] is True
    # fingerprint is captured internally (stale protection tested below);
    # the public proposal exposes only exact_change + expected_postcondition
    assert "current_state_fingerprint" not in prop
    assert prop["exact_change"]["content"] == "ok"
    assert prop["expected_postcondition"]["ticket_id"] == 500


def test_prepare_unknown_capability_fails_closed():
    facade, _ = _facade()
    with pytest.raises(GovernedWriteError) as exc:
        facade.prepare_capability(
            _request(),
            capability="helpdesk_teleport_ticket",
            args={},
            operation_label="x",
        )
    assert exc.value.code == VALIDATION


# --------------------------------------------------------------------------
# POLICY — canonical classification
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cap",
    [
        "helpdesk_create_ticket",
        "helpdesk_add_followup",
        "helpdesk_create_task",
    ],
)
def test_policy_auto_act(cap):
    assert execution_policy_for_capability(cap) == AUTO_ACT


@pytest.mark.parametrize(
    "cap",
    [
        "helpdesk_set_assignee",
        "helpdesk_add_solution",
        "helpdesk_request_validation",
        "helpdesk_accept_solution",
        "helpdesk_reject_solution",
        "helpdesk_submit_satisfaction",
        "helpdesk_accept_validation",
        "helpdesk_reject_validation",
    ],
)
def test_policy_confirm_before_act(cap):
    assert execution_policy_for_capability(cap) == CONFIRM_BEFORE_ACT


def test_confirm_before_act_commit_requires_confirmation():
    facade, ports = _facade()
    out = _prepare(facade, "set_assignee", ticket_id=500, user_id=11)
    with pytest.raises(GovernedWriteError) as exc:
        _commit(facade, out, confirmation=False)
    assert exc.value.data.get("error_code") == "CONFIRMATION_REQUIRED"
    assert ports.write_calls == []  # no write before confirmation


def test_auto_act_commit_without_confirmation_executes():
    facade, ports = _facade()
    out = _prepare(facade, "add_followup", ticket_id=500, content="nota")
    data = _commit(facade, out, confirmation=False)
    assert data["persisted"] is True
    assert ports.write_calls == [("add_followup", 500)]


# --------------------------------------------------------------------------
# ACT — idempotency, stale, read-back
# --------------------------------------------------------------------------


def test_idempotency_key_is_proposal_bound():
    facade, ports = _facade()
    out = _prepare(facade, "add_followup", ticket_id=500, content="n1")
    _commit(facade, out, confirmation=False)
    proposal_id = out["proposal"]["proposal_id"]
    assert ports.last_idempotency_key == f"teo-{proposal_id}"


def test_consumed_proposal_cannot_commit_twice():
    facade, ports = _facade()
    out = _prepare(facade, "add_followup", ticket_id=500, content="n1")
    handle = _handle_of(out)
    _commit(facade, out, confirmation=False)
    with pytest.raises(GovernedWriteError) as exc:
        facade.commit_proposal(
            _request(), proposal_handle=handle, confirmation=False
        )
    # consumed proposal rejects any second ACT — canonical code may be
    # proposal_not_found (consumed) or proposal_stale; either way, fail closed
    assert exc.value.code in {PROPOSAL_STALE, "proposal_not_found"}
    # exactly one business effect
    assert ports.write_calls == [("add_followup", 500)]


def test_stale_state_blocks_act():
    facade, ports = _facade()
    out = _prepare(facade, "set_assignee", ticket_id=500, user_id=11)
    # ticket drifts between PREPARE and ACT
    ports.ticket_state["assigned_user_id"] = 22
    ports.ticket_state["updated_at"] = "2026-10-09T11:00:00"
    with pytest.raises(GovernedWriteError) as exc:
        _commit(facade, out, confirmation=True)
    assert exc.value.code == PROPOSAL_STALE
    assert ports.write_calls == []


def test_create_ticket_end_to_end_verified():
    facade, ports = _facade()
    out = _prepare(
        facade,
        "create_ticket",
        title="Chamado teste",
        description="desc",
        category_id=1,
        urgency_id=3,
    )
    data = _commit(facade, out, confirmation=False)
    assert data["persisted"] is True
    assert data["data"]["ticket"]["id"] == 999
    assert ports.write_calls[0][0] == "create_ticket"


def test_set_assignee_read_back_verified():
    facade, _ = _facade()
    out = _prepare(facade, "set_assignee", ticket_id=500, user_id=11)
    data = _commit(facade, out, confirmation=True)
    assert data["data"]["ticket"]["assigned_user_id"] == 11


def test_solution_decision_verified_by_status():
    facade, ports = _facade()
    ports.ticket_state.update(
        status_id=5, can_accept_solution=True
    )
    out = _prepare(facade, "accept_solution", ticket_id=500)
    data = _commit(facade, out, confirmation=True)
    assert data["data"]["ticket"]["status_id"] == 6


def test_validation_decision_verified():
    facade, ports = _facade()
    ports.ticket_state["can_decide_validation"] = True
    ports.ticket_state["validations"] = [
        {"id": 9, "status": 2, "mine_to_decide": True}
    ]
    out = _prepare(
        facade, "accept_validation", ticket_id=500, validation_id=9
    )
    data = _commit(facade, out, confirmation=True)
    assert data["data"]["ticket"]["validations"][0]["status"] == 3


def test_validation_not_mine_to_decide_not_ready():
    facade, ports = _facade()
    ports.ticket_state["can_decide_validation"] = True
    ports.ticket_state["validations"] = [
        {"id": 9, "status": 2, "mine_to_decide": False}
    ]
    out = _prepare(
        facade, "accept_validation", ticket_id=500, validation_id=9
    )
    assert out["proposal"]["ready"] is False
    assert "validation_not_mine_to_decide" in (
        out["validation_result"]["blocked"]
    )


# --------------------------------------------------------------------------
# OUTCOME VERIFICATION — 2xx is not business outcome
# --------------------------------------------------------------------------


def test_followup_readback_mismatch_fails():
    facade, ports = _facade()
    out = _prepare(facade, "add_followup", ticket_id=500, content="x")
    # corrupt the write side: return id that never appears in timeline
    original = ports.add_followup

    def broken(authorization, ticket_id, **kw):
        ports.write_calls.append(("add_followup", ticket_id))
        ports._key(kw)
        return {"id": 4242}

    ports.add_followup = broken  # type: ignore[method-assign]
    try:
        with pytest.raises(GovernedWriteError) as exc:
            _commit(facade, out, confirmation=False)
    finally:
        ports.add_followup = original  # type: ignore[method-assign]
    assert exc.value.code == OUTCOME_VERIFICATION_FAILED


def test_missing_ticket_id_not_ready_and_act_blocked():
    facade, ports = _facade()
    out = _prepare(facade, "add_followup", content="x")
    assert out["proposal"]["ready"] is False
    assert ports.write_calls == []


def test_bff_error_propagates_typed():
    facade, ports = _facade()

    def link_required(authorization, ticket_id):
        raise GptActionsError(
            "Link GLPI necessário.",
            409,
            {"error_kind": "conflict", "error_code": "glpi_link_required",
             "authorize_url": "/apps/helpdesk-api/auth/glpi/start"},
        )

    ports.ticket = link_required  # type: ignore[method-assign]
    with pytest.raises(GovernedWriteError) as exc:
        _prepare(facade, "add_followup", ticket_id=500, content="x")
    assert exc.value.data.get("error_code") == "glpi_link_required"


def test_multi_action_chain_uses_read_back_id():
    """Dependent writes chain only on the authoritative returned id."""
    facade, ports = _facade()
    created = _commit(
        facade,
        _prepare(
            facade,
            "create_ticket",
            title="t",
            description="d",
            category_id=1,
            urgency_id=2,
        ),
        confirmation=False,
    )
    ticket_id = created["data"]["ticket"]["id"]  # 999 — from read-back
    out = _prepare(facade, "add_followup", ticket_id=ticket_id, content="ok")
    data = _commit(facade, out, confirmation=False)
    assert data["data"]["ticket"]["id"] == 999
    assert ports.write_calls[-1] == ("add_followup", 999)
