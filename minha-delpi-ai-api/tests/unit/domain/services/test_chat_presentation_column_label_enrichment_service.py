from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_column_label_enrichment_service import (
    ChatPresentationColumnLabelEnrichmentService,
)


def test_discovery_config_loads_from_column_labels_bundle():
    configure_domain_infrastructure_ports()
    config = ChatPresentationColumnLabelEnrichmentService.discovery_config()

    assert config.get("webSearchQueryTemplate")
    assert config.get("llmSystemPrompt")
    assert config.get("llmResponseHint")


def test_is_catalog_resolved_detects_schema_fields_and_profile_hints():
    assert ChatPresentationColumnLabelEnrichmentService.is_catalog_resolved(
        "unit",
        fields={"unit": "Unidade"},
    )
    assert ChatPresentationColumnLabelEnrichmentService.is_catalog_resolved(
        "route_code",
        schema_labels={"route_code": "Roteiro"},
    )
    assert ChatPresentationColumnLabelEnrichmentService.is_catalog_resolved(
        "custom_field",
        profile_label="Campo customizado",
    )
    assert not ChatPresentationColumnLabelEnrichmentService.is_catalog_resolved(
        "unknown_api_field_xyz",
        fields={"unit": "Unidade"},
    )


def test_build_web_search_query_uses_template():
    configure_domain_infrastructure_ports()
    query = ChatPresentationColumnLabelEnrichmentService.build_web_search_query(
        "impact_on_material_cost_percent"
    )

    assert "impact on material cost percent" in query.lower()
    assert "protheus" in query.lower()


def test_parse_llm_labels_extracts_json_object():
    raw = 'Segue:\n{"future_api_field": "Campo futuro", "extra": "Ignorado"}'
    parsed = ChatPresentationColumnLabelEnrichmentService.parse_llm_labels(
        raw,
        expected_keys=["future_api_field", "missing_key"],
    )

    assert parsed == {"future_api_field": "Campo futuro"}


def test_normalize_label_truncates_long_values():
    label = ChatPresentationColumnLabelEnrichmentService.normalize_label(
        "Rótulo extremamente longo que deveria ser truncado para cabeçalho de tabela"
    )

    assert len(label) <= 48
    assert label.endswith("…")
