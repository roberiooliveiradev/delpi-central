from app.domain.services.chat_sql_intent_service import ChatSqlIntentService


def test_monte_query_is_authoring():
    assert ChatSqlIntentService.is_authoring_request(
        "monte uma query que liste os produtos que vão ser produzidos hoje"
    )


def test_monte_query_does_not_auto_execute():
    assert ChatSqlIntentService.should_auto_execute_sql(
        "monte uma query que liste os produtos que vão ser produzidos hoje"
    ) is False


def test_mostre_a_query_does_not_auto_execute():
    assert ChatSqlIntentService.should_auto_execute_sql("mostre a query") is False


def test_ajuste_query_does_not_auto_execute():
    assert ChatSqlIntentService.should_auto_execute_sql(
        "ajuste a query para filtrar só filial 01"
    ) is False


def test_execute_explicitly():
    assert ChatSqlIntentService.should_auto_execute_sql(
        "execute essa consulta no banco"
    ) is True


def test_rode_sql():
    assert ChatSqlIntentService.should_auto_execute_sql("rode o sql abaixo") is True


def test_embedded_select_executes():
    assert ChatSqlIntentService.should_auto_execute_sql(
        "SELECT * FROM SC2010 WHERE C2_FILIAL = '01'"
    ) is True
