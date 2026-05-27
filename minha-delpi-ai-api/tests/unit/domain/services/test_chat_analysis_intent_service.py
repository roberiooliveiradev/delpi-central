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
