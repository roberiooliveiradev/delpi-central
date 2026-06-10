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
    assert "tailVisuals" in plan["narrativeOrder"]


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
