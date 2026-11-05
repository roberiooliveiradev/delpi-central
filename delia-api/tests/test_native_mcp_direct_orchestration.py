"""NATIVE-MCPTOOLSET-DIRECT-ORCHESTRATION-01 — RED tests.

Proves the Pydantic AI investigation runtime exposes owner MCP tools
natively (no ``invoke_read_capability``/``list_read_capabilities``
proxy meta-tools) while every call still passes ``process_tool_call``
into the governed Application boundary before the wire.
"""

from __future__ import annotations

from app.application.interaction.turn_budget import TurnDeadline
from app.application.specialist_interop.errors import (
    MCP_AUTHENTICATION_FAILED,
    SpecialistInteropError,
)
from app.domain.specialist_interop.model import SpecialistOperationClass
from app.infrastructure.orchestration.pydantic_ai_investigation import (
    PydanticAiInvestigationOrchestrator,
)
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel
from tests.support.capability_fixtures import (
    FakeProvider,
    _cap,
    _group,
)
from tests.support.native_mcp_fixtures import (
    native_toolset_stub,
    owner_tool_server,
    recording_owner_tool_server,
)
from tests.test_pydantic_ai_semantic_rework import (
    _final_answer,
    _gates,
)

_PROXY_META_TOOLS = {"invoke_read_capability", "list_read_capabilities"}


def _read_cap(catalog):
    return next(c for c in catalog if c["operation_class"] == "READ")


def test_meta_proxy_tools_are_not_exposed_to_the_agent():
    """The generic MCP proxies must not exist among the Agent tools."""
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    read = _read_cap(catalog)
    offered: set[str] = set()

    def _fn(messages, info):
        offered.update(t.name for t in info.function_tools)
        return _final_answer("done")

    servers = {
        "alpha": owner_tool_server(
            "alpha", {"search_items": "read items"}
        ),
        "beta": owner_tool_server(
            "beta", {"read_guidance": "read guidance"}
        ),
    }
    with native_toolset_stub(servers):
        engine = PydanticAiInvestigationOrchestrator(
            gates, model=FunctionModel(_fn), tool_calls_limit=2
        )
        engine.attempt("estrutura 90260147")
    assert offered, "agent must be offered real tools"
    assert _PROXY_META_TOOLS.isdisjoint(offered)


def test_native_owner_tools_exposed_with_capability_id_names():
    """Each eligible owner capability is a native tool whose name is
    the capability_id itself (e.g. ``alpha.search_items``)."""
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    read = _read_cap(catalog)
    offered: set[str] = set()

    def _fn(messages, info):
        offered.update(t.name for t in info.function_tools)
        return _final_answer("done")

    servers = {
        "alpha": owner_tool_server(
            "alpha", {"search_items": "read items"}
        ),
        "beta": owner_tool_server(
            "beta", {"read_guidance": "read guidance"}
        ),
    }
    with native_toolset_stub(servers):
        engine = PydanticAiInvestigationOrchestrator(
            gates, model=FunctionModel(_fn), tool_calls_limit=2
        )
        engine.attempt("estrutura 90260147")
    assert read["capability_id"] in offered


def test_native_tool_call_flows_through_process_tool_call_governance():
    """A native owner-tool call reaches ``_governed_semantic_tool_invoke``
    exactly once — intercepted before the SDK client hits the wire."""
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    read = _read_cap(catalog)
    invocations: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kw):
        invocations.append(kw.get("capability_id"))
        return original(**kw)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    wire_calls: list[str] = []

    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        if steps["n"] == 1:
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        read["capability_id"],
                        {"arguments": {"query": "terminal"}},
                    )
                ]
            )
        return _final_answer("done")

    servers = {
        "alpha": recording_owner_tool_server(
            "alpha",
            {"search_items": ("read items", {"ok": True})},
            wire_calls,
        ),
        "beta": owner_tool_server(
            "beta", {"read_guidance": "read guidance"}
        ),
    }
    with native_toolset_stub(servers):
        engine = PydanticAiInvestigationOrchestrator(
            gates, model=FunctionModel(_fn), tool_calls_limit=4
        )
        engine.attempt("consulte terminal")
    assert invocations == [read["capability_id"]]
    assert not wire_calls, (
        "process_tool_call must intercept before the SDK wire call"
    )


def test_unadvertised_capability_never_reaches_the_wire():
    """A capability outside the live eligible surface is never
    registered — the model cannot invoke it and the governed boundary
    never receives it."""
    gates = _gates()
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    read = _read_cap(catalog)
    invocations: list[str] = []
    original = gates._governed_semantic_tool_invoke

    def _spy(**kw):
        invocations.append(kw.get("capability_id"))
        return original(**kw)

    gates._governed_semantic_tool_invoke = _spy  # type: ignore[method-assign]
    wire_calls: list[str] = []
    steps = {"n": 0}

    def _fn(messages, _info):
        steps["n"] += 1
        if steps["n"] == 1:
            # the model asks for a capability it was never offered
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        "alpha.secret_admin_read",
                        {"arguments": {"query": "x"}},
                    )
                ]
            )
        return _final_answer("done")

    servers = {
        "alpha": recording_owner_tool_server(
            "alpha",
            {
                "search_items": ("read items", {"ok": True}),
                # the owner advertises it on the wire, but DÉLIA's live
                # eligible surface does not include it → not registered
                "secret_admin_read": ("admin", {"ok": True}),
            },
            wire_calls,
        ),
        "beta": owner_tool_server(
            "beta", {"read_guidance": "read guidance"}
        ),
    }
    with native_toolset_stub(servers):
        engine = PydanticAiInvestigationOrchestrator(
            gates, model=FunctionModel(_fn), tool_calls_limit=4
        )
        engine.attempt("read something")
    assert "alpha.secret_admin_read" not in invocations
    assert "secret_admin_read" not in wire_calls


def test_write_class_capability_is_never_exposed_as_agent_tool():
    """PREPARE/ACT-class capabilities stay off the tool surface — the
    model cannot even name them."""
    write = _cap(
        "alpha",
        "pa",
        "execute_write",
        schema={"type": "object", "properties": {}},
        op_class=SpecialistOperationClass.ACT,
    )
    provider = FakeProvider(
        "pa",
        [
            _group(
                "pa",
                "alpha",
                [_cap("alpha", "pa", "search_items"), write],
            )
        ],
        outcomes={},
    )
    gates = _gates(providers=[provider])
    catalog = gates._project_semantic_tool_catalog(
        correlation="c", deadline=TurnDeadline.start(30.0)
    )
    assert all(
        c["capability_id"] != write.capability_id for c in catalog
    )
    offered: set[str] = set()

    def _fn(messages, info):
        offered.update(t.name for t in info.function_tools)
        return _final_answer("done")

    servers = {
        "alpha": owner_tool_server(
            "alpha",
            {
                "search_items": "read items",
                "execute_write": "write items",
            },
        ),
    }
    with native_toolset_stub(servers):
        engine = PydanticAiInvestigationOrchestrator(
            gates, model=FunctionModel(_fn), tool_calls_limit=2
        )
        engine.attempt("execute the write")
    assert write.capability_id not in offered


def test_credential_failure_blocks_toolset_fail_closed():
    """When the delegated credential/config cannot be obtained, the
    specialist's toolset is absent — never an unauthenticated client."""
    gates = _gates()
    for provider in gates._providers.values():
        provider.native_toolset_config = _raise_credential  # type: ignore[attr-defined]

    offered: set[str] = set()

    def _fn(messages, info):
        offered.update(t.name for t in info.function_tools)
        return _final_answer("done")

    servers = {
        "alpha": owner_tool_server(
            "alpha", {"search_items": "read items"}
        ),
        "beta": owner_tool_server(
            "beta", {"read_guidance": "read guidance"}
        ),
    }
    with native_toolset_stub(servers):
        engine = PydanticAiInvestigationOrchestrator(
            gates, model=FunctionModel(_fn), tool_calls_limit=2
        )
        attempt = engine.attempt("estrutura 90260147")
    assert _PROXY_META_TOOLS.isdisjoint(offered)
    assert not ({"alpha.search_items", "beta.read_guidance"} & offered)


def _raise_credential(group_id, *, timeout_seconds=None):
    raise SpecialistInteropError(
        MCP_AUTHENTICATION_FAILED, "delegated credential unavailable"
    )


def test_internal_obs_marker_is_stripped_from_user_answer():
    """``[obs:N]`` is an internal evidence handle — never user-facing
    answer text; the output validator normalizes it away."""
    import re as _re

    from app.infrastructure.orchestration.pydantic_ai_investigation import (
        _INTERNAL_OBS_MARKER,
    )

    text = "[obs:0]\nDescrição real\n---\n[obs:1]\nPlaylist real"
    cleaned = _INTERNAL_OBS_MARKER.sub("", text)
    assert "[obs:" not in cleaned
    assert "Descrição real" in cleaned and "Playlist real" in cleaned
    # negative: legitimate bracketed text is untouched
    keep = "ver [anexo] e [v2] para detalhes"
    assert _INTERNAL_OBS_MARKER.sub("", keep) == keep


def test_candidate_bound_execute_never_fabricates_token_success():
    """``candidate_token`` is owner-issued: a forged/absent token can
    never produce a successful business attempt — the governed path
    relays owner discovery verbatim and the owner is the validator."""
    from app.application.capability_provision.contracts import (
        CapabilityProviderError,
    )
    from tests.support.capability_fixtures import _outcome

    discover = _cap(
        "alpha",
        "pa",
        "discover_items",
        schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        op_class=SpecialistOperationClass.DISCOVERY,
    )
    execute = _cap(
        "alpha",
        "pa",
        "execute_items",
        schema={
            "type": "object",
            "properties": {
                "candidate_token": {"type": "string"},
                "arguments": {"type": "object"},
            },
            "required": ["candidate_token", "arguments"],
        },
    )
    provider = FakeProvider(
        "pa",
        [_group("pa", "alpha", [discover, execute])],
        outcomes={
            ("alpha", "discover_items"): _outcome(
                "candidates",
                structured={
                    "candidates": [
                        {"candidate_token": "owner-tok-1"}
                    ]
                },
            ),
            # Owner rejects the forged/mismatched token — typed error,
            # never a fabricated success.
            ("alpha", "execute_items"): CapabilityProviderError(
                "owner_argument_rejected", "candidate rejected"
            ),
        },
    )
    gates = _gates(providers=[provider])
    attempt = gates._governed_semantic_tool_invoke(
        capability_id=execute.capability_id,
        arguments={
            "candidate_token": "FORGED-TOKEN",
            "arguments": {"code": "90260147"},
        },
        input_text="execute 90260147",
        correlation="c-neg",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prior_turns=(),
        prepare_only=False,
        deadline=TurnDeadline.start(30.0),
    )
    assert attempt.status.value != "success" or attempt.error_code, (
        "a forged candidate_token must never yield fabricated success"
    )
    # An oversized/malformed candidate_token is rejected at the bounded
    # relay boundary — never reaches the owner.
    provider.calls.clear()
    attempt = gates._governed_semantic_tool_invoke(
        capability_id=execute.capability_id,
        arguments={
            "candidate_token": "x" * 5000,
            "arguments": {"code": "90260147"},
        },
        input_text="execute 90260147",
        correlation="c-neg2",
        actor_user_id="u1",
        session_id="s1",
        workspace_context=None,
        prior_turns=(),
        prepare_only=False,
        deadline=TurnDeadline.start(30.0),
    )
    assert all(
        remote != "execute_items" for remote, _ in provider.calls
    ), "malformed candidate_token must never reach the owner"
