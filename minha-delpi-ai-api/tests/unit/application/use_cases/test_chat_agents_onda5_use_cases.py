from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.chat_agents_use_cases import (
    ChatAgentPermissionDeniedError,
    DuplicateChatAgentUseCase,
    GetChatAgentStatsUseCase,
)
from app.domain.entities.chat_agent import ChatAgent


def _agent() -> ChatAgent:
    now = datetime.now(timezone.utc)
    return ChatAgent(
        id=uuid4(),
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


def test_duplicate_agent_passes_copy_actions_flag():
    agent = _agent()
    repository = MagicMock()
    repository.get_accessible_by_id.return_value = (agent, "owner")
    repository.duplicate.return_value = agent

    DuplicateChatAgentUseCase(repository).execute(
        user_id=str(uuid4()),
        agent_id=str(agent.id),
        copy_actions=False,
    )

    repository.duplicate.assert_called_once()
    assert repository.duplicate.call_args.kwargs["copy_actions"] is False


def test_get_agent_stats_requires_editor_role():
    agent_id = uuid4()
    user_id = uuid4()
    repository = MagicMock()
    repository.get_accessible_by_id.return_value = (_agent(), "viewer")

    with pytest.raises(ChatAgentPermissionDeniedError):
        GetChatAgentStatsUseCase(repository).execute(
            user_id=str(user_id),
            agent_id=str(agent_id),
        )

    repository.get_usage_stats.assert_not_called()


def test_get_agent_stats_delegates_to_repository():
    agent_id = uuid4()
    user_id = uuid4()
    repository = MagicMock()
    repository.get_accessible_by_id.return_value = (_agent(), "owner")
    repository.get_usage_stats.return_value = {
        "agentId": "11111111-1111-4111-8111-111111111111",
        "windowHours": 168,
        "sessionsInWindow": 2,
        "messagesInWindow": 10,
        "totalSessions": 5,
        "actionProvidersCount": 1,
        "sharesCount": 0,
        "userRanking": [],
    }

    result = GetChatAgentStatsUseCase(repository).execute(
        user_id=str(user_id),
        agent_id=str(agent_id),
        hours=24,
    )

    repository.get_usage_stats.assert_called_once()
    assert repository.get_usage_stats.call_args.kwargs["hours"] == 24
    assert result["sessionsInWindow"] == 2
    assert result["miniDashboard"]["type"] == "dashboard"
    assert len(result["recommendations"]) >= 1
