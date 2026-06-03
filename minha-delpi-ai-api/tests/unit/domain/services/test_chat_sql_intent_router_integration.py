"""SQL authoring vs text_task e sub-intent do roteador."""

from app.domain.services.chat_intent_router_service import ChatIntentRouterService
from app.domain.services.chat_sql_intent_service import ChatSqlIntentService


_USER_MESSAGE = (
    "Monte uma consulta para listar clientes ativos da tabela SA1, "
    "só código e nome, sem executar."
)


def test_sql_authoring_not_pure_text_task():
    assert ChatSqlIntentService.is_authoring_request(_USER_MESSAGE) is True
    assert ChatSqlIntentService.should_auto_execute_sql(_USER_MESSAGE) is False


def test_sql_sub_intent_generate_not_execute_when_sem_executar():
    assert ChatSqlIntentService.router_sub_intent(_USER_MESSAGE) == "sql_generate"


def test_intent_router_classifies_sql_task():
    route = ChatIntentRouterService.classify(_USER_MESSAGE)

    assert route.intent == "sql_task"
    assert route.sub_intent == "sql_generate"
    assert route.requires_tool is False
