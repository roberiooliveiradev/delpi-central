from app.application.services.knowledge_curatorial_metadata_service import (
    build_global_curatorial_metadata,
    enrich_document_payload,
    merge_curatorial_metadata,
    normalize_tags,
)


def test_normalize_tags_splits_and_deduplicates():
    assert normalize_tags("FAQ, onboarding, faq") == ["faq", "onboarding"]


def test_build_global_curatorial_metadata_clamps_scores():
    metadata = build_global_curatorial_metadata(
        category=" Atendimento ",
        tags=["FAQ"],
        namespace="global:core",
        domain="suporte",
        priority=9,
        quality_score=150,
    )

    assert metadata["category"] == "Atendimento"
    assert metadata["tags"] == ["faq"]
    assert metadata["priority"] == 5
    assert metadata["qualityScore"] == 100
    assert metadata["scope"] == "global"


def test_merge_curatorial_metadata_preserves_existing_fields():
    merged = merge_curatorial_metadata(
        {"scope": "global", "origin": "admin_upload", "category": "legado"},
        tags="novo",
        quality_score=40,
    )

    assert merged["origin"] == "admin_upload"
    assert merged["category"] == "legado"
    assert merged["tags"] == ["novo"]
    assert merged["qualityScore"] == 40


def test_enrich_document_payload_exposes_flat_fields():
    payload = enrich_document_payload(
        {
            "category": "rh",
            "tags": ["beneficios"],
            "namespace": "global",
            "domain": "pessoas",
            "priority": 2,
            "qualityScore": 70,
        }
    )

    assert payload == {
        "category": "rh",
        "tags": ["beneficios"],
        "namespace": "global",
        "domain": "pessoas",
        "priority": 2,
        "qualityScore": 70,
    }
