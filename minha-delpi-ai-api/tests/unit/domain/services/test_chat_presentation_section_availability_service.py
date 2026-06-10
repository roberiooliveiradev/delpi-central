from app.domain.services.chat_presentation_section_availability_service import (
    ChatPresentationSectionAvailabilityService,
)
from app.domain.services.chat_presentation_stack_order_service import (
    ChatPresentationStackOrderService,
)


def test_analyser_humanized_sections_only_when_data_exists():
    metadata = {
        "path": "/products/90260149/analyser",
        "textPresentation": {
            "markdown": (
                "### Informações\n\n"
                "**Destaques**\n\n"
                "- Estrutura com 6 itens.\n\n"
                "**Pontos de atenção encontrados na API:**\n\n"
                "1. Bloqueio «2»."
            ),
        },
        "tablePresentations": [
            {
                "type": "table",
                "title": "Produto 90260149",
                "rows": [{"campo": "Código", "valor": "90260149"}],
            },
            {
                "type": "table",
                "title": "Roteiro de produção — 90260149",
                "rows": [{"product_code": "90260149"}],
            },
        ],
        "treePresentation": {
            "type": "tree",
            "title": "Estrutura",
            "nodes": [{"id": "root", "label": "90260149"}],
        },
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["humanizedSections"] is True
    assert plan["presentationProfile"] == "product_analyser"
    assert plan["sectionVisibility"]["profile"] is True
    assert plan["sectionVisibility"]["guide"] is True
    assert plan["sectionVisibility"]["inspection"] is False
    assert plan["sectionVisibility"]["structure"] is True
    assert "inspection" not in plan["narrativeOrder"] or plan["sectionVisibility"]["inspection"] is False
    framing = plan.get("sectionFraming") or {}
    assert "cadastro" in framing.get("profile", "").lower()
    assert "operações" in framing.get("guide", "").lower()
    assert "90260149" not in framing.get("highlights", "")
    assert "estrutura com" not in " ".join(framing.values()).lower()


def test_stock_route_has_dedicated_humanized_sections():
    metadata = {
        "path": "/products/90260149/stock",
        "textPresentation": {
            "markdown": (
                "### Estoque do produto — 90260149\n\n"
                "**Destaques**\n\n"
                "- Saldo disponível total: **150** un.\n\n"
                "**Pontos de atenção**\n\n"
                "1. Conferir paginação."
            ),
        },
        "tablePresentations": [
            {
                "type": "table",
                "title": "Resumo do estoque",
                "rows": [{"campo": "Produto", "valor": "90260149"}],
            },
            {
                "type": "table",
                "title": "Posições por filial e armazém",
                "rows": [{"branch": "01", "available_quantity": 1}],
            },
        ],
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["humanizedSections"] is True
    assert plan["presentationProfile"] == "product_stock"
    assert plan["sectionVisibility"]["highlights"] is True
    assert plan["sectionVisibility"]["profile"] is True
    assert plan["sectionVisibility"]["guide"] is True
    assert plan["sectionVisibility"].get("inspection") is not True
    assert plan["sectionVisibility"].get("structure") is not True


def test_factory_route_uses_dashboard_only_tail_when_panel_present():
    metadata = {
        "path": "/products/90269002/factory-status",
        "textPresentation": {
            "markdown": (
                "### Status fabril — 90269002\n\n"
                "**Destaques**\n\n"
                "- OP aberta.\n"
            ),
        },
        "kpiPresentation": {
            "type": "kpi",
            "title": "Indicadores fabris",
            "cards": [{"label": "MPs", "value": 1}],
        },
        "treePresentation": {
            "type": "tree",
            "title": "Estrutura",
            "root": {"id": "90269002", "label": "90269002", "children": []},
        },
        "dashboardPresentation": {
            "type": "dashboard",
            "title": "Painel fabril",
            "panels": [{"id": "summary", "presentation": {"type": "kpi", "cards": []}}],
        },
        "tablePresentations": [
            {
                "type": "table",
                "title": "Estoque de matérias-primas",
                "rows": [{"raw_material_code": "10019001"}],
            },
        ],
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["presentationProfile"] == "product_factory_status"
    assert "tailVisuals" in plan["narrativeOrder"]
    assert plan["tailVisualOrder"] == ["dashboard"]


def test_supplies_stock_value_does_not_use_product_stock_stack():
    metadata = {
        "path": "/supplies/stock-value",
        "apiDelpiResponseMeta": {"entity": "supplies_stock_value"},
        "textPresentation": {
            "type": "markdown",
            "markdown": (
                "### Valor total de estoque\n\n"
                "<!-- section:scope -->\n\n"
                "Indicador consolidado de suprimentos."
            ),
        },
        "kpiPresentation": {
            "type": "kpi",
            "title": "Estoque empresa",
            "cards": [{"label": "Valor", "value": "12.5", "unit": "M"}],
        },
        "chartPresentation": {
            "type": "chart",
            "chartType": "line",
            "data": [],
        },
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["presentationProfileKey"] == "kpi_series"
    assert plan["presentationProfile"] != "product_stock"
    assert plan["humanizedSections"] is True
    assert plan.get("sectionFraming", {}).get("scope")
    assert "tailVisuals" in plan["narrativeOrder"]


def test_filter_analyser_highlights_drops_absence_bullets():
    insights = [
        "Estrutura com 6 itens.",
        "Plano de inspeção ainda não cadastrado.",
        "Roteiro de produção ainda não cadastrado.",
        "Não há histórico recente de compra registrado para o produto.",
    ]

    filtered = ChatPresentationSectionAvailabilityService.filter_analyser_highlights(insights)

    assert filtered == ["Estrutura com 6 itens."]
