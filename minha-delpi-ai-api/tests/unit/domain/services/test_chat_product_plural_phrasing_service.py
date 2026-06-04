from app.domain.services.chat_product_plural_phrasing_service import (
    ChatProductPluralPhrasingService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)


def test_scope_labels_from_mixed_api_paths():
    stock_labels = ChatProductPluralPhrasingService.scope_labels_from_api_path(
        "/products/90260149/stock"
    )
    parents_labels = ChatProductPluralPhrasingService.scope_labels_from_api_path(
        "/products/90260149/parents"
    )

    joined = ChatProductPluralPhrasingService.join_scope_labels_pt(
        stock_labels + parents_labels
    )

    assert stock_labels == ["estoque"]
    assert parents_labels == ["onde o item é usado"]
    assert joined == "estoque e onde o item é usado"


def test_detect_stock_intent_for_plural_products_phrase():
    assert (
        ChatProductQueryIntentService.detect(
            "estoque dos produtos 10080022, 10080012"
        )
        == ChatProductQueryIntent.STOCK
    )


def test_detect_structure_intent_for_plural_products_phrase():
    assert (
        ChatProductQueryIntentService.detect(
            "estruturas dos produtos 90260077 e 90260088"
        )
        == ChatProductQueryIntent.STRUCTURE
    )


def test_detect_sales_intent_for_plural_products_phrase():
    assert (
        ChatProductQueryIntentService.detect(
            "vendas dos produtos 10080001 e 10080002"
        )
        == ChatProductQueryIntent.SALES
    )


def test_refine_full_to_stock_for_plural_linked_phrase():
    assert (
        ChatProductQueryIntentService.refine_operational_intent_from_full(
            "saldo dos itens 10080047 e 10080055"
        )
        == ChatProductQueryIntent.STOCK
    )


def test_refine_full_to_guide_for_single_scope_plural():
    assert (
        ChatProductQueryIntentService.refine_operational_intent_from_full(
            "roteiros dos produtos 10080047 e 10080055"
        )
        == ChatProductQueryIntent.FULL
    )
