"""TÉO get_product_guide — product usage knowledge foundation V1."""

from __future__ import annotations

import pytest

from tm_app.application.product_guide.product_guide_registry import (
    ProductGuideRegistry,
)
from tm_app.application.product_guide.product_guide_schema import (
    parse_product_guide,
    ProductGuideValidationError,
)
from tm_app.application.product_guide.product_guide_service import (
    ProductGuideNotFoundError,
    ProductGuideService,
)

SEED_TOPICS = {"portal_overview", "interaction_room", "tasks", "process_documents"}


def _service() -> ProductGuideService:
    return ProductGuideService(registry=ProductGuideRegistry())


# ------------------------------------------------------------------- schema


def test_schema_rejects_missing_and_invalid() -> None:
    with pytest.raises(ProductGuideValidationError):
        parse_product_guide({})
    with pytest.raises(ProductGuideValidationError):
        parse_product_guide({"schema": "product_guide_v1"})  # missing fields
    with pytest.raises(ProductGuideValidationError, match="authority"):
        parse_product_guide(
            {
                "schema": "product_guide_v1",
                "id": "x",
                "title": "t",
                "summary": "s",
                "authority": "DOMAIN_TRUTH",
                "purpose": "p",
            }
        )
    with pytest.raises(ProductGuideValidationError, match="classification"):
        parse_product_guide(
            {
                "schema": "product_guide_v1",
                "id": "x",
                "title": "t",
                "summary": "s",
                "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
                "purpose": "p",
                "source_refs": [{"ref": "r", "classification": "MAYBE"}],
            }
        )


# ----------------------------------------------------------------- registry


def test_registry_loads_four_seeds_deterministically() -> None:
    reg = ProductGuideRegistry()
    assert set(reg.topic_ids()) == SEED_TOPICS
    assert reg.version == "product-guide-registry-v1"
    assert len(reg.index()) == 4
    # Deterministic order.
    assert reg.topic_ids() == sorted(reg.topic_ids())


def test_registry_validates_related_topics_and_capability_refs(tmp_path) -> None:
    (tmp_path / "a.json").write_text(
        """{
        "schema": "product_guide_v1", "id": "a", "title": "t", "summary": "s",
        "authority": "GUIDANCE_NOT_DOMAIN_TRUTH", "purpose": "p",
        "related_topics": ["does_not_exist"]}""",
        encoding="utf-8",
    )
    with pytest.raises(ProductGuideValidationError, match="related_topic"):
        ProductGuideRegistry(content_dir=tmp_path)

    (tmp_path / "a.json").write_text(
        """{
        "schema": "product_guide_v1", "id": "a", "title": "t", "summary": "s",
        "authority": "GUIDANCE_NOT_DOMAIN_TRUTH", "purpose": "p",
        "capability_refs": ["does_not_exist"]}""",
        encoding="utf-8",
    )
    with pytest.raises(ProductGuideValidationError, match="capability_ref"):
        ProductGuideRegistry(content_dir=tmp_path)


def test_registry_capability_refs_resolve_against_live_catalog() -> None:
    """Drift guard: every seed capability_ref must be a real catalog id."""
    reg = ProductGuideRegistry()  # raises if any ref is unknown
    assert reg.topic_ids()


# ------------------------------------------------------------------ service


def test_service_index_and_topic_fetch() -> None:
    svc = _service()
    index = svc.get_product_guide()
    assert index["authority"] == "GUIDANCE_NOT_DOMAIN_TRUTH"
    assert {t["id"] for t in index["topics"]} == SEED_TOPICS

    guide = svc.get_product_guide(topic="interaction_room")
    assert guide["guide"]["id"] == "interaction_room"
    assert guide["guide"]["capability_refs"]


def test_service_section_filtering() -> None:
    svc = _service()
    out = svc.get_product_guide(topic="interaction_room", section="how_to_use")
    assert "how_to_use" in out["guide"]
    assert "quality_rules" not in out["guide"]
    quality = svc.get_product_guide(topic="process_documents", section="quality")
    rules = " ".join(quality["guide"]["quality_rules"])
    assert "DOCUMENTATION_COHERENCE_FIRST" in rules


def test_service_unknown_topic_and_section_fail_typed() -> None:
    svc = _service()
    with pytest.raises(ProductGuideNotFoundError):
        svc.get_product_guide(topic="nope")
    with pytest.raises(ValueError, match="unknown section"):
        svc.get_product_guide(topic="tasks", section="bogus")


# ------------------------------------------------------------- surface wiring


def test_capability_bound_once_both_transports() -> None:
    from tm_app.application.intelligence.capability_registry import (
        CAPABILITY_BINDINGS,
    )

    hits = [
        b
        for b in CAPABILITY_BINDINGS
        if any(t.name == "get_product_guide" for t in b.mcp_tools)
    ]
    assert len(hits) == 1
    assert hits[0].actions_operation == "gpt_get_product_guide"
    tool = next(t for t in hits[0].mcp_tools if t.name == "get_product_guide")
    assert tool.tool_class == "READ"


def test_catalog_and_directives_advertise_product_guide() -> None:
    from tm_app.application.gpt_actions.capability_descriptors import (
        build_capability_surface_catalog,
    )

    surface = build_capability_surface_catalog()
    analysis_ids = {a["id"] for a in surface["analyses"]}
    assert "product_guide" in analysis_ids
    directives = surface["agent_directives"]
    assert "product_guide" in str(directives).lower()


def test_mcp_and_openapi_projection() -> None:
    from tm_app.application.gpt_actions.openapi_builder import (
        GPT_ACTIONS_OPERATION_IDS,
        build_gpt_actions_openapi,
    )
    from tm_app.interface.mcp.server import create_mcp_server

    assert "gpt_get_product_guide" in GPT_ACTIONS_OPERATION_IDS
    spec = build_gpt_actions_openapi()
    path = spec["paths"]["/transformometro/gpt-actions/v1/product-guide"]["get"]
    assert path["operationId"] == "gpt_get_product_guide"
    assert path["x-openai-isConsequential"] is False
    assert len(path["description"]) <= 300

    mcp = create_mcp_server()
    tools = mcp._tool_manager.list_tools()
    names = [t.name for t in tools]
    assert "get_product_guide" in names
    guide_tool = next(t for t in tools if t.name == "get_product_guide")
    assert guide_tool.annotations.read_only_hint is True
