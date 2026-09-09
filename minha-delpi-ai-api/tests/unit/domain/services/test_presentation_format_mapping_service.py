"""Unit: PresentationFormatMappingService Spec ↔ MFE dataType."""

from app.domain.services.presentation_format_mapping_service import (
    MFE_DATA_TYPES,
    PresentationFormatMappingService,
)


def test_percentage_maps_to_mfe_percent():
    """Positive: Spec percentage → MFE percent (chatTypes)."""
    assert PresentationFormatMappingService.to_mfe_data_type("percentage") == "percent"
    assert PresentationFormatMappingService.to_mfe_data_type("percentage") in MFE_DATA_TYPES


def test_integer_and_decimal_map_to_number():
    """Sibling: Spec integer/decimal → MFE number."""
    assert PresentationFormatMappingService.to_mfe_data_type("integer") == "number"
    assert PresentationFormatMappingService.to_mfe_data_type("decimal") == "number"
    assert PresentationFormatMappingService.to_mfe_data_type("datetime") == "date"
    assert PresentationFormatMappingService.to_mfe_data_type("duration") == "days"


def test_unknown_format_returns_none():
    """Negative: formato inventado / hex não mapeia."""
    assert PresentationFormatMappingService.to_mfe_data_type("hex") is None
    assert PresentationFormatMappingService.to_mfe_data_type("#089bdb") is None
    assert PresentationFormatMappingService.to_mfe_data_type("") is None
    assert PresentationFormatMappingService.to_mfe_data_type(None) is None


def test_chart_field_format_keeps_percentage():
    """Chart axis formatter entende percentage (não percent)."""
    assert (
        PresentationFormatMappingService.to_chart_field_format("percentage")
        == "percentage"
    )
    assert PresentationFormatMappingService.to_chart_field_format("percent") == "percentage"
    assert PresentationFormatMappingService.map_column_data_types(
        {"rate": "percentage", "qty": "integer", "bad": "nope"}
    ) == {"rate": "percent", "qty": "number"}
    assert PresentationFormatMappingService.map_chart_field_formats(
        {"rate": "percent", "qty": "integer"}
    ) == {"rate": "percentage", "qty": "integer"}


def test_compiler_emits_mfe_datatype_not_spec_percentage():
    """Integração: compiler escreve dataType MFE (percent), não Spec percentage."""
    from app.domain.entities.presentation_data_profile import PresentationDataProfile
    from app.domain.entities.presentation_spec import PresentationSpec
    from app.domain.services.presentation_spec_compiler_service import (
        PresentationSpecCompilerService,
    )

    spec = PresentationSpec(
        view="table",
        fields=("defect_rate", "planned_qty"),
        formats={"defect_rate": "percentage", "planned_qty": "integer"},
    )
    metadata = {
        "tablePresentation": {
            "type": "table",
            "columns": [
                {"key": "defect_rate", "label": "Taxa"},
                {"key": "planned_qty", "label": "Qtd"},
            ],
            "rows": [{"defect_rate": 12.5, "planned_qty": 10}],
        }
    }
    profile = PresentationDataProfile(row_count=1, sampled_row_count=1)
    PresentationSpecCompilerService.compile_into_metadata(
        metadata, spec=spec, profile=profile
    )
    columns = {
        col["key"]: col
        for col in metadata["tablePresentation"]["columns"]
    }
    assert columns["defect_rate"]["dataType"] == "percent"
    assert columns["planned_qty"]["dataType"] == "number"
