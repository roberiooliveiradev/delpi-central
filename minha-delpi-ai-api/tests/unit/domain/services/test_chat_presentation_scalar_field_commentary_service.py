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


def test_matches_scalar_wrapped_in_item_envelope():
    metadata = {
        "path": "/dashboard/department-idd",
        "apiDelpiResponseMeta": {
            "entity": "dashboard_department_idd",
            "shape": "scalar",
            "fields": {"score": "Nota", "contribution": "Contribuição"},
        },
    }
    data = {
        "item": {
            "department_id": "engineering",
            "department_name": "Engenharia",
            "score": 0.0,
            "classification": "Crítico",
            "contribution": 0.0,
            "partial_success": True,
        }
    }

    assert ChatPresentationScalarFieldCommentaryService.matches(metadata, data)

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert "retornou registros" not in str(
        (data_answer.get("summary") or {}).get("answer") or ""
    ).lower()
    anomalies = data_answer.get("anomalies") or []
    assert not any(
        isinstance(item, dict) and item.get("type") == "empty_list" for item in anomalies
    )


def test_insight_department_indicators_not_empty_list():
    metadata = {
        "path": "/dashboard/department-indicators",
        "apiDelpiResponseMeta": {
            "entity": "dashboard_department_indicators",
            "shape": "playbook_report",
            "fields": {"name": "Nome", "goal_value": "Meta", "value": "Realizado"},
        },
    }
    data = {
        "item": {
            "department_id": "engineering",
            "department_name": "Engenharia",
            "idd": 0.0,
            "score": 0.0,
            "classification": "Crítico",
            "indicators": [
                {
                    "indicator_id": "engineering-projects-on-time",
                    "name": "% de Projetos Concluídos no Prazo",
                    "goal_value": 95.0,
                    "value": None,
                    "has_value": False,
                },
                {
                    "indicator_id": "engineering-transforma-plus",
                    "name": "Ganhos Financeiros do TRANSFORMA+ DELPI",
                    "goal_value": 15000.0,
                    "value": None,
                    "has_value": False,
                },
            ],
        }
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert isinstance(data_answer, dict)
    assert "retornou registros" not in str(
        (data_answer.get("summary") or {}).get("answer") or ""
    ).lower()
    anomalies = data_answer.get("anomalies") or []
    assert not any(
        isinstance(item, dict) and item.get("type") == "empty_list" for item in anomalies
    )
    derived = data_answer.get("derivedMetrics") or []
    assert any(
        isinstance(item, dict) and str(item.get("value")) == "2" for item in derived
    )


def test_si_goal_fields_appear_in_scalar_commentary_highlights():
    """goal_value / comparable_goal / reference_goal não ficam em skipFieldKeys."""
    metadata = {
        "path": "/dashboard/si-indicator-meta",
        "apiDelpiResponseMeta": {
            "entity": "dashboard_si_indicator_meta",
            "shape": "scalar",
            "fields": {
                "value": "Realizado",
                "comparable_goal": "Meta do período",
                "goal_value": "Meta cadastrada",
                "reference_goal": "Meta mês (referência)",
            },
        },
    }
    data = {
        "value": 52.1,
        "comparable_goal": 52.1,
        "goal_value": 95.0,
        "reference_goal": 95.0,
    }

    commentary = ChatPresentationScalarFieldCommentaryService.build(metadata, data)

    assert commentary is not None
    joined = "\n".join(commentary.get("highlights") or [])
    assert "Meta cadastrada" in joined
    assert "Meta do período" in joined
    assert "Meta mês (referência)" in joined


def test_si_goal_partial_triad_all_distinct_in_highlights():
    """Mês parcial: três campos distintos devem aparecer nos highlights (matriz E)."""
    metadata = {
        "path": "/dashboard/indicators/quality-kaizen-ideas/meta",
        "apiDelpiResponseMeta": {
            "entity": "dashboard_si_indicator_meta",
            "shape": "scalar",
            "fields": {
                "value": "Valor",
                "comparable_goal": "Meta do período",
                "goal_value": "Meta cadastrada",
                "reference_goal": "Meta mês (referência)",
            },
        },
    }
    data = {
        "value": 4.39,
        "comparable_goal": 4.39,
        "goal_value": 8.0,
        "reference_goal": 8.0,
    }

    commentary = ChatPresentationScalarFieldCommentaryService.build(metadata, data)

    assert commentary is not None
    highlights = commentary.get("highlights") or []
    joined = "\n".join(highlights)
    assert "Meta cadastrada" in joined
    assert "Meta do período" in joined
    assert "Meta mês (referência)" in joined
    assert "8" in joined
    assert "4,39" in joined or "4.39" in joined


def test_si_goal_triad_absent_from_skip_field_keys():
    import json
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[4]
        / "app"
        / "content"
        / "pt-BR"
        / "assistant"
        / "humanized_data_response.json"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    skip = set()
    for section in payload.values():
        if isinstance(section, dict) and isinstance(section.get("skipFieldKeys"), list):
            skip.update(str(k) for k in section["skipFieldKeys"])
    for key in ("goal_value", "comparable_goal", "reference_goal"):
        assert key not in skip, f"{key} must not be in skipFieldKeys"
