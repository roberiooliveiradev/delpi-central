"""Regras declarativas de section availability — Playbook 12 R4."""

from __future__ import annotations

from app.domain.services.chat_presentation_section_rules_service import (
    ChatPresentationSectionRulesService,
)
from app.domain.services.chat_presentation_stack_order_service import (
    ChatPresentationStackOrderService,
)


def test_factory_section_rules_resolve_tail_visuals():
    metadata = {
        "path": "/products/90269002/factory-status",
        "textPresentation": {"markdown": "### Status\n\n**Destaques**\n\n- OP aberta.\n"},
        "kpiPresentation": {"type": "kpi", "cards": [{"label": "MPs", "value": 1}]},
        "tablePresentations": [
            {
                "type": "table",
                "title": "Panorama fabril",
                "rows": [{"campo": "x", "valor": "1"}],
            },
        ],
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["presentationProfile"] == "product_factory_status"
    assert plan["sectionVisibility"]["profile"] is True
    narrative = plan["narrativeOrder"]
    assert "profileTables" in narrative
    assert "operationalTables" not in narrative
    assert narrative.index("profileTables") < narrative.index("highlights")
    assert "tailVisuals" in narrative


def test_sale_pricing_section_rules_use_visual_panels():
    metadata = {
        "path": "/products/90269001/pricing",
        "textPresentation": {"markdown": "### Preços\n\n**Destaques**\n\n- Tabela vigente.\n"},
        "kpiPresentation": {"type": "kpi", "cards": [{"label": "Preço", "value": "10"}]},
        "tablePresentations": [
            {
                "type": "table",
                "title": "Resumo de precificação",
                "rows": [{"campo": "Preço", "valor": "10"}],
            },
        ],
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["presentationProfile"] == "product_pricing"
    assert plan["sectionVisibility"]["structure"] is True


def test_last_purchase_section_rules_use_visual_panels():
    metadata = {
        "path": "/products/10080001/last-purchase",
        "textPresentation": {
            "markdown": "### Última compra\n\n**Destaques**\n\n- NF recente.\n",
        },
        "kpiPresentation": {"type": "kpi", "cards": [{"label": "Preço", "value": "10"}]},
        "tablePresentations": [
            {
                "type": "table",
                "title": "Resumo da última compra",
                "rows": [{"campo": "Preço", "valor": "10"}],
            },
        ],
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["presentationProfile"] == "product_last_purchase"
    assert plan["humanizedSections"] is True
    assert plan["sectionVisibility"]["structure"] is True


def test_purchase_list_section_rules_enable_humanized_stack():
    metadata = {
        "path": "/products/10080001/purchases",
        "textPresentation": {
            "markdown": "### Compras\n\n**Destaques**\n\n- 3 pedidos.\n",
        },
        "tablePresentations": [
            {
                "type": "table",
                "title": "Resumo da listagem",
                "rows": [{"campo": "Total", "valor": "3"}],
            },
        ],
    }

    plan = ChatPresentationStackOrderService.resolve_plan(metadata)

    assert plan["presentationProfile"] == "product_purchases"
    assert plan["humanizedSections"] is True
    assert "profileTables" in plan["narrativeOrder"]


def test_resolve_explicit_narrative_order_from_json_slots():
    visibility = {
        "scope": True,
        "profile": True,
        "highlights": True,
        "guide": True,
        "structure": False,
        "attention": False,
    }
    slots = [
        "lead",
        "profileTables",
        "highlights",
        "operationalTables",
        "tailVisuals",
        "attention",
    ]

    order = ChatPresentationSectionRulesService._resolve_explicit_narrative_order(
        slots,
        visibility,
        {},
        {},
    )

    assert order == ["lead", "profileTables", "highlights", "operationalTables"]


def test_resolve_visibility_from_json_rules():
    metadata = {
        "path": "/products/90260149/analyser",
        "textPresentation": {
            "markdown": "### Info\n\n**Destaques**\n\n- Estrutura com 6 itens.\n",
        },
        "tablePresentations": [
            {"type": "table", "title": "Produto 90260149", "rows": [{"campo": "Código", "valor": "90260149"}]},
        ],
        "treePresentation": {"type": "tree", "root": {"id": "90260149"}},
    }
    rules = {
        "scope": "markdown",
        "profile": "profile_table",
        "highlights": "highlights_strict",
        "structure": "tree",
    }

    visibility = ChatPresentationSectionRulesService.resolve_visibility(metadata, rules)

    assert visibility["scope"] is True
    assert visibility["profile"] is True
    assert visibility["highlights"] is True
    assert visibility["structure"] is True
