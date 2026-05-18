from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


def test_detect_description_intent():
    assert (
        ChatProductQueryIntentService.detect("descrição do produto 10080047")
        == ChatProductQueryIntent.DESCRIPTION
    )


def test_detect_stock_intent():
    assert (
        ChatProductQueryIntentService.detect("busque o estoque desse produto")
        == ChatProductQueryIntent.STOCK
    )


def test_resolve_product_code_from_conversation_context():
    code = ChatProductQueryIntentService.resolve_product_code(
        "busque o estoque desse produto",
        "assistant: Produto 10080047: TERM. PINO RETO",
    )

    assert code == "10080047"


def test_format_direct_answer_description_keeps_only_main_line():
    answer = ChatProductQueryIntentService.format_direct_answer(
        {
            "titulo": "Informações do produto 10080047",
            "linhas": [
                "Produto 10080047: TERM. PINO RETO.",
                "Tipo MP, unidade PC, grupo 1008.",
                "Roteiro: 0 registro(s).",
            ],
        },
        intent=ChatProductQueryIntent.DESCRIPTION,
    )

    assert answer == (
        "Informações do produto 10080047\n\nProduto 10080047: TERM. PINO RETO."
    )


def test_format_direct_answer_full_filters_zero_records():
    answer = ChatProductQueryIntentService.format_direct_answer(
        {
            "titulo": "Informações do produto 10080047",
            "linhas": [
                "Produto 10080047: TERM. PINO RETO.",
                "Tipo MP, unidade PC, grupo 1008.",
                "Roteiro: 0 registro(s).",
            ],
        },
        intent=ChatProductQueryIntent.FULL,
    )

    assert "Roteiro: 0 registro(s)." not in answer
    assert "Tipo MP" in answer
