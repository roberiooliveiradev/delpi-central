from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


def test_extract_product_code_ignores_date_tokens():
    assert ChatProductQueryIntentService.extract_product_code(
        "cpv de 01/04/2026 a 30/04/2026"
    ) is None
    assert ChatProductQueryIntentService.extract_product_code(
        "qual o cpv do mes passado"
    ) is None


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


def test_detect_sales_intent_over_stock_provider_preference():
    assert (
        ChatProductQueryIntentService.detect("mostre vendas do produto 10080001")
        == ChatProductQueryIntent.SALES
    )


def test_detect_summary_intent():
    assert (
        ChatProductQueryIntentService.detect("resumo do produto 10080047")
        == ChatProductQueryIntent.SUMMARY
    )


def test_detect_parents_intent_from_follow_up_phrase():
    assert (
        ChatProductQueryIntentService.detect("e os pais desse produto")
        == ChatProductQueryIntent.PARENTS
    )


def test_detect_parents_intent_when_product_code_is_between_onde_and_usado():
    assert (
        ChatProductQueryIntentService.detect("onde o produto 10080001 é usado?")
        == ChatProductQueryIntent.PARENTS
    )


def test_detect_parents_intent_for_plural_multi_product_phrase():
    assert (
        ChatProductQueryIntentService.detect(
            "onde são usados os produtos 10080022, 10080012?"
        )
        == ChatProductQueryIntent.PARENTS
    )


def test_detect_summary_not_kaizen_or_sales():
    assert (
        ChatProductQueryIntentService.detect("resumo de vendas do mês")
        != ChatProductQueryIntent.SUMMARY
    )
    assert (
        ChatProductQueryIntentService.detect("resumo de kaizens do mês")
        != ChatProductQueryIntent.SUMMARY
    )


def test_detect_full_analyser_not_summary():
    assert (
        ChatProductQueryIntentService.detect("ficha completa do produto 10080047")
        != ChatProductQueryIntent.SUMMARY
    )


def test_detect_analyser_intent():
    assert (
        ChatProductQueryIntentService.detect(
            "traga a analise completa dos produtos 10080047 e 10080055"
        )
        == ChatProductQueryIntent.ANALYSER
    )


def test_extract_product_code_ignores_example_in_prompt():
    code = ChatProductQueryIntentService.extract_product_code(
        "informe o codigo do produto (ex.: 10080099)"
    )

    assert code is None


def test_extract_product_code_from_bare_code_message():
    assert ChatProductQueryIntentService.extract_product_code("10080022") == "10080022"


def test_references_previous_product_does_not_match_generic_stock_phrase():
    assert not ChatProductQueryIntentService.references_previous_product(
        "estoque do produto"
    )
    assert ChatProductQueryIntentService.references_previous_product(
        "estoque desse produto"
    )


def test_resolve_product_code_from_conversation_context():
    code = ChatProductQueryIntentService.resolve_product_code(
        "busque o estoque desse produto",
        "assistant: Produto 10080047: TERM. PINO RETO",
    )

    assert code == "10080047"


def test_resolve_product_code_uses_last_code_in_context():
    code = ChatProductQueryIntentService.resolve_product_code(
        "estoque do produto",
        "assistant: Produto 10080047: A\nassistant: Produto 10080055: B",
    )

    assert code == "10080055"


def test_resolve_product_code_prioritizes_user_context_items_over_history():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/stock",
                        },
                    }
                ]
            },
        },
    ]
    items = [
        {
            "id": "1",
            "source": "user",
            "kind": "context",
            "label": "10080045",
            "content": "10080045",
            "extractedEntities": {"productCode": "10080045"},
        },
        {
            "id": "2",
            "source": "user",
            "kind": "context",
            "label": "10080055",
            "content": "10080055",
            "extractedEntities": {"productCode": "10080055"},
        },
    ]

    code = ChatProductQueryIntentService.resolve_product_code(
        "qual o estoque",
        previous_messages=history,
        user_context_items=items,
    )

    assert code == "10080055"


def test_resolve_product_code_prioritizes_user_context_prompt_over_history():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/stock",
                        },
                    }
                ]
            },
        },
    ]
    prompt = (
        "Contexto adicionado pelo usuário (priorize nas próximas respostas):\n"
        "- [context] 10080055: 10080055\n\n"
        "assistant: Produto 10080047: TERM. PINO RETO"
    )

    code = ChatProductQueryIntentService.resolve_product_code(
        "estoque do produto",
        prompt,
        previous_messages=history,
    )

    assert code == "10080055"


def test_resolve_product_code_from_tool_metadata_in_history():
    history = [
        {"role": "user", "content": "resumo do produto 10080047"},
        {
            "role": "assistant",
            "content": "ok",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/summary",
                        },
                    }
                ]
            },
        },
    ]

    code = ChatProductQueryIntentService.resolve_product_code(
        "ultimas compras",
        previous_messages=history,
    )

    assert code == "10080047"


def test_resolve_product_intent_inherits_stock_from_history():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080047/stock"},
                    }
                ]
            },
        },
    ]

    assert (
        ChatProductQueryIntentService.resolve_product_intent(
            "e do 10080055?",
            previous_messages=history,
        )
        == ChatProductQueryIntent.STOCK
    )


def test_resolve_product_intent_keeps_purchases_over_inherited_summary():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080047/summary"},
                    }
                ]
            },
        },
    ]

    assert (
        ChatProductQueryIntentService.resolve_product_intent(
            "ultimas compras",
            previous_messages=history,
        )
        == ChatProductQueryIntent.FULL
    )


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


def test_extract_product_code_ignores_group_number():
    assert (
        ChatProductQueryIntentService.extract_product_code(
            "busque 3 produtos do grupo 1008"
        )
        is None
    )
    assert ChatProductQueryIntentService.extract_product_code("produto 10081387") == "10081387"


def test_format_direct_answer_stock_uses_brief_summary():
    answer = ChatProductQueryIntentService.format_direct_answer(
        {
            "titulo": "Estoque 10080047",
            "linhas": [
                "Consultei o estoque do produto **10080047**: **2** posição(ões).",
                "Roteiro: 0 registro(s).",
            ],
        },
        intent=ChatProductQueryIntent.STOCK,
        path="/products/10080047/stock",
    )

    assert answer is not None
    assert "**Estoque 10080047**" in answer
    assert "Consultei o estoque" in answer
    assert "- Filial 01" not in answer
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


def test_format_direct_answer_structure_uses_hierarchical_markdown():
    answer = ChatProductQueryIntentService.format_direct_answer(
        {
            "titulo": "Estrutura do produto 90260077",
            "linhas": [],
            "dados": {
                "root": {
                    "code": "90260077",
                    "description": "CHICOTE DE LIGACAO",
                    "type": "PA",
                    "unit": "MI",
                    "quantity": 1,
                },
                "items": [
                    {
                        "code": "50230002",
                        "description": "CB14AMAR-00180/25/07-0000-0914",
                        "type": "PI",
                        "unit": "MI",
                        "quantity": 1,
                        "components": [
                            {
                                "code": "10030048",
                                "description": "CABO EPR 14AWG",
                                "type": "MP",
                                "unit": "MT",
                                "quantity": 180,
                            },
                        ],
                    },
                ],
            },
            "sourcePath": "/products/90260077/structure",
        },
        intent=ChatProductQueryIntent.STRUCTURE,
    )

    assert answer is not None
    assert "**Produto pai**" in answer
    assert "**Componentes nível 1**" in answer
    assert "**Estrutura detalhada**" in answer
    assert "90260077" in answer
    assert "50230002" in answer
    assert "10030048" in answer


def test_extract_product_code_ignores_calendar_year_in_temporal_phrase():
    assert (
        ChatProductQueryIntentService.extract_product_code("Vendas por mês em 2026")
        is None
    )
    assert (
        ChatProductQueryIntentService.extract_product_code(
            "Participação do faturamento por cliente em rosca"
        )
        is None
    )


def test_resolve_product_code_does_not_inherit_for_aggregate_sales_query():
    history = [
        {
            "role": "assistant",
            "content": "Produto 2026",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/2026/sales"},
                    }
                ]
            },
        },
    ]

    code = ChatProductQueryIntentService.resolve_product_code(
        "Vendas por mês em 2026",
        previous_messages=history,
    )

    assert code is None


def test_should_inherit_product_code_false_for_stock_list_query():
    assert not ChatProductQueryIntentService.should_inherit_product_code(
        "Liste os produtos com estoque abaixo do mínimo"
    )
