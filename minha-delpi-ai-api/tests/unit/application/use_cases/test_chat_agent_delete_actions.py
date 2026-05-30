from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.chat_agents_use_cases import (
    DeleteChatAgentActionProviderUseCase,
    DeleteChatAgentActionUseCase,
)


def test_delete_action_provider_delegates_to_repository():
    agent_id = uuid4()
    user_id = uuid4()
    repository = MagicMock()
    repository.delete_action_provider.return_value = True

    result = DeleteChatAgentActionProviderUseCase(repository).execute(
        user_id=str(user_id),
        agent_id=str(agent_id),
        provider_key="api-delpi",
        can_manage_official_agents=True,
    )

    repository.delete_action_provider.assert_called_once()
    call = repository.delete_action_provider.call_args.kwargs
    assert call["agent_id"] == agent_id
    assert call["user_id"] == user_id
    assert call["provider_key"] == "api-delpi"
    assert call["can_manage_official_agents"] is True
    assert result is True


def test_delete_action_delegates_to_repository():
    agent_id = uuid4()
    user_id = uuid4()
    repository = MagicMock()
    repository.delete_action.return_value = True

    result = DeleteChatAgentActionUseCase(repository).execute(
        user_id=str(user_id),
        agent_id=str(agent_id),
        provider_key="api-delpi",
        action_id="api_delpi.data.execute_readonly_sql",
        can_manage_official_agents=False,
    )

    repository.delete_action.assert_called_once()
    call = repository.delete_action.call_args.kwargs
    assert call["agent_id"] == agent_id
    assert call["user_id"] == user_id
    assert call["provider_key"] == "api-delpi"
    assert call["action_id"] == "api_delpi.data.execute_readonly_sql"
    assert call["can_manage_official_agents"] is False
    assert result is True
