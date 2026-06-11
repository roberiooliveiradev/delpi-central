from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService


def test_detects_comparison_with_structures_keyword():
    assert ChatAnalysisIntentService.is_comparison_or_insight_request(
        "compare as duas estruturas e traga insights"
    )


def test_detects_insight_request():
    assert ChatAnalysisIntentService.is_comparison_or_insight_request(
        "quais as diferenças entre os produtos?"
    )


def test_does_not_flag_plain_structure_query():
    assert not ChatAnalysisIntentService.is_comparison_or_insight_request(
        "estrutura do produto 90260088"
    )


def test_does_not_flag_full_analyser_fetch_as_comparison():
    assert not ChatAnalysisIntentService.is_comparison_or_insight_request(
        "traga a analise completa dos produtos 10080047 e 10080055"
    )


def test_detects_data_interpretation_follow_up():
    history = [
        {
            "role": "assistant",
            "content": "Roteiro do produto",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/90260142/guide",
                        },
                    }
                ]
            },
        }
    ]

    assert ChatAnalysisIntentService.is_data_interpretation_request(
        "explique os dados acima",
        history,
    )
    assert ChatAnalysisIntentService.is_data_interpretation_request(
        "o que isso quer dizer",
        history,
    )
    assert ChatAnalysisIntentService.is_data_interpretation_request(
        "resume",
        history,
    )
    assert ChatAnalysisIntentService.is_data_interpretation_request(
        "traduz isso",
        history,
    )
    assert ChatAnalysisIntentService.is_data_interpretation_request(
        "nao entendi",
        history,
    )


def test_detects_sql_result_interpretation_follow_up():
    history = [
        {
            "role": "assistant",
            "content": "Consulta SQL",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/data/sql",
                            "humanizedSummary": {
                                "titulo": "Consulta SQL",
                                "linhas": ["A consulta retornou 25 registro(s)."],
                            },
                        },
                    }
                ]
            },
        }
    ]

    assert ChatAnalysisIntentService.is_data_interpretation_request(
        "interprete o resultado da última consulta SQL",
        history,
    )


def test_detects_generic_row_drilldown_as_interpretation():
    history = [
        {
            "role": "assistant",
            "content": "Consulta SQL",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/data/sql"},
                    }
                ]
            },
        }
    ]

    assert ChatAnalysisIntentService.is_data_interpretation_request(
        "detalhe este registro do último resultado — A1 cod: 000224, "
        "A1 nome: ACRILMASTER INDUSTRIA DE ACRILICOS LTDA",
        history,
    )


def test_does_not_flag_data_interpretation_without_tool_history():
    assert not ChatAnalysisIntentService.is_data_interpretation_request(
        "explique os dados acima",
        [],
    )


def test_does_not_flag_format_refinement_as_data_interpretation():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/10080001/stock"},
                    }
                ]
            },
        }
    ]

    assert not ChatAnalysisIntentService.is_data_interpretation_request(
        "mostre o último resultado em tabela",
        history,
    )


def test_detects_data_reference_without_tool_history():
    assert ChatAnalysisIntentService.is_data_reference_without_tool_data(
        "explique os dados acima",
        [],
    )
    assert ChatAnalysisIntentService.is_data_reference_without_tool_data(
        "resume",
        [],
    )


def test_does_not_flag_data_reference_without_tool_when_history_exists():
    history = [
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/products/90260142/guide"},
                    }
                ]
            },
        }
    ]

    assert not ChatAnalysisIntentService.is_data_reference_without_tool_data(
        "explique os dados acima",
        history,
    )


def test_extract_all_product_codes_preserves_order():
    codes = ChatAnalysisIntentService.extract_all_product_codes(
        "user: estrutura 90260077",
        "user: estrutura 90260088",
    )

    assert codes == ["90260077", "90260088"]


def test_extract_product_code_from_structure_path():
    code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
        "/products/90260077/structure"
    )

    assert code == "90260077"


def test_extract_product_code_from_stock_path():
    code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
        "/products/10080047/stock"
    )

    assert code == "10080047"


def test_extract_product_code_from_tool_path_ignores_search_collection():
    assert (
        ChatAnalysisIntentService.extract_product_code_from_tool_path("/products/search")
        is None
    )
    assert (
        ChatAnalysisIntentService.extract_product_code_from_tool_path(
            "/products/search/description"
        )
        is None
    )


def test_extract_product_code_ignores_unresolved_path_template():
    code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
        "/products/{code}/stock"
    )

    assert code is None


def test_extract_product_path_segment():
    assert (
        ChatAnalysisIntentService.extract_product_path_segment(
            "/products/10080047/purchases"
        )
        == "purchases"
    )
