from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.chat_agents_use_cases import (
    DuplicateChatAgentUseCase,
    ListChatAgentsUseCase,
    TransferChatAgentOwnershipUseCase,
)
from app.domain.entities.chat_agent import ChatAgent
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError


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


def test_list_agents_can_include_usage_summaries():
    agent = _agent()
    repository = MagicMock()
    repository.list_accessible.return_value = [(agent, "owner")]
    repository.list_usage_summaries.return_value = {
        agent.key: {
            "sessionsInWindow": 4,
            "totalSessions": 10,
        }
    }

    result = ListChatAgentsUseCase(repository).execute(
        str(uuid4()),
        include_stats=True,
    )

    repository.list_usage_summaries.assert_called_once()
    assert result[0].sessions_in_window == 4
    assert result[0].total_sessions == 10


def test_transfer_ownership_validates_new_owner():
    repository = MagicMock()

    with pytest.raises(InvalidChatSessionInputError):
        TransferChatAgentOwnershipUseCase(repository).execute(
            user_id=str(uuid4()),
            agent_id=str(uuid4()),
            new_owner_user_id="",
        )

    repository.transfer_ownership.assert_not_called()


def test_duplicate_agent_can_copy_sources():
    agent = _agent()
    repository = MagicMock()
    repository.get_accessible_by_id.return_value = (agent, "owner")
    repository.duplicate.return_value = agent
    source_copy_service = MagicMock()

    DuplicateChatAgentUseCase(repository, source_copy_service).execute(
        user_id=str(uuid4()),
        agent_id=str(agent.id),
        copy_sources=True,
    )

    source_copy_service.copy_agent_sources.assert_called_once()
