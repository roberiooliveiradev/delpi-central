from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_field_label_resolution_service import (
    ChatPresentationFieldLabelResolutionService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
    invalidate_column_label_cache,
)


def test_resolve_field_labels_uses_column_labels_catalog():
    configure_domain_infrastructure_ports()
    invalidate_column_label_cache()
    service = ExternalActionColumnLabelService()

    labels = service.resolve_field_labels(
        ["product_type", "standard_cost_date", "total_material_cost"],
        enable_discovery=False,
    )

    assert labels["product_type"] == "Tipo de produto"
    assert labels["standard_cost_date"] == "Data custo padrão"
    assert labels["total_material_cost"] == "Custo total materiais"


def test_format_field_value_percent_suffix_wins_over_cost_token():
    configure_domain_infrastructure_ports()
    invalidate_column_label_cache()
    service = ExternalActionColumnLabelService()

    assert service.format_field_value("material_cost_vs_pa_standard_percent", 6474.99) == "6.474,99%"
    assert service.format_field_value("returned_materials", 17) == "17"
    assert service.format_field_value("standard_cost_date", "20260531") == "31/05/2026"
    assert service.format_field_value("start_date", "23/07/2026") == "23/07/2026"


def test_build_kv_rows_humanizes_summary_fields():
    configure_domain_infrastructure_ports()
    invalidate_column_label_cache()

    class _Host:
        _active_schema_labels = None
        _active_schema_formats = None

        @staticmethod
        def _format_field_value(key, value, schema_formats=None):
            return ExternalActionColumnLabelService().format_field_value(
                key,
                value,
                schema_formats=schema_formats,
            )

    rows = ChatPresentationFieldLabelResolutionService.build_kv_rows(
        {
            "product_type": "PA",
            "returned_materials": 17,
            "material_cost_vs_pa_standard_percent": 6474.996,
        },
        format_value=_Host._format_field_value,
        profile_name="costImpactOverview",
        enable_discovery=False,
    )
    by_field = {row["campo"]: row["valor"] for row in rows}

    assert by_field["Tipo de produto"] == "PA"
    assert by_field["MPs retornadas"] == "17"
    assert by_field["Custo MP vs custo PA (%)"] == "6.475,00%"
