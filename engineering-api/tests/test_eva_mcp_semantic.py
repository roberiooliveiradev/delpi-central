"""EVA semantic MCP surface — six tools, registry, governance (R1).

Mirrors the same AuthN/AuthZ/degradation semantics of the legacy
bridge tests: human principal + engineering.access required,
ENG_EVA_ACT_ENABLED fail-closed, sealed proposals for destructive
operations (prepare→commit), never confirmed=true as proof.
"""

from __future__ import annotations

import asyncio
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

from engineering_app.application.eva import proposal_store
from engineering_app.application.eva.semantic_registry import (
    SEMANTIC_ACTIONS,
    SEMANTIC_CATALOG_VERSION,
    SEMANTIC_TOOL_NAMES,
    entities_summary,
    semantic_action,
)
from engineering_app.interface.mcp import semantic_bridge as sem
from engineering_app.interface.mcp import tool_bridge as bridge
from engineering_app.interface.mcp.server import create_mcp_server
from engineering_app.interface.mcp.constants import (
    DESTRUCTIVE_ACT_TOOLS,
    SEMANTIC_TOOL_CLASS,
    TOOL_CLASS,
)


def _human_user(permissions=("engineering.access",), **over):
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
    yield
    clear_current_user()
    clear_request_authorization()


@pytest.fixture(autouse=True)
def _clear_proposals():
    proposal_store.reset_proposal_store_for_tests()
    yield
    proposal_store.reset_proposal_store_for_tests()


def _fake_use_case(result=None, error=None):
    captured = {}

    class _Fake:
        async def execute(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            if error is not None:
                raise error
            return result if result is not None else {"items": []}

    _Fake.captured = captured
    return _Fake()


def _enable_act(monkeypatch) -> None:
    """Full ACT — master + every risk tier enabled."""
    monkeypatch.setenv(bridge.EVA_ACT_ENV_FLAG, "true")
    monkeypatch.setenv(bridge.EVA_ACT_DELETE_ENV_FLAG, "true")
    monkeypatch.setenv(bridge.EVA_ACT_IMPORT_ENV_FLAG, "true")


def _enable_write_act(monkeypatch) -> None:
    """Write tier only — destructive classes stay fail-closed."""
    monkeypatch.setenv(bridge.EVA_ACT_ENV_FLAG, "true")
    monkeypatch.delenv(bridge.EVA_ACT_DELETE_ENV_FLAG, raising=False)
    monkeypatch.delenv(bridge.EVA_ACT_IMPORT_ENV_FLAG, raising=False)


class _FakeElicitCtx:
    """MCP Context fake — records elicit calls and returns a canned
    ElicitationResult-shaped object."""

    def __init__(self, *, action="accept", echo="", confirm=True):
        self._action = action
        self._echo = echo
        self._confirm = confirm
        self.calls = 0

    async def elicit(self, *, message, schema):
        self.calls += 1
        content = schema(confirm=self._confirm, target_echo=self._echo)
        return SimpleNamespace(action=self._action, content=content)


class _NoElicitCtx:
    """Context without elicitation support (attr present but broken)."""

    async def elicit(self, *, message, schema):
        raise RuntimeError("elicit unsupported")


# --- registry / surface -----------------------------------------------------


def test_semantic_surface_is_exactly_six() -> None:
    assert SEMANTIC_TOOL_NAMES == (
        "get_context",
        "read",
        "analyze",
        "knowledge",
        "execute",
        "delete",
    )
    assert set(SEMANTIC_TOOL_CLASS) == set(SEMANTIC_TOOL_NAMES)
    for name in SEMANTIC_TOOL_NAMES:
        assert name in TOOL_CLASS
        assert TOOL_CLASS[name] == SEMANTIC_TOOL_CLASS[name]


def _wire_tools() -> list[dict]:
    server = create_mcp_server()
    tools = asyncio.run(server.list_tools())
    return [
        t.model_dump(mode="json", by_alias=True, exclude_none=True)
        for t in tools
    ]


def test_semantic_annotations() -> None:
    by_name = {t["name"]: t for t in _wire_tools()}
    for name in ("get_context", "read", "analyze", "knowledge"):
        assert by_name[name]["annotations"]["readOnlyHint"] is True
        assert by_name[name]["annotations"]["destructiveHint"] is False
    for name in ("execute", "delete"):
        assert by_name[name]["annotations"]["readOnlyHint"] is False
    assert by_name["delete"]["annotations"]["destructiveHint"] is True
    assert "delete" in DESTRUCTIVE_ACT_TOOLS
    # Security schemes must ride every semantic tool (OAuth transport).
    for name in SEMANTIC_TOOL_NAMES:
        assert by_name[name]["securitySchemes"]
    # Legacy tools carry deprecation metadata - still functional.
    assert by_name["search_nonconformities"]["_meta"]["delpi/deprecated"] is True
    assert not by_name["read"].get("_meta", {}).get("delpi/deprecated")


def test_registry_parity_covers_legacy_intents() -> None:
    capabilities = {a.capability for a in SEMANTIC_ACTIONS}
    for cap in (
        "engineering.home", "engineering.overview",
        "lmp.list", "lmp.summary", "lmp.detail",
        "lmp.history_events", "lmp.history_flow",
        "lmp.goal_context", "lmp.department_idd", "lmp.nc_streak",
        "product.structure",
        "nonconformity.search", "nonconformity.detail",
        "nonconformity.history", "nonconformity.indicators",
        "nonconformity.tags", "nonconformity.context",
        "nonconformity.export",
        "nonconformity.create", "nonconformity.update",
        "nonconformity.import", "nonconformity.delete",
    ):
        assert cap in capabilities, cap
    assert entities_summary()


# --- get_context ------------------------------------------------------------


def test_get_context_catalog(monkeypatch) -> None:
    monkeypatch.delenv(bridge.EVA_ACT_ENV_FLAG, raising=False)
    monkeypatch.delenv(bridge.EVA_ACT_DELETE_ENV_FLAG, raising=False)
    monkeypatch.delenv(bridge.EVA_ACT_IMPORT_ENV_FLAG, raising=False)
    _set_context(_human_user())
    result = sem.tool_get_context()
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["catalog_version"] == SEMANTIC_CATALOG_VERSION
    assert {t["name"] for t in data["semantic_tools"]} == set(
        SEMANTIC_TOOL_NAMES
    )
    assert data["act_enabled"] is False
    assert data["act_tiers"] == {
        "write": False,
        "delete": False,
        "import": False,
    }
    assert data["act_flags"]["delete"] == bridge.EVA_ACT_DELETE_ENV_FLAG
    assert data["act_flags"]["import"] == bridge.EVA_ACT_IMPORT_ENV_FLAG
    assert data["confirmation_model"]["delete"]
    assert data["legacy_surface"]["status"] == "deprecated"
    assert data["agent_directives"]


def test_get_context_entity_filter() -> None:
    _set_context(_human_user())
    result = sem.tool_get_context(entity="nonconformity")
    assert not result.is_error
    actions = result.structured_content["data"]["actions"]
    assert all(a["entity"] == "nonconformity" for a in actions)
    assert {a["action"] for a in actions} >= {
        "search", "create", "update", "delete", "import"
    }


def test_get_context_unknown_entity() -> None:
    _set_context(_human_user())
    result = sem.tool_get_context(entity="drawing")
    assert result.is_error


def test_get_context_forbidden_service_principal() -> None:
    _set_context(_human_user(principal_type="service"), "Bearer svc")
    result = sem.tool_get_context()
    assert result.is_error


# --- read -------------------------------------------------------------------


def test_read_unknown_action_is_typed_error() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_read(entity="nonconformity", action="fly")
    )
    assert result.is_error
    payload = result.structured_content
    assert payload["error_code"] == "not_implemented"
    assert "search" in payload["data"]["allowed_actions"]


def test_read_wrong_tool_is_typed_error() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_read(entity="nonconformity", action="create")
    )
    assert result.is_error
    assert result.structured_content["data"]["expected_tool"] == "execute"


def test_read_nc_search_delegates(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"items": [], "total": 0})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_list_nonconformities_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        sem.tool_read(
            entity="nonconformity",
            action="search",
            filters={"status": "open"},
            pagination={"page": 2, "page_size": 25},
        )
    )
    assert not result.is_error
    kw = fake.captured["kwargs"]
    assert kw["status"] == "open"
    assert kw["page"] == 2 and kw["page_size"] == 25
    assert result.structured_content["entity"] == "nonconformity"


def test_read_rejects_pagination_on_non_paginated_action() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_read(
            entity="lmp",
            action="summary",
            pagination={"page_size": 10},
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "validation"
    assert result.structured_content["status_code"] == 400


def test_read_nc_detail_ref_mapping(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"id": "r1"})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        sem.tool_read(
            entity="nonconformity", action="detail", ref="r1"
        )
    )
    assert not result.is_error
    assert fake.captured["args"][0] == "r1"


def test_read_nc_detail_requires_ref() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_read(entity="nonconformity", action="detail")
    )
    assert result.is_error


def test_read_unknown_filter_rejected() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_read(
            entity="nonconformity",
            action="search",
            filters={"sql": "DROP TABLE"},
        )
    )
    assert result.is_error
    assert "allowed_fields" in result.structured_content["data"]


def test_read_lmp_history_flow_view(monkeypatch) -> None:
    _set_context(_human_user())
    captured = {}

    class _Fake:
        async def execute(self, ctx, query):
            captured["ctx"] = ctx
            return {"status": "available", "events": []}

    monkeypatch.setattr(
        bridge, "build_get_lmp_history_use_case",
        lambda view: _Fake() if view == "flow" else None,
    )
    result = asyncio.run(
        sem.tool_read(
            entity="lmp", action="history_flow", ref="003306"
        )
    )
    assert not result.is_error
    assert captured["ctx"].access_token == "human-token"


def test_read_service_principal_denied() -> None:
    _set_context(_human_user(principal_type="service"), "Bearer svc")
    result = asyncio.run(
        sem.tool_read(entity="nonconformity", action="search")
    )
    assert result.is_error


def test_read_no_permission_denied() -> None:
    _set_context(_human_user(permissions=()))
    result = asyncio.run(
        sem.tool_read(entity="nonconformity", action="search")
    )
    assert result.is_error


def test_read_unauthenticated() -> None:
    result = asyncio.run(
        sem.tool_read(entity="nonconformity", action="search")
    )
    assert result.is_error


# --- analyze ----------------------------------------------------------------


def test_analyze_nc_recurrence_groups(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case(
        {
            "items": [
                {"problem_tag": "solda", "status": "open"},
                {"problem_tag": "solda", "status": "done"},
                {"problem_tag": "dimensao", "status": "open"},
            ],
            "total": 3,
        }
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_list_nonconformities_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        sem.tool_analyze(analysis_type="nonconformity.recurrence")
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["data_class"] == "CALCULATED"
    groups = {g["value"]: g["count"] for g in data["groups"]}
    assert groups == {"solda": 2, "dimensao": 1}
    assert data["coverage"]["complete"] is True


def test_analyze_nc_recurrence_invalid_group_by() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="nonconformity.recurrence",
            parameters={"group_by": "password"},
        )
    )
    assert result.is_error


def test_analyze_lmp_performance_composes(monkeypatch) -> None:
    _set_context(_human_user())
    fake = _fake_use_case({"status": "available", "lmp_on_time": 0.9})
    monkeypatch.setattr(
        sem, "build_get_lmp_summary_use_case", lambda: fake
    )

    class _Aux:
        async def fetch_goal_context(
            self, ctx, *, start_date, end_date, branch
        ):
            return {"status": "available", "goal": 0.85}

        async def fetch_nc_streak(self, ctx):
            return {"status": "available", "days": 41}

    monkeypatch.setattr(
        sem, "build_delegated_auxiliary_source", lambda: _Aux()
    )
    result = asyncio.run(
        sem.tool_analyze(analysis_type="lmp.performance")
    )
    assert not result.is_error
    facts = result.structured_content["data"]["facts"]
    assert {f["source"] for f in facts} == {
        "lmp_summary", "goal_context", "nc_streak"
    }
    assert all(f["data_class"] in {"OBSERVED", "UNKNOWN"} for f in facts)


def test_analyze_unknown_type() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_analyze(analysis_type="drawing.compare")
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 501
    assert result.structured_content["error_code"] == "not_implemented"


def test_analyze_lmp_performance_invalid_period() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="lmp.performance",
            parameters={"start_date": "2026-10-30", "end_date": "2026-10-01"},
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 400
    assert result.structured_content["error_code"] == "validation"


# --- knowledge ---------------------------------------------------------------


def test_knowledge_nonconformity_guide() -> None:
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="nonconformity.guide")
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["knowledge_version"]
    assert data["sources"]
    assert data["guidance"]


def test_knowledge_unknown_topic() -> None:
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="quantum.welding")
    assert result.is_error
    assert result.structured_content["error_code"] == "not_found"


def test_knowledge_planned_topic_not_implemented() -> None:
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="drawing.standards")
    assert result.is_error
    assert result.structured_content["status_code"] == 501


# --- execute ------------------------------------------------------------------


def test_execute_act_disabled_without_flag(monkeypatch) -> None:
    monkeypatch.delenv(bridge.EVA_ACT_ENV_FLAG, raising=False)
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="create",
            payload={"status": "open"},
        )
    )
    assert result.is_error
    assert result.structured_content["data"]["error_code"] == "act_disabled"


def test_execute_create_direct(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    fake = _fake_use_case({"id": "nc-1", "status": "open"})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_create_nonconformity_use_case",
        lambda: fake,
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case({"id": "nc-1"}),
    )
    result = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="create",
            payload={"status": "open", "defect_description": "x"},
            idempotency_key="k-1",
        )
    )
    assert not result.is_error
    assert fake.captured["kwargs"]["idempotency_key"] == "k-1"
    data = result.structured_content["data"]
    assert data["postcondition"]["verified"] is True


def test_execute_create_prepare_side_effect_free(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    fake = _fake_use_case(
        {"valid": True, "side_effects": "none", "projected_changes": {}}
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_prepare_nonconformity_mutation_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="create",
            phase="prepare",
            payload={"status": "open"},
        )
    )
    assert not result.is_error
    assert fake.captured["kwargs"]["operation"] == "create"


def test_execute_update_merges_and_locks(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case(
            {"id": "r1", "status": "open", "updated_at": "t1"}
        ),
    )
    fake_update = _fake_use_case({"id": "r1", "status": "done"})
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_update_nonconformity_use_case",
        lambda: fake_update,
    )
    result = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="update",
            target_ref="r1",
            changes={"status": "done"},
            expected_version="t1",
        )
    )
    assert not result.is_error
    kw = fake_update.captured["kwargs"]
    assert kw["expected_updated_at"] == "t1"
    assert kw["payload"]["status"] == "done"


def test_execute_update_requires_target() -> None:
    _enable_context = None
    result_holder = {}

    async def _run():
        return await sem.tool_execute(
            entity="nonconformity", action="update", changes={}
        )

    with patch.dict("os.environ", {bridge.EVA_ACT_ENV_FLAG: "true"}):
        _set_context(_human_user())
        result_holder["r"] = asyncio.run(_run())
    assert result_holder["r"].is_error


def test_execute_import_prepare_seals_proposal(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    fake = _fake_use_case(
        SimpleNamespace(
            to_dict=lambda: {
                "would_replace_all": True,
                "dry_run": True,
                "created": 1, "deleted": 0, "skipped": 0, "errors": [],
            }
        )
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_import_nonconformities_use_case",
        lambda: fake,
    )
    result = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="import",
            phase="prepare",
            payload={"items": [{"status": "open"}]},
        )
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["proposal_ref"]
    assert data["proposal"]["impact"]["items_count"] == 1
    assert fake.captured["kwargs"]["dry_run"] is True


def test_execute_import_act_phase_rejected() -> None:
    with patch.dict("os.environ", {bridge.EVA_ACT_ENV_FLAG: "true"}):
        _set_context(_human_user())
        result = asyncio.run(
            sem.tool_execute(
                entity="nonconformity",
                action="import",
                phase="act",
                payload={"items": [{"status": "open"}]},
            )
        )
    assert result.is_error


def test_execute_import_commit_requires_proposal() -> None:
    with patch.dict("os.environ", {bridge.EVA_ACT_ENV_FLAG: "true"}):
        _set_context(_human_user())
        result = asyncio.run(
            sem.tool_execute(
                entity="nonconformity",
                action="import",
                phase="commit",
            )
        )
    assert result.is_error
    assert result.structured_content["error_code"] == "proposal_required"


def test_execute_import_commit_with_sealed_proposal(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    import_fake = _fake_use_case(
        SimpleNamespace(
            to_dict=lambda: {
                "created": 1, "deleted": 2, "skipped": 0, "errors": [],
            }
        )
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_import_nonconformities_use_case",
        lambda: import_fake,
    )
    items = [{"status": "open", "defect_description": "x"}]
    prep = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="import",
            phase="prepare",
            payload={"items": items},
        )
    )
    handle = prep.structured_content["data"]["proposal_ref"]
    result = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="import",
            phase="commit",
            proposal_ref=handle,
            ctx=_FakeElicitCtx(echo="import_replace_all"),
        )
    )
    assert not result.is_error
    kw = import_fake.captured["kwargs"]
    assert kw["dry_run"] is False
    assert kw["confirm_replace"] is True
    assert kw["items"] == items


def test_execute_import_commit_tampered_items(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_import_nonconformities_use_case",
        lambda: _fake_use_case(
            SimpleNamespace(to_dict=lambda: {"created": 1})
        ),
    )
    prep = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="import",
            phase="prepare",
            payload={"items": [{"status": "open"}]},
        )
    )
    handle = prep.structured_content["data"]["proposal_ref"]
    result = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="import",
            phase="commit",
            proposal_ref=handle,
            payload={"items": [{"status": "done", "evil": True}]},
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "proposal_mismatch"


def test_execute_wrong_tool_for_delete() -> None:
    with patch.dict("os.environ", {bridge.EVA_ACT_ENV_FLAG: "true"}):
        _set_context(_human_user())
        result = asyncio.run(
            sem.tool_execute(
                entity="nonconformity",
                action="delete",
                target_ref="r1",
            )
        )
    assert result.is_error
    assert result.structured_content["data"]["expected_tool"] == "delete"


# --- delete -----------------------------------------------------------------


def test_delete_prepare_seals_impact(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case(
            {"id": "r1", "sale_number": "003306", "status": "open"}
        ),
    )
    result = asyncio.run(
        sem.tool_delete(entity="nonconformity", target_ref="r1")
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["phase"] == "prepare"
    assert data["proposal_ref"]
    impact = data["proposal"]["impact"]
    assert impact["operation"] == "hard_delete"
    assert impact["irreversible"] is True
    assert impact["record_summary"]["sale_number"] == "003306"


def test_delete_commit_executes_with_proposal(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    calls = {"get": 0, "delete": 0}

    class _Get:
        async def execute(self, record_id):
            calls["get"] += 1
            if calls["get"] > 2:
                from engineering_app.domain.nonconformity.errors import (
                    NcNotFoundError,
                )

                raise NcNotFoundError(record_id)
            return {"id": record_id, "status": "open"}

    class _Delete:
        async def execute(self, record_id):
            calls["delete"] += 1
            return {"deleted": True}

    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _Get(),
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_delete_nonconformity_use_case",
        lambda: _Delete(),
    )
    prep = asyncio.run(
        sem.tool_delete(
            entity="nonconformity", target_ref="r1", phase="prepare"
        )
    )
    handle = prep.structured_content["data"]["proposal_ref"]
    result = asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r1",
            phase="commit",
            proposal_ref=handle,
            ctx=_FakeElicitCtx(echo="r1"),
        )
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["postcondition"]["check"] == "read_back_gone"
    assert calls["delete"] == 1


def test_delete_commit_replay_rejected(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case({"id": "r1"}),
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_delete_nonconformity_use_case",
        lambda: _fake_use_case({"deleted": True}),
    )
    prep = asyncio.run(sem.tool_delete(entity="nonconformity", target_ref="r1"))
    handle = prep.structured_content["data"]["proposal_ref"]
    asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r1",
            phase="commit",
            proposal_ref=handle,
            ctx=_FakeElicitCtx(echo="r1"),
        )
    )
    replay = asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r1",
            phase="commit",
            proposal_ref=handle,
        )
    )
    assert replay.is_error
    assert replay.structured_content["error_code"] in {
        "proposal_not_found",
        "proposal_stale",
    }


def test_delete_commit_wrong_actor_rejected(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case({"id": "r1"}),
    )
    prep = asyncio.run(sem.tool_delete(entity="nonconformity", target_ref="r1"))
    handle = prep.structured_content["data"]["proposal_ref"]
    _set_context(_human_user(id="user-2", email="other@delpi.test"))
    result = asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r1",
            phase="commit",
            proposal_ref=handle,
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "proposal_actor_mismatch"
    assert result.structured_content["status_code"] == 403


def test_delete_commit_wrong_target_rejected(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case({"id": "r1"}),
    )
    prep = asyncio.run(sem.tool_delete(entity="nonconformity", target_ref="r1"))
    handle = prep.structured_content["data"]["proposal_ref"]
    result = asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r2",
            phase="commit",
            proposal_ref=handle,
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "proposal_mismatch"


def test_delete_commit_tampered_handle_rejected() -> None:
    with patch.dict(
        "os.environ",
        {
            bridge.EVA_ACT_ENV_FLAG: "true",
            bridge.EVA_ACT_DELETE_ENV_FLAG: "true",
        },
    ):
        _set_context(_human_user())
        result = asyncio.run(
            sem.tool_delete(
                entity="nonconformity",
                target_ref="r1",
                phase="commit",
                proposal_ref="AAAA.forged",
            )
        )
    assert result.is_error
    assert result.structured_content["error_code"] == "proposal_not_found"


def test_delete_commit_expired_proposal(monkeypatch) -> None:
    _enable_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case({"id": "r1"}),
    )
    prep = asyncio.run(sem.tool_delete(entity="nonconformity", target_ref="r1"))
    handle = prep.structured_content["data"]["proposal_ref"]
    proposal_id = proposal_store.parse_proposal_handle(handle)
    proposal = proposal_store.get_proposal_store().get(proposal_id)
    proposal.expires_at = time.time() - 1
    result = asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r1",
            phase="commit",
            proposal_ref=handle,
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "proposal_expired"


def test_delete_act_disabled_without_flag(monkeypatch) -> None:
    monkeypatch.delenv(bridge.EVA_ACT_ENV_FLAG, raising=False)
    monkeypatch.delenv(bridge.EVA_ACT_DELETE_ENV_FLAG, raising=False)
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_delete(entity="nonconformity", target_ref="r1")
    )
    assert result.is_error
    assert result.structured_content["data"]["error_code"] == "act_disabled"


def test_delete_service_principal_denied() -> None:
    with patch.dict("os.environ", {bridge.EVA_ACT_ENV_FLAG: "true"}):
        _set_context(_human_user(principal_type="service"), "Bearer svc")
        result = asyncio.run(
            sem.tool_delete(entity="nonconformity", target_ref="r1")
        )
    assert result.is_error


# --- risk-tiered ACT flags + verifiable confirmation -----------------------


def test_delete_requires_delete_tier_flag(monkeypatch) -> None:
    """Master flag alone never unlocks destructive classes."""
    _enable_write_act(monkeypatch)
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_delete(entity="nonconformity", target_ref="r1")
    )
    assert result.is_error
    assert (
        result.structured_content["data"]["error_code"] == "act_disabled"
    )
    assert bridge.EVA_ACT_DELETE_ENV_FLAG in (
        result.structured_content["message"]
    )


def test_import_commit_requires_import_tier_flag(monkeypatch) -> None:
    """Write tier allows dry-run prepare but never replace-all commit."""
    _enable_write_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_import_nonconformities_use_case",
        lambda: _fake_use_case(
            SimpleNamespace(to_dict=lambda: {"created": 1})
        ),
    )
    prep = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="import",
            phase="prepare",
            payload={"items": [{"status": "open"}]},
        )
    )
    assert not prep.is_error
    handle = prep.structured_content["data"]["proposal_ref"]
    result = asyncio.run(
        sem.tool_execute(
            entity="nonconformity",
            action="import",
            phase="commit",
            proposal_ref=handle,
            ctx=_FakeElicitCtx(echo="import_replace_all"),
        )
    )
    assert result.is_error
    assert result.structured_content["data"]["error_code"] == "act_disabled"


def test_delete_commit_elicit_unavailable_no_ctx(monkeypatch) -> None:
    """No verifiable channel → honest block; proposal is NOT consumed."""
    _enable_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case({"id": "r1"}),
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_delete_nonconformity_use_case",
        lambda: _fake_use_case({"deleted": True}),
    )
    prep = asyncio.run(
        sem.tool_delete(entity="nonconformity", target_ref="r1")
    )
    handle = prep.structured_content["data"]["proposal_ref"]
    result = asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r1",
            phase="commit",
            proposal_ref=handle,
        )
    )
    assert result.is_error
    assert (
        result.structured_content["error_code"]
        == "confirmation_unavailable"
    )
    retry = asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r1",
            phase="commit",
            proposal_ref=handle,
            ctx=_FakeElicitCtx(echo="r1"),
        )
    )
    assert not retry.is_error


def test_delete_commit_elicit_broken_channel(monkeypatch) -> None:
    """Elicitation raising → same honest unavailability block."""
    _enable_act(monkeypatch)
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case({"id": "r1"}),
    )
    prep = asyncio.run(
        sem.tool_delete(entity="nonconformity", target_ref="r1")
    )
    handle = prep.structured_content["data"]["proposal_ref"]
    result = asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r1",
            phase="commit",
            proposal_ref=handle,
            ctx=_NoElicitCtx(),
        )
    )
    assert result.is_error
    assert (
        result.structured_content["error_code"]
        == "confirmation_unavailable"
    )


@pytest.mark.parametrize(
    "action,echo,confirm",
    [
        ("decline", "r1", True),
        ("cancel", "r1", True),
        ("accept", "r-WRONG", True),
        ("accept", "r1", False),
    ],
)
def test_delete_commit_elicit_not_confirmed(
    monkeypatch, action, echo, confirm
) -> None:
    """Decline/cancel/wrong echo/unchecked → declined, nothing deleted."""
    _enable_act(monkeypatch)
    _set_context(_human_user())
    delete_calls = {"n": 0}

    class _Delete:
        async def execute(self, record_id):
            delete_calls["n"] += 1
            return {"deleted": True}

    monkeypatch.setattr(
        bridge.nc_composer,
        "build_get_nonconformity_use_case",
        lambda: _fake_use_case({"id": "r1"}),
    )
    monkeypatch.setattr(
        bridge.nc_composer,
        "build_delete_nonconformity_use_case",
        lambda: _Delete(),
    )
    prep = asyncio.run(
        sem.tool_delete(entity="nonconformity", target_ref="r1")
    )
    handle = prep.structured_content["data"]["proposal_ref"]
    ctx = _FakeElicitCtx(action=action, echo=echo, confirm=confirm)
    result = asyncio.run(
        sem.tool_delete(
            entity="nonconformity",
            target_ref="r1",
            phase="commit",
            proposal_ref=handle,
            ctx=ctx,
        )
    )
    assert result.is_error
    assert (
        result.structured_content["error_code"] == "confirmation_declined"
    )
    assert ctx.calls == 1
    assert delete_calls["n"] == 0
