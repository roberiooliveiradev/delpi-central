from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.dto.create_chat_session_request import CreateChatSessionRequest
from app.application.use_cases.create_chat_session_use_case import CreateChatSessionUseCase
from app.application.use_cases.get_chat_history_use_case import GetChatHistoryUseCase
from app.application.use_cases.list_chat_sessions_use_case import ListChatSessionsUseCase
from app.domain.entities.chat_session import ChatSession
from app.domain.exceptions.chat_exceptions import ChatSessionAccessDeniedError


class FakeChatSessionRepository:
    def __init__(self):
        self.sessions = []
        self.messages = []

    def create_session(
        self,
        user_id,
        title,
        context,
        project_id=None,
        agent_id=None,
    ):
        session = ChatSession(
            id=uuid4(),
            user_id=user_id,
            title=title,
            context=context,
            project_id=project_id,
            agent_id=agent_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.sessions.append(session)
        return session

    def list_sessions_by_user(self, user_id, archived=False):
        return [session for session in self.sessions if session.user_id == user_id]

    def get_session_by_id(self, session_id):
        for session in self.sessions:
            if session.id == session_id:
                return session
        return None

    def list_messages_by_session(self, session_id):
        return self.list_all_messages_by_session(session_id)

    def list_all_messages_by_session(self, session_id):
        return [message for message in self.messages if message.session_id == session_id]

    def get_message_by_id(self, message_id, *, user_id=None):
        for message in self.messages:
            if message.id == message_id:
                if user_id is None:
                    return message
                session = self.get_session_by_id(message.session_id)
                if session and session.user_id == user_id:
                    return message
        return None

    def set_active_leaf_message_id(self, *, session_id, user_id, message_id):
        session = self.get_session_by_id(session_id)
        if not session or session.user_id != user_id:
            return None
        object.__setattr__(session, "active_leaf_message_id", message_id)
        return session

    def create_message(
        self,
        session_id,
        role,
        content,
        metadata=None,
        parent_message_id=None,
    ):
        from app.domain.entities.chat_message import ChatMessage

        message = ChatMessage(
            id=uuid4(),
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata,
            created_at=datetime.now(timezone.utc),
            parent_message_id=parent_message_id,
        )
        self.messages.append(message)
        return message

    def update_user_message(self, *args, **kwargs):
        return None

    def delete_messages_after(self, *args, **kwargs):
        return 0

    def get_user_message_for_user(self, *args, **kwargs):
        return None

    def patch_message_metadata(self, *args, **kwargs):
        return None

    def update_assistant_message(self, *args, **kwargs):
        return None

    def delete_session(self, *args, **kwargs):
        return False

    def rename_session(self, *args, **kwargs):
        return None

    def update_session_agent_id(self, *args, **kwargs):
        return False

    def set_session_pinned(self, *args, **kwargs):
        return None

    def set_session_archived(self, *args, **kwargs):
        return None


def test_create_chat_session_use_case():
    repository = FakeChatSessionRepository()
    user_id = str(uuid4())

    use_case = CreateChatSessionUseCase(repository)

    result = use_case.execute(
        CreateChatSessionRequest(
            user_id=user_id,
            title=" Minha sessão ",
            context=" geral ",
        )
    )

    assert result.id
    assert result.title == "Minha sessão"
    assert result.context == "geral"


def test_list_chat_sessions_filters_by_user():
    repository = FakeChatSessionRepository()
    user_id = str(uuid4())
    other_user_id = str(uuid4())

    create_use_case = CreateChatSessionUseCase(repository)
    list_use_case = ListChatSessionsUseCase(repository)

    create_use_case.execute(CreateChatSessionRequest(user_id=user_id, title="A", context=None))
    create_use_case.execute(CreateChatSessionRequest(user_id=other_user_id, title="B", context=None))

    result = list_use_case.execute(user_id)

    assert len(result) == 1
    assert result[0].title == "A"


def test_get_chat_history_blocks_other_user_session():
    repository = FakeChatSessionRepository()
    owner_id = str(uuid4())
    attacker_id = str(uuid4())

    create_use_case = CreateChatSessionUseCase(repository)
    history_use_case = GetChatHistoryUseCase(repository)

    session = create_use_case.execute(
        CreateChatSessionRequest(user_id=owner_id, title="Privada", context=None)
    )

    with pytest.raises(ChatSessionAccessDeniedError):
        history_use_case.execute(user_id=attacker_id, session_id=session.id)
