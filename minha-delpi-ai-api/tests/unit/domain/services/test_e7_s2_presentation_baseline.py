"""E7.S2 — baseline freeze: presentation por shape (authority atual)."""

from __future__ import annotations

from dataclasses import dataclass

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_data_shape_analyzer import (
    ChatPresentationDataShapeAnalyzer,
)
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.openapi_presentation_profile_deriver_service import (
    OpenApiPresentationProfileDeriverService,
)

configure_domain_infrastructure_ports()


@dataclass(frozen=True)
class PresentationBaselineCase:
    family: str
    entity: str
    shape: str
    path_a: str
    path_b: str
    expected_view_policy: str
    expects_openapi_derived: bool
    notes: str


# Frozen 2026-09-10 — authority atual (shape defaults + entity/path residual).
_CORPUS: tuple[PresentationBaselineCase, ...] = (
    PresentationBaselineCase(
        family="scalar",
        entity="ext_acme_kpi",
        shape="scalar",
        path_a="/ext/acme/kpi",
        path_b="/vendor/acme/v2/kpi-summary",
        expected_view_policy="kpi_when_available",
        expects_openapi_derived=True,
        notes="unknown API scalar → openapiDerived",
    ),
    PresentationBaselineCase(
        family="paged_list",
        entity="ext_acme_orders",
        shape="paged_list",
        path_a="/ext/acme/orders",
        path_b="/partner/orders/page",
        expected_view_policy="table_when_available",
        expects_openapi_derived=True,
        notes="unknown API paged list",
    ),
    PresentationBaselineCase(
        family="hierarchy",
        entity="ext_acme_bom",
        shape="hierarchy",
        path_a="/ext/acme/bom",
        path_b="/ext/acme/structure-tree",
        expected_view_policy="tree_when_available",
        expects_openapi_derived=True,
        notes="unknown API hierarchy",
    ),
    PresentationBaselineCase(
        family="composite_analysis",
        entity="ext_acme_dossier",
        shape="composite_analysis",
        path_a="/ext/acme/dossier",
        path_b="/ext/acme/composite",
        expected_view_policy="text_when_available",
        expects_openapi_derived=True,
        notes="unknown API composite",
    ),
    PresentationBaselineCase(
        family="document_export",
        entity="ext_acme_export",
        shape="document_export",
        path_a="/ext/acme/export.xlsx",
        path_b="/ext/acme/downloads/file",
        expected_view_policy="text_when_available",
        expects_openapi_derived=True,
        notes="document export text-first; narrative skip no shape default",
    ),
    PresentationBaselineCase(
        family="specialized_stock_gap",
        entity="product_stock",
        shape="paged_list",
        path_a="/products/10080001/stock",
        path_b="/products/10080001/inventory-positions",
        expected_view_policy="table_when_available",
        expects_openapi_derived=False,
        notes="GAP: entityProfiles force stock JSON even with shape",
    ),
)


def test_e7_s2_corpus_families():
    assert {c.family for c in _CORPUS} == {
        "scalar",
        "paged_list",
        "hierarchy",
        "composite_analysis",
        "document_export",
        "specialized_stock_gap",
    }


def test_e7_s2_shape_defaults_view_policies():
    for case in _CORPUS:
        if case.family == "specialized_stock_gap":
            continue
        defaults = OpenApiPresentationProfileDeriverService.node("openapiShapeDefaults") or {}
        shape_profile = defaults.get(case.shape) or {}
        assert shape_profile.get("defaultViewPolicy") == case.expected_view_policy, case.family


def test_e7_s2_unknown_api_openapi_derived_and_path_rename_stable():
    """R5/PC08 metamorphic: rename path mantém profile openapi quando entity/shape iguais."""

    for case in _CORPUS:
        if not case.expects_openapi_derived:
            continue
        profile_a = ChatPresentationProfileService.build_resolved_profile(
            path=case.path_a,
            entity=case.entity,
            shape=case.shape,
        )
        profile_b = ChatPresentationProfileService.build_resolved_profile(
            path=case.path_b,
            entity=case.entity,
            shape=case.shape,
        )
        assert profile_a.get("openapiDerived") is True, case.family
        assert profile_a.get("defaultViewPolicy") == case.expected_view_policy, case.family
        assert profile_a.get("profileKey") == profile_b.get("profileKey"), case.family
        assert profile_a.get("openapiShape") == case.shape


def test_e7_s2_specialized_entity_still_blocks_shape_derive():
    case = next(c for c in _CORPUS if c.family == "specialized_stock_gap")
    profile = ChatPresentationProfileService.build_resolved_profile(
        path=case.path_a,
        entity=case.entity,
        shape=case.shape,
    )
    assert profile.get("openapiDerived") is not True
    assert profile.get("profileKey") == "stock"


def test_e7_s2_shape_analyzer_families_on_payloads():
    """R5 payload→recommended view (sem profile local)."""

    scalar = ChatPresentationDataShapeAnalyzer.analyze(
        rows=[{"metric": "oee", "value": 0.82}]
    )
    assert scalar["recommended"] in {"kpi", "text", "table"}

    paged = ChatPresentationDataShapeAnalyzer.analyze(
        rows=[
            {"code": "A", "qty": 1},
            {"code": "B", "qty": 2},
            {"code": "C", "qty": 3},
        ]
    )
    assert paged["rows"] == 3
    assert paged["recommended"] in {"table", "bar", "kpi", "text", "donut"}

    hierarchy = ChatPresentationDataShapeAnalyzer.analyze(
        rows=[
            {
                "code": "root",
                "children": [{"code": "child", "qty": 1}],
            }
        ]
    )
    assert hierarchy["hasHierarchy"] is True
    assert hierarchy["recommended"] in {"tree", "table", "text"}

    empty = ChatPresentationDataShapeAnalyzer.analyze(rows=[])
    assert empty["recommended"] == "text"
    assert empty["viewIntent"] == "unknown"


def test_e7_s2_partially_typed_payload_still_analyzes():
    """Schema incompleto: analyzer usa keys presentes (não exige profile)."""

    result = ChatPresentationDataShapeAnalyzer.analyze(
        rows=[{"id": 1, "label": "x", "amount": 10.5, "extra_unknown": None}]
    )
    assert result["columns"] >= 3
    assert "amount" in result["numericKeys"]
    assert result["labelKey"] in {"label", "id", "extra_unknown"}


def test_e7_s2_no_llm_required_for_shape_defaults():
    """R11/R4: defaults determinísticos — sem chamada LLM no deriver."""

    profile = OpenApiPresentationProfileDeriverService.build_profile(
        entity="ext_no_model_call",
        shape="paged_list",
    )
    assert profile["openapiDerived"] is True
    assert profile.get("presentationStrategy") == "as_delivered"
    assert "prompt" not in profile
    assert "model" not in profile
