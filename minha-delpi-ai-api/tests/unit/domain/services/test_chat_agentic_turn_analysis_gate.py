from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)

configure_domain_infrastructure_ports()


def test_skip_agentic_when_turn_analysis_clarify():
    assert ChatOperationalParameterService.should_skip_agentic_loop(
        "programação",
        tool_context={
            "turnAnalysis": {"decision": "clarify", "reason": "vague_term"},
            "directAnswer": "Não ficou claro.",
            "toolCalls": [],
        },
    )


def test_skip_agentic_when_analysis_actions_already_executed():
    assert ChatOperationalParameterService.should_skip_agentic_loop(
        "estoque e estrutura 10080022",
        tool_context={
            "turnAnalysis": {"decision": "execute"},
            "turnAnalysisActionIds": ["get_product_stock", "get_product_structure"],
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {"actionId": "get_product_stock"},
                    "metadata": {"ok": True, "actionId": "get_product_stock"},
                },
                {
                    "name": "execute_external_action",
                    "arguments": {"actionId": "get_product_structure"},
                    "metadata": {"ok": True, "actionId": "get_product_structure"},
                },
            ],
        },
    )
