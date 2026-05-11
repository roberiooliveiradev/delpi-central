from app.application.use_cases.create_chat_session_use_case import CreateChatSessionUseCase
from app.application.use_cases.get_chat_history_use_case import GetChatHistoryUseCase
from app.application.use_cases.list_chat_sessions_use_case import ListChatSessionsUseCase
from app.infrastructure.persistence.postgres_chat_session_repository import (
    PostgresChatSessionRepository,
)


def make_create_chat_session_use_case() -> CreateChatSessionUseCase:
    return CreateChatSessionUseCase(PostgresChatSessionRepository())


def make_list_chat_sessions_use_case() -> ListChatSessionsUseCase:
    return ListChatSessionsUseCase(PostgresChatSessionRepository())


def make_get_chat_history_use_case() -> GetChatHistoryUseCase:
    return GetChatHistoryUseCase(PostgresChatSessionRepository())
