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


def test_normalize_product_code_strips_mask():
    assert ChatProductQueryIntentService.normalize_product_code("10.080.055") == "10080055"
    assert ChatProductQueryIntentService.extract_product_code("produto 10.080.055") == "10080055"


def test_format_direct_answer_stock_uses_bullets():
    answer = ChatProductQueryIntentService.format_direct_answer(
        {
            "titulo": "Estoque 10080047",
            "linhas": [
                "Filial 01 — quantidade disponível: 120 PC",
                "Roteiro: 0 registro(s).",
            ],
        },
        intent=ChatProductQueryIntent.STOCK,
    )

    assert answer is not None
    assert "**Estoque 10080047**" in answer
    assert "- Filial 01" in answer
    assert "Roteiro" not in answer


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
