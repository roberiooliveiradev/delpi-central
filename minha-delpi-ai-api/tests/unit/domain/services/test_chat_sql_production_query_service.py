from app.domain.services.chat_sql_production_query_service import (
    ChatSqlProductionQueryService,
)


def test_resolve_execute_for_production_today():
    resolution = ChatSqlProductionQueryService.resolve(
        "quais produtos serão produzidos hoje?"
    )

    assert resolution is not None
    assert resolution.mode == "execute"
    assert "SC2010" in resolution.sql
    assert "D4_OPERAC" in resolution.sql
    assert "CAST(GETDATE()" in resolution.sql


def test_resolve_authoring_for_monte_query():
    resolution = ChatSqlProductionQueryService.resolve(
        "monte uma query que liste os produtos que vão ser produzidos hoje"
    )

    assert resolution is not None
    assert resolution.mode == "authoring"
    assert "SELECT" in resolution.sql


def test_can_fast_path_with_sql_action():
    assert ChatSqlProductionQueryService.can_fast_path(
        "quais produtos serão produzidos hoje?",
        ["api_delpi.data.execute_readonly_sql"],
    )


def test_can_fast_path_authoring_without_sql_action():
    assert ChatSqlProductionQueryService.can_fast_path(
        "monte uma query que liste os produtos que vão ser produzidos hoje",
        ["api_delpi.products.search_products"],
    )


def test_resolve_execute_for_production_monday():
    resolution = ChatSqlProductionQueryService.resolve(
        "quais produtos serão produzidos na segunda-feira?"
    )

    assert resolution is not None
    assert resolution.mode == "execute"
    assert "DECLARE @DATA DATE =" in resolution.sql
    assert "CAST(GETDATE()" not in resolution.sql
    assert "segunda-feira" in resolution.title.lower()


def test_resolve_execute_for_production_tomorrow():
    resolution = ChatSqlProductionQueryService.resolve(
        "o que vai ser produzido amanhã?"
    )

    assert resolution is not None
    assert resolution.mode == "execute"
    assert "amanhã" in resolution.title
    assert "CAST(GETDATE()" not in resolution.sql
