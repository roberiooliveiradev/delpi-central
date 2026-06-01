from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)


def test_missing_product_code_skipped_for_aggregate_stock_sql():
    answer = ChatOperationalParameterService.resolve_missing_product_code_answer(
        "Liste os produtos com estoque abaixo do mínimo",
    )

    assert answer is None


def test_missing_product_code_still_asks_for_single_stock():
    answer = ChatOperationalParameterService.resolve_missing_product_code_answer(
        "estoque do produto",
    )

    assert answer is not None
