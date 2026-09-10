"""E7.S3 — shape defaults como caminho principal (schema desconhecido / provider externo)."""

from __future__ import annotations

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.openapi_presentation_profile_deriver_service import (
    OpenApiPresentationProfileDeriverService,
)

configure_domain_infrastructure_ports()


def test_e7_s3_shape_only_without_entity_derives_useful_profile():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/vendor/acme/items",
        entity=None,
        shape="paged_list",
    )
    assert profile.get("openapiDerived") is True
    assert profile.get("openapiShape") == "paged_list"
    assert profile.get("defaultViewPolicy") == "table_when_available"
    assert profile.get("profileKey") == "openapi:shape:paged_list"


def test_e7_s3_unknown_shape_token_falls_back_to_unknown_defaults():
    profile = OpenApiPresentationProfileDeriverService.build_profile(
        entity="ext_weird",
        shape="totally_unknown_shape_xyz",
    )
    assert profile.get("openapiDerived") is True
    assert profile.get("openapiShape") == "unknown"
    assert profile.get("defaultViewPolicy") == "table_when_available"


def test_e7_s3_infer_shape_from_hierarchy_rows():
    shape = OpenApiPresentationProfileDeriverService.infer_shape_from_rows(
        [{"code": "root", "children": [{"code": "c1"}]}]
    )
    assert shape == "hierarchy"
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/ext/partner/tree",
        entity=None,
        shape=None,
        rows=[{"code": "root", "children": [{"code": "c1"}]}],
    )
    assert profile.get("openapiDerived") is True
    assert profile.get("openapiShape") == "hierarchy"
    assert profile.get("defaultViewPolicy") == "tree_when_available"


def test_e7_s3_infer_shape_from_list_rows():
    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/ext/partner/rows",
        rows=[
            {"code": "A", "name": "n1", "status": "ok", "qty": 1},
            {"code": "B", "name": "n2", "status": "ok", "qty": 2},
        ],
    )
    assert profile.get("openapiDerived") is True
    assert profile.get("openapiShape") in {"list", "paged_list", "unknown"}
    assert profile.get("defaultViewPolicy") == "table_when_available"


def test_e7_s3_external_scalar_list_hierarchy_without_local_profile():
    cases = (
        ("scalar", "kpi_when_available"),
        ("list", "table_when_available"),
        ("hierarchy", "tree_when_available"),
    )
    for shape, policy in cases:
        profile = ChatPresentationProfileService.build_resolved_profile(
            path=f"/ext/acme/{shape}",
            entity=f"ext_acme_{shape}",
            shape=shape,
        )
        assert profile.get("openapiDerived") is True, shape
        assert profile.get("defaultViewPolicy") == policy, shape


def test_e7_s3_specialized_entity_still_blocks_blind_derive():
    """Invariante: entityProfiles especializados não são sobrescritos em S3."""

    profile = ChatPresentationProfileService.build_resolved_profile(
        path="/products/10080001/stock",
        entity="product_stock",
        shape="paged_list",
    )
    assert profile.get("openapiDerived") is not True
    assert profile.get("profileKey") == "stock"
