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
    EVA_LEGACY_TOOL_NAMES,
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
    # Legacy tools retired — none present on the wire surface.
    for legacy in EVA_LEGACY_TOOL_NAMES:
        assert legacy not in by_name, legacy
    assert not by_name["read"].get("_meta", {}).get("delpi/deprecated")


def test_registry_parity_covers_legacy_intents() -> None:
    capabilities = {a.capability for a in SEMANTIC_ACTIONS}
    for cap in (
        "engineering.home", "engineering.overview",
        "lmp.list", "lmp.summary", "lmp.detail",
        "lmp.history_events", "lmp.history_flow",
        "lmp.goal_context", "lmp.department_idd", "lmp.nc_streak",
        "product.structure",
        "routing.steps",
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
    assert data["legacy_surface"]["status"] == "retired"
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
    result = sem.tool_get_context(entity="inexistent_entity")
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


def test_read_product_search_previous_code_filter(monkeypatch) -> None:
    """read(product.search, filters={previous_code}) — linhagem reversa
    oficial propagada ao gateway da api-delpi (G13)."""
    _set_context(_human_user())

    class _Aux:
        calls = {}

        async def fetch_product_search(self, ctx, **kw):
            self.calls["search"] = kw
            return {
                "status": "available",
                "items": [
                    {"code": "90264302", "previous_code": "80015472"}
                ],
            }

    aux = _Aux()
    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: aux
    )
    result = asyncio.run(
        sem.tool_read(
            entity="product",
            action="search",
            filters={"previous_code": "80015472"},
        )
    )
    assert not result.is_error
    assert aux.calls["search"]["previous_code"] == "80015472"


def test_read_product_search_rejects_unknown_filter() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_read(
            entity="product",
            action="search",
            filters={"previous_code_typo": "80015472"},
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "validation"


# --- routing.steps (roteiro de fabricação — SG2 via api-delpi) ---------------


def _routing_items():
    return {
        "status": "available",
        "data": {
            "items": [
                {
                    "branch": "01",
                    "route_code": "01",
                    "product_code": "90264302",
                    "operation_code": "010",
                    "operation_description": "CORTE",
                    "resource_code": "LASER01",
                    "work_center": "CT10",
                    "setup_hours": 0.5,
                    "standard_time_hour_mil": 120.0,
                    "standard_time_hours_piece": 0.12,
                    "standard_time_minutes_piece": 7.2,
                    "operation_type": "1",
                    "mandatory_operation": "S",
                    "mandatory_sequence": "S",
                    "mandatory_report": "N",
                    "component_code": None,
                    "component_description": None,
                    "component_sequence": None,
                    "bom_level": 0,
                },
                {
                    "branch": "01",
                    "route_code": "01",
                    "product_code": "90264302",
                    "operation_code": "020",
                    "operation_description": "DOBRA",
                    "resource_code": "DOBRA01",
                    "work_center": "CT20",
                    "setup_hours": 0.25,
                    "standard_time_hour_mil": 60.0,
                    "standard_time_hours_piece": 0.06,
                    "standard_time_minutes_piece": 3.6,
                    "operation_type": "1",
                    "mandatory_operation": "S",
                    "mandatory_sequence": "S",
                    "mandatory_report": "N",
                    "component_code": None,
                    "component_description": None,
                    "component_sequence": None,
                    "bom_level": 0,
                },
            ],
            "page": None,
            "page_size": None,
            "total": 2,
            "total_pages": None,
        },
    }


def test_read_routing_steps_delegates(monkeypatch) -> None:
    """read(routing.steps) — ref → product_code; filtros e paginação
    propagados ao gateway delegado; payload oficial preservado."""
    _set_context(_human_user())

    class _Aux:
        calls = {}

        async def fetch_product_guide(self, ctx, **kw):
            self.calls["guide"] = kw
            return _routing_items()

    aux = _Aux()
    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: aux
    )
    result = asyncio.run(
        sem.tool_read(
            entity="routing",
            action="steps",
            ref="90264302",
            filters={"branch": "01", "max_depth": 3},
            pagination={"page": 1, "page_size": 50},
        )
    )
    assert not result.is_error
    kw = aux.calls["guide"]
    assert kw["code"] == "90264302"
    assert kw["branch"] == "01"
    assert kw["max_depth"] == 3
    assert kw["page"] == 1 and kw["page_size"] == 50
    payload = result.structured_content
    assert payload["entity"] == "routing"
    assert payload["action"] == "steps"
    ops = payload["data"]["data"]["items"]
    assert [o["operation_code"] for o in ops] == ["010", "020"]
    assert ops[0]["work_center"] == "CT10"
    assert ops[0]["resource_code"] == "LASER01"
    # Tempos trafegam intactos — nunca reconvertidos na borda.
    assert ops[0]["standard_time_hour_mil"] == 120.0
    assert ops[0]["standard_time_minutes_piece"] == 7.2


def test_read_routing_steps_requires_ref() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_read(entity="routing", action="steps")
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "validation"


def test_read_routing_steps_rejects_unknown_filter() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_read(
            entity="routing",
            action="steps",
            ref="90264302",
            filters={"warehouse": "01"},
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "validation"
    assert "allowed_fields" in result.structured_content["data"]


def test_read_routing_steps_forbidden_maps_403(monkeypatch) -> None:
    _set_context(_human_user())

    class _Aux:
        async def fetch_product_guide(self, ctx, **kw):
            return {"status": "forbidden", "reason": "owner_denied"}

    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: _Aux()
    )
    result = asyncio.run(
        sem.tool_read(entity="routing", action="steps", ref="90264302")
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_read_routing_steps_not_found_maps_404(monkeypatch) -> None:
    _set_context(_human_user())

    class _Aux:
        async def fetch_product_guide(self, ctx, **kw):
            return {"status": "not_found", "reason": "not_found"}

    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: _Aux()
    )
    result = asyncio.run(
        sem.tool_read(entity="routing", action="steps", ref="99999999")
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 404


def test_read_routing_steps_empty_is_honest_not_error(monkeypatch) -> None:
    """Produto válido sem roteiro: available + items vazio — ausência
    explícita, nunca operações fabricadas nem erro falso."""
    _set_context(_human_user())

    class _Aux:
        async def fetch_product_guide(self, ctx, **kw):
            return {
                "status": "available",
                "data": {
                    "items": [],
                    "page": None,
                    "page_size": None,
                    "total": 0,
                    "total_pages": None,
                },
            }

    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: _Aux()
    )
    result = asyncio.run(
        sem.tool_read(entity="routing", action="steps", ref="90264302")
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["status"] == "available"
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


def test_read_routing_steps_unavailable_is_honest(monkeypatch) -> None:
    """Falha upstream → status unavailable tipado, nunca sucesso falso."""
    _set_context(_human_user())

    class _Aux:
        async def fetch_product_guide(self, ctx, **kw):
            return {"status": "unavailable", "reason": "timeout"}

    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: _Aux()
    )
    result = asyncio.run(
        sem.tool_read(entity="routing", action="steps", ref="90264302")
    )
    assert not result.is_error
    assert result.structured_content["data"]["status"] == "unavailable"


def test_read_routing_steps_requires_human() -> None:
    _set_context(_human_user(principal_type="service"), "Bearer svc")
    result = asyncio.run(
        sem.tool_read(entity="routing", action="steps", ref="90264302")
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_routing_guide_adapter_calls_owner_route() -> None:
    """Adapter delegado → GET /products/{code}/guide no owner, com o
    Bearer humano propagado — nunca service token nem SQL direto."""
    from engineering_app.application.ports.home_sources import (
        HomeSourceContext,
    )
    from engineering_app.infrastructure.gateways.delegated_auxiliary import (
        ApiDelpiDelegatedAuxiliary,
    )

    class _Client:
        calls = {}

        async def get(
            self,
            path,
            *,
            params=None,
            access_token,
            request_id=None,
            service_token=None,
        ):
            self.calls["path"] = path
            self.calls["params"] = params
            self.calls["access_token"] = access_token
            self.calls["service_token"] = service_token
            return {"items": [], "total": 0}

    client = _Client()
    ctx = HomeSourceContext(
        user_id="u1", access_token="tok", request_id="r1"
    )
    out = asyncio.run(
        ApiDelpiDelegatedAuxiliary(client).fetch_product_guide(
            ctx,
            code="90264302",
            branch="01",
            max_depth=2,
            page=1,
            page_size=50,
        )
    )
    assert out["status"] == "available"
    assert client.calls["path"] == "/products/90264302/guide"
    assert client.calls["access_token"] == "tok"
    assert client.calls["service_token"] is None
    assert client.calls["params"] == {
        "branch": "01",
        "max_depth": 2,
        "page": 1,
        "page_size": 50,
    }


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


def _guide_payload(items):
    return {
        "status": "available",
        "data": {
            "items": items,
            "page": None,
            "page_size": None,
            "total": len(items),
            "total_pages": None,
        },
    }


def _guide_row(product, level, op, wc, res, minutes, setup=0.0, comp=""):
    return {
        "branch": "02",
        "route_code": "01",
        "product_code": product,
        "bom_level": level,
        "operation_code": op,
        "operation_description": f"OP {op}",
        "work_center": wc,
        "resource_code": res,
        "operation_type": "1",
        "standard_time_minutes_piece": minutes,
        "setup_hours": setup,
        "component_code": comp,
        "component_description": f"COMP {comp}" if comp else None,
    }


_BALANCE_ITEMS = [
    _guide_row("90264135", 0, "010", "CT1", "R1", 2.0, comp="C1"),
    _guide_row("90264135", 0, "010", "CT1", "R1", 2.0, comp="C2"),
    _guide_row("90264135", 0, "020", "CT2", "R2", 3.0, setup=1.0, comp="C1"),
    _guide_row("C1", 1, "010", "CT9", "R9", 5.0, comp="MP1"),
]


def _aux_guide(payload):
    class _Aux:
        calls = {}

        async def fetch_product_guide(self, ctx, **kw):
            self.calls["guide"] = kw
            return payload

    return _Aux()


def test_analyze_routing_line_balance_full(monkeypatch) -> None:
    """analyze(routing.line_balance) — cadeia real: roteiro oficial
    deduplicado por componente, estágio por nível, takt e postos."""
    _set_context(_human_user())
    aux = _aux_guide(_guide_payload(_BALANCE_ITEMS))
    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: aux
    )
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={
                "product_code": "90264135",
                "demand": 500,
                "available_minutes": 420,
            },
        )
    )
    assert not result.is_error
    kw = aux.calls["guide"]
    assert kw["code"] == "90264135"
    assert kw["page"] is None and kw["page_size"] is None
    data = result.structured_content["data"]
    assert data["data_class"] == "CALCULATED"
    assert data["unique_operations"] == 3  # op010 deduplicada por comp.
    stages = {s["product_code"]: s for s in data["stages"]}
    p = stages["90264135"]
    assert p["work_content_minutes"] == 5.0
    assert p["takt_minutes"] == 0.84
    assert p["theoretical_min_stations"] == 6
    assert p["bottleneck_candidate"]["operation_code"] == "020"
    # nível 1 analisado como estágio próprio — nunca somado ao nível 0
    assert stages["C1"]["bom_level"] == 1
    assert stages["C1"]["work_content_minutes"] == 5.0
    # setup sem batch_size → reportado à parte, não amortizado
    assert p["setup_minutes_piece_amortized"] is None
    # cenário FFD presente e rotulado
    assert p["balance_scenario"]["data_class"] == "SIMULATION"


def test_analyze_routing_line_balance_partial_missing_params(
    monkeypatch,
) -> None:
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge,
        "build_delegated_auxiliary_source",
        lambda: _aux_guide(_guide_payload(_BALANCE_ITEMS)),
    )
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={"product_code": "90264135"},
        )
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["data_class"] == "PARTIAL"
    assert set(data["missing_parameters"]) == {
        "demand",
        "available_minutes",
    }
    assert data["stages"][0]["takt_minutes"] is None


def test_analyze_routing_line_balance_rejects_unknown_params() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={"product_code": "90264135", "operator_count": 4},
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "validation"
    assert "allowed_fields" in result.structured_content["data"]


def test_analyze_routing_line_balance_requires_product_code() -> None:
    _set_context(_human_user())
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance", parameters={}
        )
    )
    assert result.is_error
    assert result.structured_content["error_code"] == "validation"


def test_analyze_routing_line_balance_empty_routing_honest(
    monkeypatch,
) -> None:
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge,
        "build_delegated_auxiliary_source",
        lambda: _aux_guide(_guide_payload([])),
    )
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={
                "product_code": "90264135",
                "demand": 500,
                "available_minutes": 420,
            },
        )
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["stages"] == []
    assert data["data_class"] == "PARTIAL"


def test_analyze_routing_line_balance_forbidden_upstream(
    monkeypatch,
) -> None:
    _set_context(_human_user())

    class _Aux:
        async def fetch_product_guide(self, ctx, **kw):
            return {"status": "forbidden"}

    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: _Aux()
    )
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={"product_code": "90264135"},
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 403


def test_analyze_routing_line_balance_not_found_upstream(
    monkeypatch,
) -> None:
    _set_context(_human_user())

    class _Aux:
        async def fetch_product_guide(self, ctx, **kw):
            return {"status": "not_found"}

    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: _Aux()
    )
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={"product_code": "99999999"},
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 404


def test_analyze_routing_line_balance_invalid_params_labeled(
    monkeypatch,
) -> None:
    """Parâmetros fornecidos mas inválidos → data_class INVALID +
    análise parcial — nunca rotulados PROVIDED/CALCULATED."""
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge,
        "build_delegated_auxiliary_source",
        lambda: _aux_guide(_guide_payload(_BALANCE_ITEMS)),
    )
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={
                "product_code": "90264135",
                "demand": 0,
                "available_minutes": 420,
            },
        )
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["data_class"] == "PARTIAL"
    assert data["parameters"]["demand"]["data_class"] == "INVALID"
    assert "demand" in data["invalid_parameters"]
    assert data["stages"][0]["takt_minutes"] is None


def test_analyze_routing_line_balance_unavailable_upstream(
    monkeypatch,
) -> None:
    _set_context(_human_user())

    class _Aux:
        async def fetch_product_guide(self, ctx, **kw):
            return {"status": "timeout"}

    monkeypatch.setattr(
        bridge, "build_delegated_auxiliary_source", lambda: _Aux()
    )
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={"product_code": "90264135"},
        )
    )
    assert result.is_error
    assert result.structured_content["status_code"] == 502
    assert result.structured_content["error_code"] == "unavailable"


def test_analyze_routing_line_balance_bom_levels_scope(
    monkeypatch,
) -> None:
    _set_context(_human_user())
    monkeypatch.setattr(
        bridge,
        "build_delegated_auxiliary_source",
        lambda: _aux_guide(_guide_payload(_BALANCE_ITEMS)),
    )
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={
                "product_code": "90264135",
                "demand": 500,
                "available_minutes": 420,
                "bom_levels": [0],
            },
        )
    )
    assert not result.is_error
    data = result.structured_content["data"]
    assert len(data["stages"]) == 1
    assert data["stages"][0]["bom_level"] == 0


def test_analyze_routing_line_balance_requires_human() -> None:
    _set_context(_human_user(principal_type="service"), "Bearer svc")
    result = asyncio.run(
        sem.tool_analyze(
            analysis_type="routing.line_balance",
            parameters={"product_code": "90264135"},
        )
    )
    assert result.is_error


def test_knowledge_routing_balance_guide() -> None:
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="routing.balance_guide")
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["knowledge_version"]
    assert data["sources"]
    assert any("takt" in g.lower() for g in data["guidance"])


def test_knowledge_routing_guided_analysis() -> None:
    _set_context(_human_user())
    result = sem.tool_knowledge(topic="routing.guided_analysis")
    assert not result.is_error
    data = result.structured_content["data"]
    assert data["knowledge_version"]
    assert data["sources"]
    joined = " ".join(data["guidance"]).lower()
    for marker in (
        "routing.steps", "routing.line_balance", "observed",
        "provided", "calculated", "simulation", "unknown",
        "engenharia",
    ):
        assert marker in joined, marker


def test_guided_analysis_discoverable_and_registered() -> None:
    _set_context(_human_user())
    result = sem.tool_get_context(topic="guided")
    assert not result.is_error
    caps = {
        f"{a['entity']}.{a['action']}"
        for a in result.structured_content["data"]["actions"]
    }
    assert "routing.guided_analysis" in caps
    assert "routing.guided_analysis" in sem.knowledge_topics()


def test_mcp_instructions_point_to_guided_analysis() -> None:
    from engineering_app.interface.mcp.branding import (
        EVA_MCP_INSTRUCTIONS,
    )
    assert "routing.guided_analysis" in EVA_MCP_INSTRUCTIONS
    assert "routing.steps" in EVA_MCP_INSTRUCTIONS
    assert "routing.line_balance" in EVA_MCP_INSTRUCTIONS


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
