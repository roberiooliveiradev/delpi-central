"""SEMANTIC_TOOLS_V1 — closed-vocabulary semantic verbs (A1–A4).

Covers: capability surface projection, get_context, read, analyze,
knowledge — positive, sibling and negative cases, authorization
derivation, closed-vocabulary rejection and no-persistence guarantees.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS
from tv_app.application.gpt_actions.capability_surface import (
    ANALYZE_ACTIONS,
    DELETE_ENTITIES,
    DELETE_VERB_STATUS,
    EXECUTE_ENTITIES,
    EXECUTE_VERB_STATUS,
    KNOWLEDGE_ACTIONS,
    READ_ENTITY_ACTIONS,
    READ_ENTITY_STATUS,
    build_capability_surface,
)
from tv_app.application.gpt_actions.dispatch_service import GptActionsDispatchService
from tv_app.application.gpt_actions.errors import GptActionsError
from tv_app.application.gpt_actions.openapi_builder import (
    assert_operation_ids,
    build_gpt_actions_openapi,
)
from tv_app.interface.mcp.constants import MCP_FORBIDDEN_TOOLS, MCP_TOOL_NAMES, TOOL_CLASS


def _admin():
    return SimpleNamespace(
        is_superadmin=True, permissions=[], id="actor-1", principal_type="user"
    )


def _viewer():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.read"],
        id="viewer-1",
        principal_type="user",
    )


def _writer():
    return SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.read", "tv-dashboard.write"],
        id="writer-1",
        principal_type="user",
    )


def _no_perms():
    return SimpleNamespace(
        is_superadmin=False, permissions=[], id="noperm-1", principal_type="user"
    )


def _dispatch() -> GptActionsDispatchService:
    return GptActionsDispatchService(
        repo=MagicMock(), writes=MagicMock(), commit=MagicMock()
    )


# ---------------------------------------------------------------------------
# Capability surface — semantic_verbs projection
# ---------------------------------------------------------------------------


def test_surface_exposes_six_semantic_verbs():
    surface = build_capability_surface(transport="mcp")
    verbs = surface["semantic_verbs"]
    assert verbs["version"] == "SEMANTIC_TOOLS_V1"
    assert set(verbs["tools"]) == {
        "get_context",
        "read",
        "analyze",
        "knowledge",
        "execute",
        "delete",
    }


def test_surface_read_vocab_is_closed_and_status_honest():
    verbs = build_capability_surface(transport="mcp")["semantic_verbs"]
    entities = verbs["tools"]["read"]["entities"]
    assert set(entities) == set(READ_ENTITY_ACTIONS)
    for entity, actions in READ_ENTITY_ACTIONS.items():
        assert entities[entity]["actions"] == list(actions)
        assert entities[entity]["status"] == READ_ENTITY_STATUS[entity]
    # Planned capabilities are declared, not silently mapped.
    assert entities["slide_preset"]["status"] == "proven"
    assert entities["media_asset"]["status"] == "proven"


def test_surface_write_verbs_planned_until_consent_foundation():
    verbs = build_capability_surface(transport="mcp")["semantic_verbs"]
    assert verbs["tools"]["execute"]["status"] == EXECUTE_VERB_STATUS
    assert verbs["tools"]["delete"]["status"] == DELETE_VERB_STATUS
    confirm = verbs["tools"]["execute"]["confirmation_model"]
    assert confirm["fallback"] == "CONFIRMATION_UNAVAILABLE"


def test_surface_verbs_projection_policy_per_transport():
    """MCP carries the semantic_verbs vocabulary descriptor; the Actions
    projection omits it — the OpenAI 100 KiB envelope is a hard ceiling and
    Actions discovers verbs via first-class vista_* operationIds plus
    vista_get_context effectiveCapabilities instead."""
    mcp = build_capability_surface(transport="mcp")
    actions = build_capability_surface(transport="actions")
    assert set(mcp["semantic_verbs"]["tools"]) == {
        "get_context", "read", "analyze", "knowledge", "execute", "delete",
    }
    assert "semantic_verbs" not in actions


# ---------------------------------------------------------------------------
# get_context
# ---------------------------------------------------------------------------


def test_get_context_admin_sees_all_authorized():
    out = _dispatch().semantic_get_context(user=_admin())
    caps = {c["capability"]: c for c in out["effectiveCapabilities"]}
    assert caps["read.playlist.list"]["authorized"] is True
    assert caps["analyze.intent_materialization"]["authorized"] is True
    assert caps["execute.presentation.apply_mutation"]["authorized"] is True
    assert caps["execute.presentation.apply_mutation"]["status"] == "implemented"
    assert caps["delete.slide"]["authorized"] is True
    assert out["assistant"]["id"] == "vista"
    assert out["confirmationModel"]["fallback"] == "CONFIRMATION_UNAVAILABLE"


def test_get_context_viewer_lacks_write_authorized():
    out = _dispatch().semantic_get_context(user=_viewer())
    caps = {c["capability"]: c for c in out["effectiveCapabilities"]}
    # Catalog informs; AuthZ decides — read caps authorized, write not.
    assert caps["read.playlist.list"]["authorized"] is True
    assert caps["knowledge.search"]["authorized"] is True
    assert caps["analyze.data_block_preview"]["authorized"] is True
    assert caps["analyze.intent_materialization"]["authorized"] is False
    assert caps["execute.presentation.apply_mutation"]["authorized"] is False
    assert caps["delete.block"]["authorized"] is False


def test_get_context_unauthenticated_denied():
    with pytest.raises(PermissionError):
        _dispatch().semantic_get_context(user=_no_perms())


def test_get_context_unknown_action_typed():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_get_context(user=_admin(), action="bogus")
    assert exc.value.code == "UNKNOWN_ACTION"
    assert exc.value.status_code == 422


def test_get_context_catalog_delegates_to_write_catalog():
    out = _dispatch().semantic_get_context(user=_admin(), action="catalog")
    assert "operations" in out or "entities" in out


def test_get_context_catalog_denied_for_viewer():
    """Catalog action delegates to the write catalog — TV_WRITE required."""
    with pytest.raises(PermissionError):
        _dispatch().semantic_get_context(user=_viewer(), action="catalog")


# ---------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------


def test_read_playlist_list_delegates_and_bounds_limit():
    dispatch = _dispatch()
    spy = MagicMock(return_value={"items": []})
    dispatch.list_playlists = spy
    out = dispatch.semantic_read(
        user=_viewer(), entity="playlist", action="list",
        pagination={"limit": 500, "cursor": 3},
    )
    assert out == {"items": []}
    spy.assert_called_once()
    assert spy.call_args.kwargs["limit"] == 100  # capped
    assert spy.call_args.kwargs["offset"] == 3


def test_read_playlist_get_routes_ref_to_context():
    dispatch = _dispatch()
    spy = MagicMock(return_value={"playlist": {}})
    dispatch.get_playlist_context = spy
    dispatch.semantic_read(
        user=_viewer(), entity="playlist", action="get", ref="pl-1",
        filters={"slideId": "sl-9", "includePreview": True},
    )
    kwargs = spy.call_args.kwargs
    assert kwargs["playlist_id"] == "pl-1"
    assert kwargs["preview_slide_id"] == "sl-9"
    assert kwargs["include_preview"] is True


def test_read_playlist_context_sibling_action():
    dispatch = _dispatch()
    spy = MagicMock(return_value={})
    dispatch.get_playlist_context = spy
    dispatch.semantic_read(
        user=_viewer(), entity="playlist", action="context", ref="pl-1"
    )
    assert spy.call_args.kwargs["playlist_id"] == "pl-1"


def test_read_history_routes_ref_and_filters():
    dispatch = _dispatch()
    spy = MagicMock(return_value={})
    dispatch.get_playlist_history = spy
    dispatch.semantic_read(
        user=_viewer(), entity="playlist_history", action="history",
        ref="pl-1", filters={"snapshotId": "snap-2", "page": 2, "pageSize": 5},
    )
    kwargs = spy.call_args.kwargs
    assert kwargs["playlist_id"] == "pl-1"
    assert kwargs["snapshot_id"] == "snap-2"
    assert kwargs["page"] == 2
    assert kwargs["page_size"] == 5


def test_read_data_route_search_uses_declared_filters():
    dispatch = _dispatch()
    spy = MagicMock(return_value={"items": []})
    dispatch.search_data_routes = spy
    dispatch.semantic_read(
        user=_viewer(), entity="data_route", action="search",
        filters={"query": "otd", "limit": 5, "category": "commercial"},
    )
    kwargs = spy.call_args.kwargs
    assert kwargs["query"] == "otd"
    assert kwargs["limit"] == 5
    assert kwargs["category"] == "commercial"


def test_read_data_model_inspect_routes_ref_and_scope():
    dispatch = _dispatch()
    spy = MagicMock(return_value={})
    dispatch.inspect_data_model = spy
    dispatch.semantic_read(
        user=_viewer(), entity="data_model", action="inspect",
        ref="model-7", filters={"playlistId": "pl-1", "slideId": "sl-1"},
    )
    kwargs = spy.call_args.kwargs
    assert kwargs["model_id"] == "model-7"
    assert kwargs["playlist_id"] == "pl-1"
    assert kwargs["slide_id"] == "sl-1"


def test_read_product_guide_uses_ref_as_topic():
    dispatch = _dispatch()
    spy = MagicMock(return_value={})
    dispatch.get_product_guide = spy
    dispatch.semantic_read(
        user=_viewer(), entity="product_guide", action="guide",
        ref="data-model", filters={"section": "overview"},
    )
    kwargs = spy.call_args.kwargs
    assert kwargs["topic"] == "data-model"
    assert kwargs["section"] == "overview"


def test_read_unknown_entity_typed():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_read(
            user=_viewer(), entity="secret_table", action="list"
        )
    assert exc.value.code == "UNKNOWN_ENTITY"
    assert exc.value.status_code == 422


def test_read_unknown_action_typed():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_read(
            user=_viewer(), entity="playlist", action="drop"
        )
    assert exc.value.code == "UNKNOWN_ACTION"


def test_read_media_asset_requires_playlist_ref_fail_closed():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_read(
            user=_viewer(), entity="media_asset", action="list"
        )
    assert exc.value.code == "VALIDATION_ERROR"
    assert exc.value.status_code == 422


def test_read_undeclared_filter_rejected_fail_closed():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_read(
            user=_viewer(), entity="playlist", action="get", ref="pl-1",
            filters={"sql": "DROP TABLE"},
        )
    assert exc.value.code == "VALIDATION_ERROR"
    assert "sql" in exc.value.details["rejectedFilters"]


def test_read_denied_without_permission():
    """Negative authz: no tv-dashboard.read → handler-level denial."""
    dispatch = _dispatch()
    with pytest.raises(PermissionError):
        dispatch.semantic_read(user=_no_perms(), entity="playlist", action="list")


def test_read_never_persists():
    """Sibling check: semantic read path must not touch the write service."""
    writes = MagicMock()
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    dispatch.list_playlists = MagicMock(return_value={"items": []})
    dispatch.semantic_read(user=_viewer(), entity="playlist", action="list")
    writes.assert_not_called()


# ---------------------------------------------------------------------------
# analyze
# ---------------------------------------------------------------------------


def test_analyze_intent_requires_message():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_analyze(
            user=_admin(), analysis="intent_materialization", parameters={}
        )
    assert exc.value.code == "VALIDATION_ERROR"


def test_analyze_intent_delegates_to_suggest_calculation():
    dispatch = _dispatch()
    spy = MagicMock(return_value={"suggestions": []})
    dispatch.suggest_change = spy
    out = dispatch.semantic_analyze(
        user=_writer(),
        analysis="intent_materialization",
        subject_refs={"playlistId": "pl-1"},
        parameters={"message": "crie slide de OTD"},
    )
    assert out["evidenceClass"] == "calculation"
    kwargs = spy.call_args.kwargs
    assert kwargs["message"] == "crie slide de OTD"
    assert kwargs["host_context"] == {"playlistId": "pl-1"}


def test_analyze_block_preview_marks_preview_evidence():
    dispatch = _dispatch()
    spy = MagicMock(return_value={"preview": {}})
    dispatch.preview_data_block = spy
    out = dispatch.semantic_analyze(
        user=_viewer(),
        analysis="data_block_preview",
        subject_refs={"playlistId": "pl-1"},
        parameters={"operationId": "get_otd"},
    )
    assert out["evidenceClass"] == "preview"
    body = spy.call_args.kwargs["body"]
    assert body["playlistId"] == "pl-1"
    assert body["operationId"] == "get_otd"


def test_analyze_model_preview_marks_preview_evidence():
    dispatch = _dispatch()
    spy = MagicMock(return_value={})
    dispatch.preview_data_model = spy
    out = dispatch.semantic_analyze(
        user=_viewer(),
        analysis="data_model_preview",
        subject_refs={"playlistId": "pl-1", "slideId": "s1"},
        parameters={"modelId": "m1"},
    )
    assert out["evidenceClass"] == "preview"
    assert spy.call_args.kwargs["body"]["modelId"] == "m1"


def test_analyze_unknown_analysis_typed():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_analyze(user=_admin(), analysis="train_model")
    assert exc.value.code == "UNKNOWN_ACTION"


def test_analyze_never_persists():
    writes = MagicMock()
    dispatch = GptActionsDispatchService(
        repo=MagicMock(), writes=writes, commit=MagicMock()
    )
    dispatch.preview_data_model = MagicMock(return_value={})
    dispatch.semantic_analyze(user=_viewer(), analysis="data_model_preview")
    writes.assert_not_called()


# ---------------------------------------------------------------------------
# knowledge
# ---------------------------------------------------------------------------


def test_knowledge_get_delegates_to_product_guide():
    dispatch = _dispatch()
    spy = MagicMock(return_value={"topic": "data-model"})
    dispatch.get_product_guide = spy
    out = dispatch.semantic_knowledge(
        user=_viewer(), action="get", topic="data-model", section="overview"
    )
    assert out["topic"] == "data-model"
    kwargs = spy.call_args.kwargs
    assert kwargs["topic"] == "data-model"
    assert kwargs["section"] == "overview"


def test_knowledge_get_without_topic_returns_index():
    dispatch = _dispatch()
    spy = MagicMock(return_value={"topics": []})
    dispatch.get_product_guide = spy
    dispatch.semantic_knowledge(user=_viewer(), action="get")
    assert spy.call_args.kwargs["topic"] is None


def test_knowledge_search_filters_index_deterministically():
    out = _dispatch().semantic_knowledge(
        user=_viewer(), action="search", query="playlist"
    )
    assert out["source"] == "product_guide_registry"
    assert out["evidenceClass"] == "fact"
    assert out["total"] == len(out["topics"])
    for item in out["topics"]:
        hay = f"{item.get('id','')} {item.get('title','')} {item.get('summary','')}".lower()
        assert "playlist" in hay


def test_knowledge_search_empty_query_returns_bounded_index():
    out = _dispatch().semantic_knowledge(user=_viewer(), action="search", limit=3)
    assert out["total"] <= 3


def test_knowledge_search_denied_without_read():
    with pytest.raises(PermissionError):
        _dispatch().semantic_knowledge(user=_no_perms(), action="search")


def test_knowledge_unknown_action_typed():
    with pytest.raises(GptActionsError) as exc:
        _dispatch().semantic_knowledge(user=_viewer(), action="train")
    assert exc.value.code == "UNKNOWN_ACTION"


# ---------------------------------------------------------------------------
# Transport parity — MCP tools + GPT Actions opIds + OpenAPI
# ---------------------------------------------------------------------------


def test_mcp_surface_registers_semantic_verbs():
    for name in ("get_context", "read", "analyze", "knowledge"):
        assert name in MCP_TOOL_NAMES
        assert name in TOOL_CLASS
    # Legacy tools coexist unchanged.
    for legacy in ("list_playlists", "prepare_change", "commit_proposal"):
        assert legacy not in MCP_TOOL_NAMES


def test_mcp_forbidden_names_still_absent():
    new_tools = {"get_context", "read", "analyze", "knowledge"}
    assert not (new_tools & MCP_FORBIDDEN_TOOLS)


def test_actions_operation_ids_include_vista_projection():
    for op in (
        "vista_get_context",
        "vista_read",
        "vista_analyze",
        "vista_knowledge",
    ):
        assert op in GPT_ACTIONS_OPERATION_IDS


def test_openapi_operation_ids_match_registry():
    doc = build_gpt_actions_openapi(server_url="https://example.com/x")
    assert_operation_ids(doc)
    for path in (
        "/gpt-actions/v1/semantic/context",
        "/gpt-actions/v1/semantic/read",
        "/gpt-actions/v1/semantic/analyze",
        "/gpt-actions/v1/semantic/knowledge",
    ):
        assert path in doc["paths"]


def test_parity_map_covers_vista_projection():
    from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
        VistaAgentIntelligenceService,
    )

    parity = VistaAgentIntelligenceService.document()["surface_parity"]["parity_map"]
    assert parity["vista_get_context"] == "get_context"
    assert parity["vista_read"] == "read"
    assert parity["vista_analyze"] == "analyze"
    assert parity["vista_knowledge"] == "knowledge"
