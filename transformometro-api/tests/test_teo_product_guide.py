"""TÉO get_product_guide — product usage knowledge foundation V1."""

from __future__ import annotations

import json

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

SEED_TOPICS = {
    "portal_overview",
    "interaction_room",
    "tasks",
    "process_documents",
    "process",
    "instance",
    "revision",
    "baseline",
    "measurement",
    "investment",
    "diagram",
    "decomposition",
    "evidence",
    "timeline",
    "impact_effort_matrix",
    "meeting_minutes",
    "shared_resources",
    "resource_costs",
    "diagnostic",
    "dashboard",
    "branch",
    "department",
    "signature_profile",
    "data_transfer",
}


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


def test_registry_loads_all_seeds_deterministically() -> None:
    reg = ProductGuideRegistry()
    assert set(reg.topic_ids()) == SEED_TOPICS
    assert reg.version == "product-guide-registry-v1"
    assert len(reg.index()) == len(SEED_TOPICS)
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


# ----------------------------------------------------------- wave 1: semantics


def test_all_seeds_keep_guidance_authority_and_classified_sources() -> None:
    reg = ProductGuideRegistry()
    for topic in reg.topic_ids():
        guide = reg.get(topic)
        assert guide["authority"] == "GUIDANCE_NOT_DOMAIN_TRUTH"
        assert guide["source_refs"], topic
        for src in guide["source_refs"]:
            assert src["classification"] in ("PROVEN", "INFERRED", "PROPOSED")


def test_instance_explains_melhoria_alias() -> None:
    reg = ProductGuideRegistry()
    guide = reg.get("instance")
    blob = json.dumps(guide, ensure_ascii=False).lower()
    assert "melhoria" in blob
    assert "instância operacional" in guide["title"].lower()


def test_revision_created_is_not_active() -> None:
    reg = ProductGuideRegistry()
    guide = reg.get("revision")
    blob = json.dumps(guide, ensure_ascii=False)
    assert "revisão criada" in blob.lower() or "criada" in blob.lower()
    assert "ativa" in blob.lower()


def test_baseline_is_not_active_scenario_and_unknown_is_not_zero() -> None:
    reg = ProductGuideRegistry()
    baseline = json.dumps(reg.get("baseline"), ensure_ascii=False)
    measurement = json.dumps(reg.get("measurement"), ensure_ascii=False)
    assert "UNKNOWN != 0" in baseline
    assert "UNKNOWN != 0" in measurement
    assert "não é cenário operacional ativo" in baseline.lower() or (
        "cenário operacional ativo" in baseline.lower()
    )


def test_cross_guide_consistency_process_instance_revision() -> None:
    reg = ProductGuideRegistry()
    instance_blob = json.dumps(reg.get("instance"), ensure_ascii=False).lower()
    process_blob = json.dumps(reg.get("process"), ensure_ascii=False).lower()
    # Both guides explain the same distinction: process-mestre != instance.
    assert "processo-mestre" in process_blob
    assert "instance" in instance_blob
    assert "revision" in json.dumps(
        reg.get("instance")["related_topics"]
    )
    # New scenario = revision of the same instance, not a new instance.
    assert "revision" in instance_blob


# ----------------------------------------------------------- wave 2: semantics


def test_diagram_canonical_format_and_mermaid_derived() -> None:
    reg = ProductGuideRegistry()
    blob = json.dumps(reg.get("diagram"), ensure_ascii=False).lower()
    assert "flowchart_v1" in blob
    assert "mermaid" in blob
    assert "derivado" in blob or "derived" in blob
    assert "diagram_catalog" in blob


def test_diagram_distinct_from_decomposition() -> None:
    reg = ProductGuideRegistry()
    diagram = json.dumps(reg.get("diagram"), ensure_ascii=False).lower()
    decomposition = json.dumps(reg.get("decomposition"), ensure_ascii=False).lower()
    assert "decomposition" in diagram
    assert "diagram" in decomposition
    assert "hierarqu" in decomposition
    assert "fluxo" in diagram


def test_evidence_is_not_domain_truth() -> None:
    reg = ProductGuideRegistry()
    blob = json.dumps(reg.get("evidence"), ensure_ascii=False)
    assert "evidence exists != claim proven" in blob
    assert "ui-only" in blob.lower() or "blocked_by_platform" in blob.lower()


def test_timeline_is_not_current_state_authority() -> None:
    reg = ProductGuideRegistry()
    blob = json.dumps(reg.get("timeline"), ensure_ascii=False).lower()
    assert "estado atual" in blob
    assert "o que aconteceu" in blob or "histórico" in blob


def test_impact_effort_matrix_does_not_authorize_decision() -> None:
    reg = ProductGuideRegistry()
    blob = json.dumps(reg.get("impact_effort_matrix"), ensure_ascii=False).lower()
    assert "autoriza" in blob
    assert "calculated" in blob or "calculad" in blob
    assert "prioriza" in blob


def test_process_documents_routes_to_specialized_features() -> None:
    reg = ProductGuideRegistry()
    guide = reg.get("process_documents")
    for topic in ("diagram", "decomposition", "evidence", "timeline",
                  "impact_effort_matrix"):
        assert topic in guide["related_topics"]
        assert topic in " ".join(guide["do_not_use_when"])


# ----------------------------------------------------------- wave 3: semantics


def test_meeting_minutes_distinct_from_room_and_document() -> None:
    reg = ProductGuideRegistry()
    guide = reg.get("meeting_minutes")
    blob = json.dumps(guide, ensure_ascii=False).lower()
    assert "sala" in blob
    assert "process_document" in blob
    assert "interaction_room" in guide["related_topics"]
    assert "formal" in blob


def test_shared_resources_distinct_from_investment() -> None:
    reg = ProductGuideRegistry()
    blob = json.dumps(reg.get("shared_resources"), ensure_ascii=False).lower()
    assert "investment" in blob
    assert "resource_cost" in blob
    assert "resource_costs" in reg.get("shared_resources")["related_topics"]


def test_resource_costs_distinct_and_unknown_not_zero() -> None:
    reg = ProductGuideRegistry()
    guide = reg.get("resource_costs")
    blob = json.dumps(guide, ensure_ascii=False)
    assert "UNKNOWN != 0" in blob
    assert "investment" in blob.lower()
    assert "adjust_shared_resource_cost" in blob
    assert "update genérico" in blob


def test_diagnostic_hypothesis_is_not_fact() -> None:
    reg = ProductGuideRegistry()
    guide = reg.get("diagnostic")
    blob = json.dumps(guide, ensure_ascii=False).lower()
    assert "hypothesis != fact" in blob
    assert "evidence attached != validated" in blob
    assert "methodology" in blob
    assert "stale" in blob


def test_dashboard_is_not_domain_truth_and_recalc_is_governed() -> None:
    reg = ProductGuideRegistry()
    guide = reg.get("dashboard")
    blob = json.dumps(guide, ensure_ascii=False).lower()
    assert "verdade" in blob or "truth" in blob
    assert "recalculate_dashboard" in blob
    assert "ausência" in blob or "ausencia" in blob
    assert "recalculate_dashboard" in guide["capability_refs"]


# ----------------------------------------------------------- wave 4: coverage


def test_branch_and_department_are_distinct() -> None:
    reg = ProductGuideRegistry()
    branch = json.dumps(reg.get("branch"), ensure_ascii=False).lower()
    department = json.dumps(reg.get("department"), ensure_ascii=False).lower()
    assert "filial" in branch and "unidade" in branch
    assert "setor" in department and "departamento" in department
    assert "department" in reg.get("branch")["related_topics"]
    assert "branch" in reg.get("department")["related_topics"]


def test_signature_profile_keeps_binary_ui_only() -> None:
    reg = ProductGuideRegistry()
    blob = json.dumps(reg.get("signature_profile"), ensure_ascii=False).lower()
    assert "display_name" in blob
    assert "ui-only" in blob
    assert "update_signature_profile" in blob


def test_data_transfer_is_ui_only_with_confirm() -> None:
    reg = ProductGuideRegistry()
    guide = reg.get("data_transfer")
    blob = json.dumps(guide, ensure_ascii=False).lower()
    assert "prévia" in blob or "previa" in blob
    assert "confirma" in blob
    assert "ui" in blob
    # No typed capability for import/export — UI feature only.
    assert guide["capability_refs"] == []


def test_main_semantic_aliases_present() -> None:
    reg = ProductGuideRegistry()
    assert "melhoria" in reg.get("instance")["title"].lower()
    assert "filial" in json.dumps(reg.get("branch"), ensure_ascii=False).lower()
    assert "setor" in json.dumps(reg.get("department"), ensure_ascii=False).lower()
    assert "atas" in reg.get("meeting_minutes")["title"].lower()


def test_portal_overview_links_only_valid_topics() -> None:
    reg = ProductGuideRegistry()
    for topic in reg.get("portal_overview")["related_topics"]:
        assert reg.get(topic) is not None, topic


# ----------------------------------------------------- coverage acceptance


# Wave 4 inventory: every user-facing Portal feature classified.
# COVERED features must resolve to a guide; the rest carry an explicit
# non-guide class. Nothing may silently drop off this matrix.
PORTAL_FEATURE_COVERAGE = {
    # COVERED — guide-backed
    "home_overview": "portal_overview",
    "dashboard_metas_idd": "dashboard",
    "processes": "process",
    "improvements": "instance",
    "revisions": "revision",
    "baseline": "baseline",
    "measurement": "measurement",
    "investment": "investment",
    "process_documents": "process_documents",
    "diagram": "diagram",
    "decomposition": "decomposition",
    "evidence": "evidence",
    "diagnostic": "diagnostic",
    "tasks": "tasks",
    "interaction_room": "interaction_room",
    "meeting_minutes": "meeting_minutes",
    "timeline": "timeline",
    "impact_effort_matrix": "impact_effort_matrix",
    "shared_resources": "shared_resources",
    "resource_costs": "resource_costs",
    "branches_units": "branch",
    "departments": "department",
    "signature_profile": "signature_profile",
    "data_transfer": "data_transfer",
    # Non-guide classifications
    "person_directory": "UI_ONLY",
    "binary_attachments": "PLATFORM_BLOCKED",
    "binary_evidence": "PLATFORM_BLOCKED",
    "handwritten_signature": "PLATFORM_BLOCKED",
    "improvement_package": "TECHNICAL_INTERNAL",
}


def test_portal_feature_coverage_has_no_orphans() -> None:
    reg = ProductGuideRegistry()
    for feature, target in PORTAL_FEATURE_COVERAGE.items():
        if target in ("UI_ONLY", "TECHNICAL_INTERNAL", "PLATFORM_BLOCKED"):
            continue
        assert reg.get(target) is not None, f"{feature} -> {target}"


def test_terminology_aliases_present() -> None:
    reg = ProductGuideRegistry()
    assert "documento" in reg.get("process_documents")["title"].lower()
    assert "diagrama" in reg.get("diagram")["title"].lower()
    assert "melhoria" in reg.get("instance")["title"].lower()
    assert "ata" in reg.get("meeting_minutes")["title"].lower()


# --------------------------------------------------- portal help surface


def test_help_view_excludes_internal_fields() -> None:
    svc = ProductGuideService()
    view = svc.get_help_view(topic="tasks")["topic"]
    assert view["id"] == "tasks"
    assert "title" in view and "how_to_use" in view
    for internal in (
        "capability_refs",
        "contract_refs",
        "source_refs",
        "agent_guidance",
        "schema",
        "authority",
    ):
        assert internal not in view


def test_help_view_index_and_unknown_topic() -> None:
    svc = ProductGuideService()
    all_views = svc.get_help_view()
    assert all_views["schema"] == "product_guide_help_v1"
    assert {t["id"] for t in all_views["topics"]} == SEED_TOPICS
    with pytest.raises(ProductGuideNotFoundError):
        svc.get_help_view(topic="nope")


def test_portal_product_guides_route_serves_help_view() -> None:
    """Portal domain route shares the registry — Help Convergence V1."""
    from starlette.testclient import TestClient

    from tests.support.test_app import create_test_app

    client = TestClient(create_test_app())
    index = client.get("/transformometro/product-guides")
    assert index.status_code == 200
    assert {t["id"] for t in index.json()["data"]["topics"]} == SEED_TOPICS

    help_view = client.get("/transformometro/product-guides?view=help")
    assert help_view.status_code == 200
    topic = next(
        t for t in help_view.json()["data"]["topics"] if t["id"] == "tasks"
    )
    assert "capability_refs" not in topic
    assert "how_to_use" in topic

    single = client.get("/transformometro/product-guides/diagram")
    assert single.status_code == 200
    assert single.json()["data"]["topic"]["id"] == "diagram"
    missing = client.get("/transformometro/product-guides/nope")
    assert missing.status_code == 404
