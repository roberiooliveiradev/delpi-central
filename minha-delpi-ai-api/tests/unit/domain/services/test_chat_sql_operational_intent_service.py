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
