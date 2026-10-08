"""TV Product Guide V1 (KIC-V1 PHASE 2).

Proves the canonical product-usage registry: bounded fail-closed schema,
existence-deep cross-reference validation against canonical registries,
read-only service, help-safe projection, and single-binding Actions/MCP
surface parity. GUIDANCE_NOT_DOMAIN_TRUTH — never domain state, never AuthZ.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tv_app.application.gpt_actions import GPT_ACTIONS_OPERATION_IDS
from tv_app.application.gpt_actions.capability_surface import (
    build_capability_surface,
)
from tv_app.application.gpt_actions.openapi_builder import (
    assert_operation_ids,
    build_gpt_actions_openapi,
)
from tv_app.application.gpt_actions.vista_agent_intelligence_service import (
    VistaAgentIntelligenceService,
    clear_vista_agent_intelligence_cache,
)
from tv_app.application.product_guide.product_guide_registry import (
    CONTENT_DIR,
    REGISTRY_VERSION,
    ProductGuideRegistry,
    get_product_guide_registry,
)
from tv_app.application.product_guide.product_guide_schema import (
    GUIDE_SECTIONS,
    PRODUCT_GUIDE_AUTHORITY,
    PRODUCT_GUIDE_SCHEMA,
    ProductGuideValidationError,
    parse_product_guide,
)
from tv_app.application.product_guide.product_guide_service import (
    HELP_VIEW_FIELDS,
    ProductGuideNotFoundError,
    ProductGuideService,
)
from tv_app.interface.mcp.constants import MCP_TOOL_NAMES

WAVE_1_TOPICS = {
    "tv_dashboard_overview",
    "playlist",
    "slide",
    "block_types",
    "data_sources",
    "data_models",
    "data_bindings",
    "filters_and_layering",
    "display_formats",
    "data_route_discovery",
    "visual_verification",
}

_INTERNAL_FIELDS = {
    "schema",
    "capability_refs",
    "operation_refs",
    "read_refs",
    "write_refs",
    "source_refs",
    "agent_guidance",
}


def _registry() -> ProductGuideRegistry:
    get_product_guide_registry.cache_clear()
    clear_vista_agent_intelligence_cache()
    return get_product_guide_registry()


def _valid_guide(topic_id: str = "sample_topic") -> dict:
    return {
        "schema": PRODUCT_GUIDE_SCHEMA,
        "id": topic_id,
        "title": "Sample",
        "summary": "Summary.",
        "authority": PRODUCT_GUIDE_AUTHORITY,
        "purpose": "Purpose.",
        "use_when": ["case"],
        "do_not_use_when": ["other"],
        "how_to_use": ["step"],
        "quality_rules": ["rule"],
        "common_mistakes": ["mistake"],
        "related_topics": [],
        "capability_refs": [],
        "operation_refs": [],
        "read_refs": [],
        "write_refs": [],
        "source_refs": [{"ref": "x", "classification": "PROVEN"}],
    }


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------


def test_schema_accepts_valid_guide():
    guide = parse_product_guide(_valid_guide())
    assert guide["id"] == "sample_topic"
    assert guide["authority"] == PRODUCT_GUIDE_AUTHORITY


@pytest.mark.parametrize("missing", ["id", "title", "summary", "authority", "purpose"])
def test_schema_rejects_missing_required_field(missing):
    raw = _valid_guide()
    raw.pop(missing)
    with pytest.raises(ProductGuideValidationError):
        parse_product_guide(raw)


def test_schema_rejects_invalid_authority():
    raw = _valid_guide()
    raw["authority"] = "DOMAIN_TRUTH"
    with pytest.raises(ProductGuideValidationError):
        parse_product_guide(raw)


def test_schema_is_closed_against_unknown_keys():
    raw = _valid_guide()
    raw["ui_refs"] = ["/apps/tv-dashboard"]
    with pytest.raises(ProductGuideValidationError):
        parse_product_guide(raw)


def test_schema_rejects_bad_source_ref_classification():
    raw = _valid_guide()
    raw["source_refs"] = [{"ref": "x", "classification": "GUESSED"}]
    with pytest.raises(ProductGuideValidationError):
        parse_product_guide(raw)


# ---------------------------------------------------------------------------
# Registry — real content + fail-closed behavior
# ---------------------------------------------------------------------------


def test_wave_1_registry_loads_exactly_11_topics():
    registry = _registry()
    assert set(registry.topic_ids()) == WAVE_1_TOPICS
    assert registry.version == REGISTRY_VERSION


def test_registry_index_shape():
    index = _registry().index()
    assert len(index) == 11
    for entry in index:
        assert set(entry) == {"id", "title", "summary", "authority"}
        assert entry["authority"] == PRODUCT_GUIDE_AUTHORITY


def _write_topic(tmp_path: Path, topic_id: str, **overrides) -> Path:
    raw = _valid_guide(topic_id)
    raw.update(overrides)
    path = tmp_path / f"{topic_id}.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return path


def _fixture_registry(tmp_path: Path, *topics: dict) -> ProductGuideRegistry:
    for topic in topics:
        _write_topic(tmp_path, topic["id"], **topic)
    return ProductGuideRegistry(
        content_dir=tmp_path,
        capability_ids=lambda: frozenset({"playlist"}),
        operation_ids=lambda: frozenset({"create_block"}),
        neutral_names=lambda: frozenset(
            {"get_catalog", "suggest_change", "prepare_change"}
        ),
    )


def test_registry_rejects_id_filename_mismatch(tmp_path):
    _write_topic(tmp_path, "some_topic", id="other_id")
    with pytest.raises(ProductGuideValidationError):
        _fixture_registry(tmp_path)


def test_registry_rejects_duplicate_ids(tmp_path):
    _write_topic(tmp_path, "dup_a")
    second = _valid_guide("dup_b")
    second["id"] = "dup_a"
    _write_topic(tmp_path, "dup_b", **second)
    with pytest.raises(ProductGuideValidationError):
        _fixture_registry(tmp_path)


def test_registry_rejects_empty_dir(tmp_path):
    with pytest.raises(ProductGuideValidationError):
        _fixture_registry(tmp_path)


def test_registry_rejects_unknown_related_topic(tmp_path):
    _write_topic(tmp_path, "a_topic", related_topics=["ghost_topic"])
    with pytest.raises(ProductGuideValidationError, match="related_topic"):
        _fixture_registry(tmp_path)


def test_registry_rejects_unknown_capability_ref(tmp_path):
    _write_topic(tmp_path, "a_topic", capability_refs=["not_a_capability"])
    with pytest.raises(ProductGuideValidationError, match="capability_ref"):
        _fixture_registry(tmp_path)


def test_registry_rejects_unknown_operation_ref(tmp_path):
    _write_topic(tmp_path, "a_topic", operation_refs=["not_an_op"])
    with pytest.raises(ProductGuideValidationError, match="operation_ref"):
        _fixture_registry(tmp_path)


def test_registry_rejects_invalid_read_and_write_refs(tmp_path):
    _write_topic(tmp_path, "a_topic", read_refs=["prepare_change"])
    with pytest.raises(ProductGuideValidationError, match="read_ref"):
        _fixture_registry(tmp_path)
    tmp2 = tmp_path / "other"
    tmp2.mkdir()
    _write_topic(tmp2, "a_topic", write_refs=["get_catalog"])
    with pytest.raises(ProductGuideValidationError, match="write_ref"):
        ProductGuideRegistry(
            content_dir=tmp2,
            capability_ids=lambda: frozenset(),
            operation_ids=lambda: frozenset(),
            neutral_names=lambda: frozenset(
                {"get_catalog", "prepare_change", "commit_proposal"}
            ),
        )


# ---------------------------------------------------------------------------
# Service — bounded reads, typed failures
# ---------------------------------------------------------------------------


def test_service_index_and_topic():
    service = ProductGuideService(_registry())
    index = service.get_product_guide()
    assert index["schema"] == "product_guide_index_v1"
    assert index["registryVersion"] == REGISTRY_VERSION
    assert {t["id"] for t in index["topics"]} == WAVE_1_TOPICS

    full = service.get_product_guide(topic="playlist")
    assert full["schema"] == "product_guide_v1"
    assert full["guide"]["id"] == "playlist"


def test_service_unknown_topic_fails_typed():
    service = ProductGuideService(_registry())
    with pytest.raises(ProductGuideNotFoundError):
        service.get_product_guide(topic="ghost")
    with pytest.raises(ProductGuideNotFoundError):
        service.get_help_view(topic="ghost")


def test_service_invalid_section_fails_typed():
    service = ProductGuideService(_registry())
    with pytest.raises(ValueError, match="unknown section"):
        service.get_product_guide(topic="playlist", section="everything")


def test_service_section_projection():
    service = ProductGuideService(_registry())
    overview = service.get_product_guide(topic="playlist", section="overview")
    guide = overview["guide"]
    assert {"id", "title", "summary", "authority", "purpose"} == set(guide)
    assert "how_to_use" not in guide


# ---------------------------------------------------------------------------
# Help projection — whitelist, no internal refs
# ---------------------------------------------------------------------------


def test_help_view_strips_internal_fields():
    service = ProductGuideService(_registry())
    view = service.get_help_view()
    assert view["schema"] == "product_guide_help_v1"
    assert len(view["topics"]) == 11
    for topic in view["topics"]:
        assert set(topic) <= set(HELP_VIEW_FIELDS)
        assert not (set(topic) & _INTERNAL_FIELDS)


def test_help_view_single_topic():
    service = ProductGuideService(_registry())
    view = service.get_help_view(topic="slide")
    assert view["topic"]["id"] == "slide"
    assert "related_topics" in view["topic"]


# ---------------------------------------------------------------------------
# Content invariants — special required cases
# ---------------------------------------------------------------------------


def _blob(topic_id: str) -> str:
    return json.dumps(_registry().get(topic_id), ensure_ascii=False)


def test_display_formats_declares_partial_typed_coverage():
    blob = _blob("display_formats")
    assert "PARTIAL" in blob


def test_data_route_discovery_preserves_search_miss_semantics():
    blob = _blob("data_route_discovery")
    assert "SEARCH MISS" in blob and "ABSENCE" in blob
    assert "allowlist" in blob.lower() or "allowlist" in blob


def test_visual_verification_preserves_evidence_ladder():
    blob = _blob("visual_verification").lower()
    assert "canonical_stage" in blob
    assert "digest" in blob or "schematic" in blob
    assert "test_not_run" in blob or "não chega" in blob or "nunca" in blob


def test_no_topic_embeds_full_operation_schema():
    """Guides reference ops by name — never duplicate inputSchema trees."""
    for topic_id in _registry().topic_ids():
        blob = _blob(topic_id)
        assert "inputSchema" not in blob
        assert "properties" not in blob


def test_no_topic_mentions_retired_copilot_surface():
    for topic_id in _registry().topic_ids():
        blob = _blob(topic_id).lower()
        assert "/data/copilot" not in blob
        assert "data_copilot" not in blob


def test_every_topic_has_provenance():
    for topic_id in _registry().topic_ids():
        guide = _registry().get(topic_id)
        assert guide["source_refs"], topic_id
        for ref in guide["source_refs"]:
            assert ref["classification"] in {"PROVEN", "INFERRED", "PROPOSED"}


# ---------------------------------------------------------------------------
# Surface parity — one semantic binding, two transports
# ---------------------------------------------------------------------------


def test_parity_map_covers_product_guide_capability():
    doc = VistaAgentIntelligenceService.document()
    parity = doc["surface_parity"]["parity_map"]
    assert parity["gpt_get_product_guide"] == "get_product_guide"
    assert "get_product_guide" in MCP_TOOL_NAMES
    assert "gpt_get_product_guide" in GPT_ACTIONS_OPERATION_IDS


def test_openapi_includes_product_guide_operation():
    doc = build_gpt_actions_openapi()
    assert_operation_ids(doc)
    op = doc["paths"]["/gpt-actions/v1/product-guides"]["get"]
    assert op["operationId"] == "gpt_get_product_guide"
    param_names = {p["name"] for p in op["parameters"]}
    assert param_names == {"topic", "section"}


def test_mcp_tool_registered():
    from tv_app.interface.mcp.tool_bridge import list_tool_names

    assert "get_product_guide" in list_tool_names()


def test_capability_surface_declares_product_guide_analysis():
    surface = build_capability_surface(transport="mcp")
    ids = {a["id"] for a in surface["analyses"]}
    assert "product_guide" in ids


def test_dispatch_get_product_guide_read_only():
    from tv_app.application.gpt_actions.dispatch_service import (
        GptActionsDispatchService,
    )

    dispatch = GptActionsDispatchService.__new__(GptActionsDispatchService)
    user = SimpleNamespace(permissions=["tv-dashboard.read"], id="u1")
    data = dispatch.get_product_guide(user=user)
    assert data["schema"] == "product_guide_index_v1"
    topic = dispatch.get_product_guide(user=user, topic="data_models", section="overview")
    assert topic["guide"]["id"] == "data_models"


def test_get_catalog_embeds_compact_index_not_bodies():
    from tv_app.application.gpt_actions.dispatch_service import (
        GptActionsDispatchService,
    )

    dispatch = GptActionsDispatchService.__new__(GptActionsDispatchService)
    user = SimpleNamespace(permissions=["tv-dashboard.write"], id="u1")
    doc = dispatch.get_catalog(user=user, transport="mcp")
    index = doc["productGuide"]
    assert index["schema"] == "product_guide_index_v1"
    assert index["readCapability"] == "get_product_guide"
    assert {t["id"] for t in index["topics"]} == WAVE_1_TOPICS
    # Index entries carry no bodies — on-demand fetch only.
    for entry in index["topics"]:
        assert "how_to_use" not in entry
    # Actions envelope sits at the ~100 KiB ceiling — the index is
    # MCP-primary; Actions discovers the capability via gpt_get_product_guide.
    actions_doc = dispatch.get_catalog(user=user, transport="actions")
    assert "productGuide" not in actions_doc


def test_knowledge_orchestration_product_usage_is_proven():
    doc = VistaAgentIntelligenceService.document()
    source = doc["knowledge_orchestration"]["sources"]["product_usage"]
    assert source["status"] == "PROVEN"
    assert any("get_product_guide" in r for r in source["reads"])
