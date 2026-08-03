from app.application.services.chat_turn.chat_turn_preparation_tool_routing_service import (
    ChatTurnPreparationToolRoutingService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_format_refinement_skips_missing_product_code_guard():
    guards = ChatTurnPreparationToolRoutingService.resolve_operational_guards(
        message="mostre o último resultado como indicador",
        history_source=[],
        conversation_context="",
        working_memory_snapshot={},
        workspace_context={"agentId": "agent-1"},
        canvas_action=None,
        pre_capability_answer=None,
        analysis_mode=False,
        text_task_pure=False,
    )

    assert guards.missing_product_code_answer is None


def test_format_refinement_does_not_inherit_product_code_from_history_metrics():
    previous = [
        {
            "role": "assistant",
            "content": "OTD com late_ops=117783",
            "metadata": {
                "toolCalls": [
                    {
                        "metadata": {
                            "path": "/production/otd",
                            "kpi": {"late_ops": 117783},
                        }
                    }
                ]
            },
        }
    ]

    code = ChatProductQueryIntentService.resolve_product_code(
        "mostre o último resultado como indicador",
        previous_messages=previous,
    )

    assert code is None
