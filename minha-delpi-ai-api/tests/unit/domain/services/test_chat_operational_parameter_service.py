from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
)


def test_missing_stock_code_returns_direct_answer():
    answer = ChatOperationalParameterService.resolve_missing_product_code_answer(
        "estoque do produto",
    )

    assert answer is not None
    assert "código" in answer.lower()
    assert ChatOperationalParameterService.should_skip_tools("estoque do produto")


def test_stock_with_code_does_not_short_circuit():
    assert (
        ChatOperationalParameterService.resolve_missing_product_code_answer(
            "estoque do produto 10080099",
        )
        is None
    )
    assert not ChatOperationalParameterService.should_skip_tools(
        "estoque do produto 10080099",
    )


def test_missing_intent_is_stock():
    intent = ChatOperationalParameterService._missing_product_code_intent(
        "estouque do produto",
        None,
    )

    assert intent == ChatProductQueryIntent.STOCK


def test_should_skip_agentic_for_stock_branch_refinement():
    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080022/stock"},
                    }
                ]
            },
        },
    ]

    assert ChatOperationalParameterService.should_skip_agentic_loop(
        "filtre filial 02",
        previous_messages=history,
    )


def test_should_skip_agentic_for_incomplete_stock_question():
    assert ChatOperationalParameterService.should_skip_agentic_loop(
        "estoque do produto",
        conversation_context=None,
        tool_context={"toolCalls": []},
    )


def test_should_skip_tools_after_missing_code_prompt_with_example():
    context = (
        "user: estoque do produto\n"
        "assistant: Para consultar o estoque, informe o codigo do produto "
        "(ex.: 10080099)."
    )

    assert ChatOperationalParameterService.should_skip_tools(
        "estoque do produto",
        conversation_context=context,
    )
    assert (
        ChatOperationalParameterService.resolve_missing_product_code_answer(
            "estoque do produto",
            conversation_context=context,
        )
        is not None
    )
