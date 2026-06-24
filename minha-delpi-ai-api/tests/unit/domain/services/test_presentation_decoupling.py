"""Testes — desacoplamento apresentação (jun/2026)."""

from app.domain.services.chat_data_insight_service import ChatDataInsightService
from app.domain.services.chat_operational_data_commentary_service import (
    ChatOperationalDataCommentaryService,
)
from app.domain.services.chat_presentation_insight_service import (
    ChatPresentationInsightService,
)
from app.domain.services.chat_presentation_operational_metadata_field_service import (
    ChatPresentationOperationalMetadataFieldService,
)
from app.domain.services.chat_presentation_recommendation_service import (
    ChatPresentationRecommendationService,
)
from app.domain.services.chat_presentation_visual_ui_hint_service import (
    ChatPresentationVisualUiHintService,
)
from app.domain.services.chat_product_pricing_insight_service import (
    ChatProductPricingInsightService,
)


from app.domain.services.chat_presentation_prose_delivery_service import (
    ChatPresentationProseDeliveryService,
)


def test_data_answer_lead_preserved_when_profile_declares_template_alignment():
    metadata = {
        "path": "/products/90260882/structure/exclusivity",
        "apiDelpiResponseMeta": {"entity": "product_structure_exclusivity"},
    }

    assert ChatPresentationProseDeliveryService.should_preserve_template_markdown_over_data_answer(
        "**Resposta:** Não — nenhuma MP exclusiva.",
        metadata,
    )
    assert ChatPresentationProseDeliveryService.should_skip_question_synthesis_verdict(metadata)


def test_strip_template_duplicated_commentary_prose_clears_verdict_channels():
    metadata = {
        "path": "/products/90260882/structure/exclusivity",
        "apiDelpiResponseMeta": {"entity": "product_structure_exclusivity"},
    }
    commentary = {
        "profileKey": "structure_exclusivity",
        "summary": "Resposta duplicada",
        "interpretation": "Composição duplicada",
        "highlights": ["Resposta duplicada", "Composição duplicada"],
        "summaryLines": ["Resposta duplicada"],
        "attention": ["Ponto operacional"],
        "limitations": ["Lista truncada"],
    }

    cleaned = ChatPresentationProseDeliveryService.strip_template_duplicated_commentary_prose(
        commentary,
        metadata,
    )

    assert cleaned.get("summary") is None
    assert cleaned.get("interpretation") is None
    assert cleaned.get("narrativeInsight") is None
    assert cleaned.get("facts") is None
    assert cleaned.get("highlights") == []
    assert cleaned.get("summaryLines") == []
    assert cleaned.get("attention") == ["Ponto operacional"]
    assert cleaned.get("limitations") == ["Lista truncada"]


def test_operational_metadata_field_service_filters_technical_keys():
    filtered = ChatPresentationOperationalMetadataFieldService.filter_summary(
        {
            "total_records": 50,
            "is_complete": False,
            "branch_filter_applied": False,
            "total_shipped_quantity": 10,
        }
    )

    assert "is_complete" not in filtered
    assert "branch_filter_applied" not in filtered
    assert filtered["total_records"] == 50


def test_stock_commentary_omits_pagination_lines():
    root = {
        "items": [{"available_quantity": 1.0, "committed_quantity": 0.0, "branch": "01"}],
        "total": 99,
    }

    commentary = ChatOperationalDataCommentaryService.build("stock", root)
    combined = "\n".join(
        (commentary or {}).get("highlights", [])
        + (commentary or {}).get("attention", [])
    ).lower()

    assert "página" not in combined
    assert "99" not in combined or "150" in combined or "1" in combined


def test_visual_ui_hint_enriches_table_recommendation():
    decision = {
        "selected": "text",
        "availableViews": ["text", "table"],
    }
    metadata = {"path": "/products/90269001/stock"}

    recommendations = ChatPresentationRecommendationService.build(
        decision=decision,
        metadata=metadata,
    )

    assert any(item.get("view") == "table" for item in recommendations)


def test_insight_prefers_data_answer_summary():
    metadata = {
        "dataAnswer": {
            "summary": {"answer": "Saldo disponível total: **150** un."},
        }
    }

    insight = ChatPresentationInsightService.build_with_metadata(
        selected="table",
        rows=[{"a": 1}],
        metadata=metadata,
    )

    assert "150" in insight


def test_generic_list_skips_large_list_when_operational_incomplete():
    metadata = {
        "apiDelpiResponseMeta": {
            "pagination": {"limit": 50, "returned": 50, "is_complete": False},
        },
    }
    data = {
        "items": [{"value": index} for index in range(30)],
        "pagination": {"limit": 50, "returned": 50, "is_complete": False},
    }

    data_answer = ChatDataInsightService.build(metadata, data)

    assert data_answer
    limitations = "\n".join(data_answer.get("limitations") or []).lower()
    attention = "\n".join(data_answer.get("attention") or []).lower()

    assert "lista extensa" not in attention
    assert "refinar" not in limitations or "limite" in limitations or "parcial" in limitations


def test_pricing_insight_service_builds_commentary():
    root = {
        "product": {"code": "90269001", "description": "PRODUTO", "unit": "PC"},
        "prices": [
            {"table_code": "01", "table_description": "Tabela A", "sale_price": 10.0},
            {"table_code": "02", "table_description": "Tabela B", "sale_price": 20.0},
        ],
    }

    commentary = ChatProductPricingInsightService.build_commentary(root)

    assert commentary
    assert commentary.get("highlights")


def test_resolve_table_hint_for_stock_path():
    hint = ChatPresentationVisualUiHintService.resolve_table_hint(
        path="/products/90269001/stock",
    )

    assert hint
    assert "tabela" in hint.lower()


def test_llm_prose_decoupling_archives_template_without_exposing_markdown():
    from app.domain.services.chat_presentation_llm_prose_decoupling_service import (
        ChatPresentationLlmProseDecouplingService,
    )

    metadata = {
        "ok": True,
        "textPresentation": {"markdown": "### Estoque\n\nSaldo **150** un."},
        "presentationDecision": {"layoutMode": "stack"},
    }

    ChatPresentationLlmProseDecouplingService.decouple_metadata(metadata)

    assert metadata["textPresentation"]["markdown"] == ""
    assert "150" in metadata["templateProseArchive"]["textPresentationMarkdown"]
    assert metadata["llmProseDecoupled"] is True
