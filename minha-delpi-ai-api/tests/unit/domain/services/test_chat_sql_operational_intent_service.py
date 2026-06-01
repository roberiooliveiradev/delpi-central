from app.domain.services.chat_sql_operational_intent_service import (
    ChatSqlOperationalIntentService,
)


def test_detects_production_schedule_question():
    assert ChatSqlOperationalIntentService.requires_sql_knowledge(
        "quais produtos serão produzidos hoje?"
    )


def test_detects_programacao_de_producao():
    assert ChatSqlOperationalIntentService.requires_sql_knowledge(
        "me traga a programação de produção de hoje"
    )


def test_does_not_flag_catalog_product_search():
    assert not ChatSqlOperationalIntentService.requires_sql_knowledge(
        "busque produto parafuso m8 no cadastro"
    )


def test_does_not_flag_plain_stock_question():
    assert not ChatSqlOperationalIntentService.requires_sql_knowledge(
        "estoque do produto 10080047"
    )


def test_detects_production_question_for_monday():
    assert ChatSqlOperationalIntentService.requires_sql_knowledge(
        "quais produtos serão produzidos na segunda-feira?"
    )


def test_detects_production_question_for_tomorrow():
    assert ChatSqlOperationalIntentService.requires_sql_knowledge(
        "o que vai ser produzido amanhã?"
    )


def test_detects_scheduled_production_tomorrow_phrase():
    assert ChatSqlOperationalIntentService.requires_sql_knowledge(
        "Produtos programados para produção amanhã"
    )


def test_detects_ruptura_stock_below_minimum():
    assert ChatSqlOperationalIntentService.requires_sql_knowledge(
        "Ruptura de estoque — quais produtos estão abaixo do mínimo?"
    )


def test_detects_aggregate_stock_below_minimum():
    assert ChatSqlOperationalIntentService.requires_sql_knowledge(
        "Liste os produtos com estoque abaixo do mínimo"
    )


def test_detects_aggregate_sales_by_month():
    assert ChatSqlOperationalIntentService.requires_sql_knowledge(
        "Vendas por mês em 2025"
    )


def test_does_not_flag_single_product_stock_without_code():
    assert not ChatSqlOperationalIntentService.requires_sql_knowledge(
        "estoque do produto"
    )
