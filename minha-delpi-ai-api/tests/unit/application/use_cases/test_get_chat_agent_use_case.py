from uuid import uuid4
from datetime import datetime, timezone
from unittest.mock import MagicMock

from app.application.use_cases.chat_agents_use_cases import GetChatAgentUseCase
from app.domain.entities.chat_agent import ChatAgent


def _agent() -> ChatAgent:
    now = datetime.now(timezone.utc)
    return ChatAgent(
        id=uuid4(),
        key="test-agent",
        name="Test",
        description="desc",
        system_prompt="secret prompt",
        enabled=True,
        metadata={},
        owner_user_id=uuid4(),
        visibility="private",
        category=None,
        icon=None,
        response_style=None,
        max_tool_calls=5,
        requires_confirmation_for_write=False,
        created_at=now,
        updated_at=now,
    )


def test_get_agent_includes_system_prompt_for_editor():
    agent = _agent()
    repository = MagicMock()
    repository.get_accessible_by_id.return_value = (agent, "editor")

    result = GetChatAgentUseCase(repository).execute(str(uuid4()), str(agent.id))

    assert result is not None
    assert result.system_prompt == "secret prompt"
    assert result.access_role == "editor"


def test_get_agent_hides_system_prompt_for_viewer():
    agent = _agent()
    repository = MagicMock()
    repository.get_accessible_by_id.return_value = (agent, "viewer")

    result = GetChatAgentUseCase(repository).execute(str(uuid4()), str(agent.id))

    assert result is not None
    assert result.system_prompt is None
