from app.domain.services.chat_data_insight_service import ChatDataInsightService
from app.domain.services.chat_presentation_scalar_field_commentary_service import (
    ChatPresentationScalarFieldCommentaryService,
)


def test_matches_scalar_shape_from_api_meta():
    metadata = {
        "path": "/financial/rol",
        "apiDelpiResponseMeta": {"entity": "financial_rol", "shape": "scalar"},
    }
    data = {"rol": 100.0, "branch": "01"}

    assert ChatPresentationScalarFieldCommentaryService.matches(metadata, data)


def test_build_orders_fields_by_api_meta_labels_before_payload_sort():
    metadata = {
        "path": "/financial/rol",
        "apiDelpiResponseMeta": {
            "entity": "financial_rol",
            "shape": "scalar",
            "fields": {
                "gross_revenue": "Receita bruta",
                "rol": "ROL",
                "icms": "ICMS",
            },
            "fieldFormats": {
                "gross_revenue": "currency",
                "rol": "currency",
                "icms": "currency",
            },
        },
    }
    data = {
        "icms": 911.75,
        "gross_revenue": 13027.76,
        "rol": 10995.66,
        "branch": "01",
    }

    commentary = ChatPresentationScalarFieldCommentaryService.build(metadata, data)

    assert commentary is not None
    assert commentary.get("profileKey") == "generic_kpi_series"

    highlights = commentary.get("highlights") or []

    assert highlights[0].startswith("**ROL:**")
    assert any("**Receita bruta:**" in line for line in highlights)


def test_build_generic_department_kpi_with_value_field():
    metadata = {
        "path": "/supplies/cpv",
        "apiDelpiResponseMeta": {
            "entity": "supplies_cpv",
            "shape": "scalar",
            "fields": {"value": "CPV", "percentage": "Percentual"},
            "fieldFormats": {"value": "currency", "percentage": "percent"},
        },
    }
    data = {"value": 42.5, "percentage": 12.3, "branch": "01"}

    commentary = ChatPresentationScalarFieldCommentaryService.build(metadata, data)

    assert commentary is not None
    joined = "\n".join(commentary.get("highlights") or [])

    assert "CPV" in joined
    assert "Percentual" in joined


def test_insight_pipeline_does_not_classify_scalar_as_empty_list():
    metadata = {
        "path": "/financial/rol",
        "apiDelpiResponseMeta": {
            "entity": "financial_rol",
            "shape": "scalar",
            "fields": {"rol": "ROL", "gross_revenue": "Receita bruta"},
            "fieldFormats": {"rol": "currency", "gross_revenue": "currency"},
        },
    }
    data = {"branch": "01", "gross_revenue": 13027.76, "rol": 10995.66}

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert data_answer.get("profileKey") == "generic_kpi_series"
    assert "retornou registros" not in str(
        (data_answer.get("summary") or {}).get("answer") or ""
    ).lower()

    anomalies = data_answer.get("anomalies") or []

    assert not any(
        isinstance(item, dict) and item.get("type") == "empty_list" for item in anomalies
    )
