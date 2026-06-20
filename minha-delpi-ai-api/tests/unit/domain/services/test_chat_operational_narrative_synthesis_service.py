from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_narrative_synthesis_service import (
    ChatOperationalNarrativeSynthesisService,
)

configure_domain_infrastructure_ports()


def _factory_stack_metadata() -> dict:
    return {
        "ok": True,
        "path": "/products/90269002/factory-status",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
            "presentationMode": "summary_then_evidence",
        },
        "stackPresentationPlan": {
            "presentationProfile": "product_factory_status",
            "humanizedSections": True,
        },
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Status fabril\n\nSituação consolidada.",
        },
    }


def test_overview_resolves_product_overview_kind():
    kind = ChatOperationalNarrativeSynthesisService.resolve_synthesis_kind(
        "me fale do produto 10080045"
    )

    assert kind == "product_overview"


def test_factory_status_message_suggests_narrative_before_tools():
    assert ChatOperationalNarrativeSynthesisService.message_suggests_narrative_llm_synthesis(
        "qual o status do produto 90269002 na fabrica hoje?",
    )


def test_factory_status_stack_resolves_summary_then_evidence():
    kind = ChatOperationalNarrativeSynthesisService.resolve_synthesis_kind(
        "qual o status do produto 90269002 na fabrica hoje?",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": _factory_stack_metadata(),
            }
        ],
    )

    assert kind == "summary_then_evidence"


def test_factory_status_stack_forces_llm_in_normal_mode():
    assert ChatOperationalNarrativeSynthesisService.should_force_llm_synthesis(
        "qual o status do produto 90269002 na fabrica hoje?",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": _factory_stack_metadata(),
            }
        ],
    )


def test_factual_narrow_stock_without_narrative_marker_skips_synthesis():
    metadata = {
        "ok": True,
        "path": "/products/10080045/stock",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
        },
        "stackPresentationPlan": {
            "presentationProfile": "product_stock",
        },
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Estoque\n\nFilial 01: 10",
        },
    }

    assert not ChatOperationalNarrativeSynthesisService.should_force_llm_synthesis(
        "estoque do produto 10080045 filial 01 quantidade",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": metadata,
            }
        ],
    )


def test_narrative_stock_stack_forces_llm():
    metadata = {
        "ok": True,
        "path": "/products/10080045/stock",
        "presentationDecision": {
            "selected": "text",
            "layoutMode": "stack",
        },
        "stackPresentationPlan": {
            "presentationProfile": "product_stock",
        },
        "textPresentation": {
            "type": "markdown",
            "markdown": "### Estoque\n\nResumo consolidado.",
        },
    }

    assert ChatOperationalNarrativeSynthesisService.should_force_llm_synthesis(
        "como está o estoque do produto 10080045?",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": metadata,
            }
        ],
    )


def test_build_prompt_policy_addon_for_operational_synthesis():
    addon = ChatOperationalNarrativeSynthesisService.build_prompt_policy_addon(
        "como está o estoque do produto 10080045?",
        response_mode="fast",
    )

    assert "Rápida" in addon or "curta" in addon.lower()

    addon = ChatOperationalNarrativeSynthesisService.build_prompt_policy_addon(
        "qual o status do produto 90269002 na fabrica hoje?",
        response_mode="fast",
    )

    assert "Rápida" in addon or "curta" in addon.lower()
