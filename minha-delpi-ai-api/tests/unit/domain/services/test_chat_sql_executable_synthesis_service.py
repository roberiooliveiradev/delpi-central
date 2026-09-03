from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_sql_executable_synthesis_service import (
    ChatSqlExecutableSynthesisService,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_synthesize_select_oneshot_sb1010_group():
    sql = ChatSqlExecutableSynthesisService.synthesize_select(
        "executa no banco select top 10 produtos grupo 1008 SB1010",
        invent_default_table=False,
    )

    assert sql is not None
    assert "FROM SB1010" in sql.upper()
    assert "1008" in sql
    assert "TOP 10" in sql.upper()


def test_synthesize_select_without_table_returns_none_for_execute():
    sql = ChatSqlExecutableSynthesisService.synthesize_select(
        "executa no banco select top 10 de itens aleatorios sem dominio",
        invent_default_table=False,
    )

    assert sql is None


def test_synthesize_select_authoring_may_invent_default_table():
    sql = ChatSqlExecutableSynthesisService.synthesize_select(
        "crie um sql dos clientes",
        invent_default_table=True,
    )

    assert sql is not None
    assert "FROM" in sql.upper()
