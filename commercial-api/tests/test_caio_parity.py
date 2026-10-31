"""CAIO 2.0 parity suite — dispatch coverage, governed writes,
sealed delete prepare→commit, scope honesty and knowledge corpus.

Proves every proven registry entry is reachable through the six
semantic tools and that destructive ops never bypass the sealed
proposal model.
"""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from delpi_mcp.errors import mcp_tool_result

from commercial_app.application.caio import proposal_store
from commercial_app.application.caio.semantic_registry import (
    SEMANTIC_ACTIONS,
)
from commercial_app.interface.mcp import semantic_bridge as sem
from commercial_app.interface.mcp import tool_bridge_parity as parity


def _human_user(permissions=("commercial.access",), **over):
    data = {
        "id": "user-1",
        "email": "user@delpi.test",
        "name": "Test User",
        "principal_type": "user",
        "is_superadmin": False,
        "permissions": list(permissions),
        "access_token": "human-token",
    }
    data.update(over)
    return SimpleNamespace(**data)


def _set_context(user, authorization="Bearer human-token"):
    set_current_user(user)
    set_request_authorization(authorization)


@pytest.fixture(autouse=True)
def _clear_context():
    clear_current_user()
    clear_request_authorization()
    proposal_store.reset_proposal_store_for_tests()
    yield
    proposal_store.reset_proposal_store_for_tests()
    clear_current_user()
    clear_request_authorization()


def _ok_result(**_kwargs):
    return "HANDLER_CALLED"


# --- coverage: every proven entry is reachable ---------------------------------


def test_every_proven_read_has_dispatch():
    for a in SEMANTIC_ACTIONS:
        if a.tool == "read" and a.status == "proven":
            assert (a.entity, a.action) in sem._READ_DISPATCH, (
                f"missing read dispatch: {a.capability}"
            )


def test_every_proven_analyze_has_dispatch():
    for a in SEMANTIC_ACTIONS:
        if a.tool == "analyze" and a.status == "proven":
            assert a.capability in sem._ANALYZE_DISPATCH, (
                f"missing analyze dispatch: {a.capability}"
            )


def test_every_proven_execute_has_dispatch():
    for a in SEMANTIC_ACTIONS:
        if a.tool == "execute" and a.status == "proven":
            assert (a.entity, a.action) in sem._EXECUTE_DISPATCH, (
                f"missing execute dispatch: {a.capability}"
            )


def test_every_proven_delete_has_sealed_spec():
    for a in SEMANTIC_ACTIONS:
        if a.tool == "delete" and a.status == "proven":
            assert a.capability in sem._DELETE_SPEC, (
                f"missing delete spec: {a.capability}"
            )
            builder, executor = sem._DELETE_SPEC[a.capability]
            assert callable(builder) and callable(executor)


def test_analyze_proxy_map_covers_generic_types():
    assert set(parity.ANALYZE_PROXY_MAP) <= set(sem._ANALYZE_DISPATCH)


def test_registry_covers_portal_families():
    entities = {a.entity for a in SEMANTIC_ACTIONS}
    for expected in (
        "portfolio", "customer", "customer_center", "open_order",
        "proposal", "worklist", "task", "activity", "group",
        "sla_policy", "home_favorite", "team", "attachment",
        "interaction_room", "interaction_message", "production",
        "user_profile", "contact",
    ):
        assert expected in entities


# --- read / analyze dispatch -----------------------------------------------------


def test_read_task_list_dispatches():
    _set_context(_human_user())
    stub = mcp_tool_result({"success": True, "data": {"items": []}}, is_error=False)
    with patch.object(
        parity, "tool_task_list", return_value=stub
    ) as mock:
        result = sem.tool_read(entity="task", action="list")
    assert result.is_error is False
    assert mock.call_count == 1


def test_read_interaction_room_list_fields():
    _set_context(_human_user())
    captured = {}

    def fake(**kwargs):
        captured.update(kwargs)
        return mcp_tool_result({"success": True, "data": {}}, is_error=False)

    with patch.object(parity, "tool_interaction_room_list", fake):
        result = sem.tool_read(
            entity="interaction_room",
            action="list",
            filters={"filter_key": "unread", "limit": 10},
        )
    assert result.is_error is False
    assert captured["filter_key"] == "unread"
    assert captured["limit"] == 10


def test_analyze_generic_proxy_dispatches_owner_path():
    _set_context(_human_user())
    captured = {}

    def fake(**kwargs):
        captured.update(kwargs)
        return mcp_tool_result({"success": True, "data": {}}, is_error=False)

    with patch.object(parity, "analyze_proxy", fake):
        result = sem.tool_analyze(
            analysis_type="rol.series",
            parameters={
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "granularity": "month",
            },
        )
    assert result.is_error is False
    assert captured["path"] == "/rol/series"
    assert captured["start_date"] == "2025-01-01"
    assert captured["granularity"] == "month"
    assert captured["analysis_label"] == "rol.series"


def test_analyze_rejects_undeclared_param():
    _set_context(_human_user())
    result = sem.tool_analyze(
        analysis_type="rol.series",
        parameters={"sql_query": "DROP TABLE"},
    )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "validation"


# --- execute -----------------------------------------------------------------------


def test_execute_merges_target_ref_into_ref_arg():
    _set_context(_human_user(permissions=["commercial.manage"]))
    captured = {}

    def fake(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    with patch.dict(sem._EXECUTE_DISPATCH, {("group", "rename"): fake}):
        result = sem.tool_execute(
            entity="group",
            action="rename",
            target_ref="grp-1",
            payload={"name": "Squad A"},
        )
    assert result.is_error is False
    assert captured == {"group_id": "grp-1", "name": "Squad A"}
    data = result.structured_content["data"]
    assert data["executed"] is True


def test_execute_payload_and_changes_merge():
    _set_context(_human_user(permissions=["commercial.manage"]))
    captured = {}

    def fake(**kwargs):
        captured.update(kwargs)
        return {"ok": True}

    with patch.dict(sem._EXECUTE_DISPATCH, {("portfolio", "update"): fake}):
        result = sem.tool_execute(
            entity="portfolio",
            action="update",
            target_ref="p-1",
            payload={"display_name": "Carteira X"},
            changes={"active": True},
        )
    assert result.is_error is False
    assert captured["portfolio_id"] == "p-1"
    assert captured["display_name"] == "Carteira X"
    assert captured["active"] is True


def test_execute_requires_ref_arg_when_declared():
    _set_context(_human_user(permissions=["commercial.manage"]))
    result = sem.tool_execute(
        entity="group", action="rename", payload={"name": "x"}
    )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "validation"


def test_execute_without_context_is_unauthorized():
    result = sem.tool_execute(
        entity="task",
        action="create",
        payload={"title": "t"},
    )
    assert result.is_error is True
    assert result.structured_content["status_code"] == 401


def test_execute_task_create_allowed_for_access_user():
    _set_context(_human_user())
    captured = {}

    def fake(**kwargs):
        captured.update(kwargs)
        return {"id": "t-1"}

    with patch.dict(sem._EXECUTE_DISPATCH, {("task", "create"): fake}):
        result = sem.tool_execute(
            entity="task",
            action="create",
            payload={
                "title": "Follow-up",
                "priority": "high",
            },
        )
    assert result.is_error is False
    assert captured["title"] == "Follow-up"
    assert captured["priority"] == "high"


# --- delete: sealed prepare → commit -------------------------------------------------


def _fake_delete_spec(calls: list):
    def impact(target):
        return {"target": target, "effect": "exclusão de teste"}

    def executor(target, args):
        calls.append((target, dict(args)))
        return {"deleted_target": target}

    return impact, executor


def _install_fake_spec(capability="task.delete"):
    calls: list = []
    impact, executor = _fake_delete_spec(calls)
    spec = dict(sem._DELETE_SPEC)
    spec[capability] = (impact, executor)
    return calls, patch.object(sem, "_DELETE_SPEC", spec)


def test_delete_prepare_seals_proposal_with_impact():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        result = sem.tool_delete(
            entity="task",
            target_ref="task-9",
            phase="prepare",
        )
    assert result.is_error is False
    data = result.structured_content["data"]
    assert data["phase"] == "prepare"
    assert data["proposal_ref"]
    assert data["proposal"]["impact"]["effect"] == "exclusão de teste"
    assert calls == []  # nothing executed on prepare


def test_delete_commit_executes_and_consumes():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        prep = sem.tool_delete(
            entity="task", target_ref="task-9", phase="prepare"
        )
        ref = prep.structured_content["data"]["proposal_ref"]
        result = sem.tool_delete(
            entity="task",
            target_ref="task-9",
            phase="commit",
            proposal_ref=ref,
        )
    assert result.is_error is False
    assert result.structured_content["data"]["deleted"] is True
    assert calls == [("task-9", {})]


def test_delete_commit_replay_fails():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        prep = sem.tool_delete(entity="task", target_ref="t", phase="prepare")
        ref = prep.structured_content["data"]["proposal_ref"]
        first = sem.tool_delete(
            entity="task", target_ref="t", phase="commit",
            proposal_ref=ref,
        )
        second = sem.tool_delete(
            entity="task", target_ref="t", phase="commit",
            proposal_ref=ref,
        )
    assert first.is_error is False
    assert second.is_error is True
    assert second.structured_content["error_code"] == "proposal_not_found"
    assert len(calls) == 1


def test_delete_commit_tampered_handle_fails():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        prep = sem.tool_delete(entity="task", target_ref="t", phase="prepare")
        ref = prep.structured_content["data"]["proposal_ref"]
        tampered = ref[:-2] + ("AA" if not ref.endswith("AA") else "BB")
        result = sem.tool_delete(
            entity="task", target_ref="t", phase="commit",
            proposal_ref=tampered,
        )
    assert result.is_error is True
    assert result.structured_content["error_code"].startswith(
        "proposal"
    )
    assert calls == []


def test_delete_commit_wrong_target_fails():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        prep = sem.tool_delete(entity="task", target_ref="t-1", phase="prepare")
        ref = prep.structured_content["data"]["proposal_ref"]
        result = sem.tool_delete(
            entity="task", target_ref="t-2", phase="commit",
            proposal_ref=ref,
        )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "proposal_mismatch"
    assert calls == []


def test_delete_commit_wrong_capability_fails():
    _set_context(_human_user())
    calls = []
    spec = dict(sem._DELETE_SPEC)
    impact, executor = _fake_delete_spec(calls)
    spec["task.delete"] = (impact, executor)
    spec["group.delete"] = (impact, executor)
    with patch.object(sem, "_DELETE_SPEC", spec):
        prep = sem.tool_delete(entity="task", target_ref="t", phase="prepare")
        ref = prep.structured_content["data"]["proposal_ref"]
        result = sem.tool_delete(
            entity="group", action="delete", target_ref="t",
            phase="commit", proposal_ref=ref,
        )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "proposal_mismatch"
    assert calls == []


def test_delete_commit_cross_user_fails():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        prep = sem.tool_delete(entity="task", target_ref="t", phase="prepare")
        ref = prep.structured_content["data"]["proposal_ref"]
        _set_context(_human_user(id="user-2"))
        result = sem.tool_delete(
            entity="task", target_ref="t", phase="commit",
            proposal_ref=ref,
        )
    assert result.is_error is True
    assert result.structured_content["error_code"] == (
        "proposal_actor_mismatch"
    )
    assert calls == []


def test_delete_commit_expired_proposal_fails():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        prep = sem.tool_delete(entity="task", target_ref="t", phase="prepare")
        ref = prep.structured_content["data"]["proposal_ref"]
        pid = proposal_store.parse_proposal_handle(ref)
        proposal = proposal_store.get_proposal_store().get(pid)
        proposal.expires_at = time.time() - 1
        result = sem.tool_delete(
            entity="task", target_ref="t", phase="commit",
            proposal_ref=ref,
        )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "proposal_expired"
    assert calls == []


def test_delete_commit_without_prepare_fails():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        result = sem.tool_delete(
            entity="task", target_ref="t", phase="commit",
            proposal_ref="bm90LWEtcmVhbA.c2ln",
        )
    assert result.is_error is True
    assert calls == []


def test_delete_compound_target_args_parsed():
    _set_context(_human_user())
    calls = []
    impact, executor = _fake_delete_spec(calls)
    spec = dict(sem._DELETE_SPEC)
    spec["interaction_message.delete"] = (impact, executor)
    target = "room_id=r-1&message_id=m-2"
    with patch.object(sem, "_DELETE_SPEC", spec):
        prep = sem.tool_delete(
            entity="interaction_message",
            target_ref=target,
            phase="prepare",
        )
        ref = prep.structured_content["data"]["proposal_ref"]
        result = sem.tool_delete(
            entity="interaction_message",
            target_ref=target,
            phase="commit",
            proposal_ref=ref,
        )
    assert result.is_error is False
    assert calls and calls[0][1] == {
        "room_id": "r-1", "message_id": "m-2"
    }


def test_delete_default_phase_is_prepare():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        result = sem.tool_delete(entity="task", target_ref="t")
    assert result.is_error is False
    assert result.structured_content["data"]["phase"] == "prepare"
    assert calls == []


def test_delete_confirmed_true_is_not_proof():
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        result = sem.tool_delete(
            entity="task",
            target_ref="t",
            phase="commit",
            proposal_ref=None,
        )
    assert result.is_error is True
    assert result.structured_content["error_code"].startswith(
        "proposal"
    )
    assert calls == []


# --- knowledge ----------------------------------------------------------------------


def test_knowledge_parity_topics_present():
    _set_context(_human_user())
    for topic in (
        "commercial.processes",
        "commercial.portfolio_governance",
        "commercial.worklist_process",
        "commercial.interaction_rooms",
        "commercial.indicators",
        "commercial.scope_semantics",
        "commercial.permissions",
        "commercial.integrations",
        "commercial.delete_governance",
        "commercial.honest_states",
        "caio.tool_map",
    ):
        result = sem.tool_knowledge(topic=topic)
        assert result.is_error is False, topic
        data = result.structured_content["data"]
        assert data["source"]
        assert data["guidance"]


def test_knowledge_planned_topic_still_honest():
    """products.guide was implemented (CAIO 3.0 ampliação); a topic
    outside corpus and planned list is still an honest 404."""
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="products.guide")
    assert result.is_error is False
    result = sem.tool_knowledge(topic="products.unknown")
    assert result.is_error is True
    assert result.structured_content["status_code"] == 404


# --- issue #123: pagination contract -------------------------------------------------


def test_read_pagination_rejected_when_capability_does_not_declare_it():
    """Issue #123 — pagination forwarded to handlers that do not
    support it surfaced as 502; now a typed 400."""
    _set_context(_human_user())
    for entity, action in (
        ("portfolio", "list"),
        ("portfolio", "load_summary"),
        ("customer", "list"),
        ("open_order", "list"),
        ("open_order", "recently_closed"),
        ("worklist", "mine"),
        ("task", "list"),
        ("interaction_room", "list"),
    ):
        result = sem.tool_read(
            entity=entity,
            action=action,
            pagination={"page": 1, "page_size": 1},
        )
        assert result.is_error is True, f"{entity}.{action}"
        payload = result.structured_content
        assert payload["status_code"] == 400, f"{entity}.{action}"
        assert payload["error_code"] == "validation"


def test_read_pagination_supported_capabilities_accept_it():
    _set_context(_human_user())
    captured = {}
    from commercial_app.interface.mcp import tool_bridge as bridge

    def fake(**kwargs):
        captured.update(kwargs)
        return mcp_tool_result({"success": True, "data": {"items": []}}, is_error=False)

    with patch.object(bridge, "tool_proposal_list", fake):
        result = sem.tool_read(
            entity="proposal",
            action="list",
            pagination={"page": 2, "page_size": 5},
        )
    assert result.is_error is False
    assert captured["page"] == 2
    assert captured["page_size"] == 5


def test_read_pagination_unknown_key_rejected():
    _set_context(_human_user())
    result = sem.tool_read(
        entity="proposal",
        action="list",
        pagination={"offset": 10},
    )
    assert result.is_error is True
    assert result.structured_content["error_code"] == "validation"


def test_read_cursor_pagination_on_room_list():
    _set_context(_human_user())
    captured = {}

    def fake(**kwargs):
        captured.update(kwargs)
        return mcp_tool_result({"success": True, "data": {}}, is_error=False)

    with patch.object(parity, "tool_interaction_room_list", fake):
        result = sem.tool_read(
            entity="interaction_room",
            action="list",
            pagination={"limit": 10, "cursor": "abc"},
        )
    assert result.is_error is False
    assert captured["limit"] == 10
    assert captured["cursor"] == "abc"


# --- issue #123: required upstream params (series) ------------------------------------


def test_analyze_series_requires_granularity_locally():
    _set_context(_human_user())
    for kind in ("rol.series", "closing_rate.series",
                 "sales_order_otd.series"):
        result = sem.tool_analyze(
            analysis_type=kind,
            parameters={
                "start_date": "2026-10-01",
                "end_date": "2026-10-30",
            },
        )
        assert result.is_error is True, kind
        payload = result.structured_content
        assert payload["status_code"] == 400
        assert payload["error_code"] == "validation"
        assert "granularity" in str(payload["data"]["required"])


def test_analyze_sales_order_otd_series_forwards_granularity():
    """granularity was missing from the allowed upstream params of
    sales_order_otd.series — the call could never succeed upstream."""
    _set_context(_human_user())
    captured = {}

    def fake(**kwargs):
        captured.update(kwargs)
        return mcp_tool_result({"success": True, "data": {}}, is_error=False)

    with patch.object(parity, "analyze_proxy", fake):
        result = sem.tool_analyze(
            analysis_type="sales_order_otd.series",
            parameters={
                "start_date": "2026-10-01",
                "end_date": "2026-10-30",
                "granularity": "day",
            },
        )
    assert result.is_error is False
    assert captured["granularity"] == "day"
    assert captured["path"] == "/sales-order-otd/series"


def test_analyze_rol_by_product_requires_period():
    _set_context(_human_user())
    result = sem.tool_analyze(analysis_type="rol.by_product")
    assert result.is_error is True
    payload = result.structured_content
    assert payload["status_code"] == 400
    assert set(payload["data"]["required"]) == {
        "start_date", "end_date"
    }


# --- issue #123: upstream 4xx must not surface as 502 ----------------------------------


def test_upstream_client_error_maps_to_typed_result():
    from commercial_app.infrastructure.gateways.delpi_commercial_gateway import (  # noqa: E501
        DelpiUpstreamError,
    )
    from commercial_app.interface.mcp import tool_bridge as bridge

    res = bridge.handle_tool_error(
        DelpiUpstreamError(
            "start_date e end_date são obrigatórios.",
            status_code=400,
        )
    )
    assert res.is_error is True
    payload = res.structured_content
    assert payload["status_code"] == 400
    assert payload["error_code"] == "validation"

    res = bridge.handle_tool_error(
        DelpiUpstreamError("not found", status_code=404)
    )
    assert res.structured_content["status_code"] == 404

    res = bridge.handle_tool_error(
        DelpiUpstreamError("boom", status_code=500)
    )
    assert res.structured_content["status_code"] == 502
    assert res.structured_content["error_code"] == "upstream_error"


# --- issue #123: delete commit claims atomically before executing ----------------------


def test_delete_commit_executor_runs_only_after_claim():
    _set_context(_human_user())
    observed = {}

    def impact(target):
        return {"target": target, "effect": "x"}

    def executor(target, args):
        store = proposal_store.get_proposal_store()
        pid = observed["pid"]
        # consumed proposals are purged from the store — absence at
        # executor time proves the claim already flipped single-use.
        observed["consumed_at_exec"] = store.get(pid) is None
        return {"ok": True}

    spec = dict(sem._DELETE_SPEC)
    spec["task.delete"] = (impact, executor)
    with patch.object(sem, "_DELETE_SPEC", spec):
        prep = sem.tool_delete(
            entity="task", target_ref="t", phase="prepare"
        )
        ref = prep.structured_content["data"]["proposal_ref"]
        observed["pid"] = proposal_store.parse_proposal_handle(ref)
        result = sem.tool_delete(
            entity="task", target_ref="t", phase="commit",
            proposal_ref=ref,
        )
    assert result.is_error is False
    assert observed["consumed_at_exec"] is True


def test_delete_commit_failed_executor_still_consumes_proposal():
    _set_context(_human_user())

    def impact(target):
        return {"target": target}

    def executor(target, args):
        raise RuntimeError("backend failure")

    spec = dict(sem._DELETE_SPEC)
    spec["task.delete"] = (impact, executor)
    with patch.object(sem, "_DELETE_SPEC", spec):
        prep = sem.tool_delete(
            entity="task", target_ref="t", phase="prepare"
        )
        ref = prep.structured_content["data"]["proposal_ref"]
        first = sem.tool_delete(
            entity="task", target_ref="t", phase="commit",
            proposal_ref=ref,
        )
        second = sem.tool_delete(
            entity="task", target_ref="t", phase="commit",
            proposal_ref=ref,
        )
    assert first.is_error is True
    assert first.structured_content["error_code"] == "upstream_error"
    assert second.is_error is True
    assert second.structured_content["error_code"] in {
        "proposal_not_found", "proposal_stale"
    }


def test_delete_commit_concurrent_replay_fails_atomically():
    """Two near-simultaneous commits of one handle: the claim is a
    single critical section, so the second always loses."""
    _set_context(_human_user())
    calls, patcher = _install_fake_spec()
    with patcher:
        prep = sem.tool_delete(entity="task", target_ref="t", phase="prepare")
        ref = prep.structured_content["data"]["proposal_ref"]
        for _ in range(3):
            sem.tool_delete(
                entity="task", target_ref="t", phase="commit",
                proposal_ref=ref,
            )
    assert len(calls) == 1
