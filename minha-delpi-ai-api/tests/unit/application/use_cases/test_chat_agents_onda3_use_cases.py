from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.chat_agents_use_cases import DuplicateChatAgentUseCase
from app.application.use_cases.search_chat_directory_users_use_case import (
    SearchChatDirectoryUsersUseCase,
)
from app.domain.entities.chat_agent import ChatAgent
from app.domain.exceptions.authorization_exceptions import CoreApiUnavailableError
from datetime import datetime, timezone


def _agent() -> ChatAgent:
    now = datetime.now(timezone.utc)
    return ChatAgent(
        id=uuid4(),
        key="origem",
        name="Agente origem",
        description="desc",
        system_prompt="prompt",
        enabled=True,
        metadata={},
        owner_user_id=uuid4(),
        visibility="private",
        category=None,
        icon=None,
        response_style=None,
        max_tool_calls=3,
        requires_confirmation_for_write=False,
        created_at=now,
        updated_at=now,
    )


def test_duplicate_agent_returns_owner_response():
    agent = _agent()
    repository = MagicMock()
    repository.duplicate.return_value = agent

    result = DuplicateChatAgentUseCase(repository).execute(
        user_id=str(uuid4()),
        agent_id=str(agent.id),
    )

    repository.duplicate.assert_called_once()
    assert repository.duplicate.call_args.kwargs["copy_actions"] is True
    assert result is not None
    assert result.access_role == "owner"
    assert result.system_prompt == "prompt"


def test_search_directory_users_returns_empty_for_short_query():
    gateway = MagicMock()

    result = SearchChatDirectoryUsersUseCase(gateway).execute(
        access_token="token",
        query="a",
    )

    assert result == []
    gateway.search_directory_users.assert_not_called()


def test_search_directory_users_degrades_when_core_unavailable():
    gateway = MagicMock()
    gateway.search_directory_users.side_effect = CoreApiUnavailableError("down")

    result = SearchChatDirectoryUsersUseCase(gateway).execute(
        access_token="token",
        query="maria",
    )

    assert result == []
