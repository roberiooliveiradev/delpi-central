"""E4.S3 — contrato canônico uxCapability (sem path authority)."""

from __future__ import annotations

from app.domain.services.capability_ux_classifier_service import (
    CapabilityUxClassifierService,
)


_REQUIRED_KEYS = frozenset({"category", "examples", "source", "confidence"})


def test_e4_s3_contract_shape_and_fallback():
    classified = CapabilityUxClassifierService.classify_action(
        {"summary": "zzz", "description": "", "path": "/only/path/matters-not"}
    )
    assert _REQUIRED_KEYS <= set(classified)
    assert isinstance(classified["examples"], list)
    assert classified["category"] == "Outras consultas"
    assert classified["source"] in {"default", "empty"}


def test_e4_s3_path_alone_never_classifies_family():
    a = CapabilityUxClassifierService.classify_action(
        {
            "summary": "",
            "description": "",
            "path": "/products/{code}/stock",
            "operation_id": "opAlpha",
            "tags": [],
        }
    )
    b = CapabilityUxClassifierService.classify_action(
        {
            "summary": "",
            "description": "",
            "path": "/totally/different/{id}/balance",
            "operation_id": "opBeta",
            "tags": [],
        }
    )
    assert a["category"] == b["category"] == "Outras consultas"


def test_e4_s3_entity_shape_beats_path_and_survives_rename():
    base_meta = {"entity": "product", "shape": "stock"}
    left = CapabilityUxClassifierService.attach_to_action(
        {
            "summary": "x",
            "path": "/a/b/c",
            "delpi_metadata": dict(base_meta),
        }
    )
    right = CapabilityUxClassifierService.attach_to_action(
        {
            "summary": "x",
            "path": "/renamed/vendor/on-hand",
            "operationId": "whatever",
            "delpi_metadata": dict(base_meta),
        }
    )
    assert left["delpi_metadata"]["uxCapability"]["category"] == "Estoque de produto"
    assert (
        left["delpi_metadata"]["uxCapability"]["category"]
        == right["delpi_metadata"]["uxCapability"]["category"]
    )
    assert left["delpi_metadata"]["uxCapability"]["source"] == "entity_shape"


def test_e4_s3_no_capability_group_field_invented():
    classified = CapabilityUxClassifierService.classify_action(
        {
            "summary": "Consultar estoque do produto",
            "tags": ["stock"],
            "path": "/x",
        }
    )
    assert "capabilityGroup" not in classified
    assert "x-delpi" not in str(classified)
