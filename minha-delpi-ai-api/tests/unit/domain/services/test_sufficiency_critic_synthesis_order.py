"""Ordem critic → evidenceRefs → síntese multi-fonte."""

from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_operational_llm_synthesis_context_content_service import (
    ChatOperationalLlmSynthesisContextContentService,
)
from app.domain.services.chat_operational_llm_synthesis_context_service import (
    ChatOperationalLlmSynthesisContextService,
)


def test_merged_follow_up_tool_calls_trigger_multi_source_cross_rule():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/x/stock",
                "operationId": "get_product_stock",
                "dataAnswer": {"profileKey": "stock", "lines": ["saldo 0"]},
            },
        },
        {
            "name": "execute_external_action",
            "metadata": {
                "ok": True,
                "path": "/products/x/sales",
                "operationId": "get_product_sales",
                "dataAnswer": {"profileKey": "generic_list", "lines": ["sem vendas"]},
            },
        },
    ]
    addon = ChatOperationalLlmSynthesisContextService.build_facts_addon(tool_calls)
    cross = ChatOperationalLlmSynthesisContextContentService.multi_source_cross_rule()
    assert cross
    assert cross in addon
