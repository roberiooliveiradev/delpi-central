from app.domain.services.chat_sql_inventory_query_service import (
    ChatSqlInventoryQueryService,
)
from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)


def test_requires_sql_for_below_minimum_stock_list():
    message = "Liste os produtos com estoque abaixo do mínimo"

    assert ChatSqlOperationalIntentService.requires_sql_knowledge(message)
    resolution = ChatSqlInventoryQueryService.resolve(message)

    assert resolution is not None
    assert resolution.mode == "execute"
    assert "SB2010" in resolution.sql
    assert "B1_EMIN" in resolution.sql
    assert "SC2010" not in resolution.sql


def test_does_not_resolve_single_product_stock():
    assert ChatSqlInventoryQueryService.resolve("estoque do produto 10080001") is None
