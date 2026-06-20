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


def test_factual_narrow_stock_forces_llm_when_everywhere():
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
    }

    assert ChatOperationalNarrativeSynthesisService.should_force_llm_synthesis(
        "estoque do produto 10080045 filial 01 quantidade",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": metadata,
            }
        ],
    )


def test_factual_narrow_stock_skips_synthesis_when_everywhere_off(monkeypatch):
    from app.domain.services.chat_presentation_prose_delivery_content_service import (
        ChatPresentationProseDeliveryContentService,
    )

    monkeypatch.setattr(
        ChatPresentationProseDeliveryContentService,
        "llm_prose_everywhere",
        lambda: False,
    )

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


def test_playbook_path_uses_playbook_domain_policy():
    addon = ChatOperationalNarrativeSynthesisService.build_prompt_policy_addon(
        "top itens de consumo no periodo",
        response_mode="normal",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/production/consumption/top-items",
                },
            }
        ],
    )

    assert "ranking / playbook operacional" in addon
    assert "Anti-deflexão" in addon or "informações adicionais" in addon


def test_kpi_path_uses_kpi_domain_policy():
    addon = ChatOperationalNarrativeSynthesisService.build_prompt_policy_addon(
        "qual o cpv do periodo",
        response_mode="normal",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/production/kpi/cpv",
                },
            }
        ],
    )

    assert "KPI / indicador" in addon


def test_sql_path_uses_sql_domain_policy():
    addon = ChatOperationalNarrativeSynthesisService.build_prompt_policy_addon(
        "consulta sql",
        response_mode="normal",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": True,
                    "path": "/data/sql/rows",
                },
            }
        ],
    )

    assert "consulta SQL" in addon


def test_failed_tool_uses_error_domain_policy():
    addon = ChatOperationalNarrativeSynthesisService.build_prompt_policy_addon(
        "top itens",
        response_mode="normal",
        tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {
                    "ok": False,
                    "path": "/production/consumption/top-items",
                    "statusCode": 500,
                    "responsePreview": "Internal error",
                },
            }
        ],
    )

    assert "falha de consulta operacional" in addon or "falha operacional" in addon


def test_resolve_policy_kind_splits_operational_data():
    assert (
        ChatOperationalNarrativeSynthesisService._resolve_policy_kind(
            "operational_data",
            [
                {
                    "name": "execute_external_action",
                    "metadata": {"ok": True, "path": "/production/kpi/cpv"},
                }
            ],
        )
        == "kpi_data"
    )

    assert (
        ChatOperationalNarrativeSynthesisService._resolve_policy_kind(
            "operational_data",
            [
                {
                    "name": "execute_external_action",
                    "metadata": {"ok": True, "path": "/production/top-items"},
                }
            ],
        )
        == "playbook_data"
    )
