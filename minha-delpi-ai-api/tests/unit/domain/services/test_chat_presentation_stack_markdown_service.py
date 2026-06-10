from app.domain.services.chat_presentation_stack_markdown_service import (
    ChatPresentationStackMarkdownService,
)
from app.domain.services.chat_presentation_stack_order_service import (
    ChatPresentationStackOrderService,
)


def test_generic_stock_stack_gets_humanized_sections_and_framing():
    metadata = {
        "path": "/products/90260149/stock",
        "textPresentation": {
            "markdown": (
                "### Estoque\n\n"
                "<!-- section:scope -->\n\n"
                "**Destaques**\n\n"
                "- Saldo positivo na filial 01."
            ),
        },
        "tablePresentation": {
            "type": "table",
            "title": "Estoque por filial",
            "rows": [{"branch": "01", "available_quantity": 10}],
        },
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["humanizedSections"] is True
    assert plan["sectionVisibility"]["highlights"] is True
    assert plan["sectionVisibility"]["guide"] is True
    assert plan["sectionFraming"]["highlights"]
    assert "<!-- section:highlights -->" in metadata["textPresentation"]["markdown"]


def test_apply_section_markers_is_idempotent():
    metadata = {
        "textPresentation": {
            "markdown": (
                "### Título\n\n"
                "<!-- section:scope -->\n\n"
                "**Destaques**\n\n"
                "- Um."
            ),
        },
    }
    plan = {"sectionVisibility": {"scope": True, "highlights": True}}

    ChatPresentationStackMarkdownService.apply_section_markers(metadata, plan)
    first = metadata["textPresentation"]["markdown"]

    ChatPresentationStackMarkdownService.apply_section_markers(metadata, plan)

    assert metadata["textPresentation"]["markdown"] == first


def test_kpi_series_stack_gets_humanized_sections_and_framing():
    metadata = {
        "path": "/quality/nonconformities/series",
        "apiDelpiResponseMeta": {"entity": "nonconformity_series"},
        "textPresentation": {
            "markdown": (
                "### Não conformidades\n\n"
                "<!-- section:scope -->\n\n"
                "Série temporal com 2 ponto(s)."
            ),
        },
        "tablePresentation": {
            "type": "table",
            "title": "Série",
            "rows": [
                {"period": "jan/2026", "value": 4},
                {"period": "fev/2026", "value": 6},
            ],
        },
        "chartPresentation": {
            "type": "chart",
            "chartType": "line",
            "data": [],
        },
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["humanizedSections"] is True
    assert plan["presentationProfile"] == "kpi_series"
    assert plan["sectionVisibility"]["scope"] is True
    assert plan["sectionVisibility"]["guide"] is True
    assert plan["sectionVisibility"]["structure"] is True
    assert plan["sectionFraming"]["scope"]
    assert "temporal" in plan["sectionFraming"]["scope"].lower()


def test_inject_scope_marker_after_title():
    metadata = {
        "textPresentation": {
            "markdown": "### Consulta\n\nResumo inicial.",
        },
    }
    plan = {
        "sectionVisibility": {"scope": True, "highlights": False},
        "narrativeOrder": ["lead"],
    }

    ChatPresentationStackMarkdownService.apply_section_markers(metadata, plan)

    assert "<!-- section:scope -->" in metadata["textPresentation"]["markdown"]
