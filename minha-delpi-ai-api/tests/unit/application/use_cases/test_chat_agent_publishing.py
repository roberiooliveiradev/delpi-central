from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.services.chat_agent_config_snapshot_service import (
    has_unpublished_changes,
    normalize_draft_payload,
)
from app.application.use_cases.chat_agents_use_cases import (
    PreviewChatAgentUseCase,
    PublishChatAgentUseCase,
)
from app.domain.entities.chat_agent import ChatAgent


def _agent(**overrides):
    base = {
        "id": uuid4(),
        "key": "demo",
        "name": "Demo",
        "description": "desc",
        "system_prompt": "prompt",
        "enabled": True,
        "metadata": {"icebreakers": ["Oi"]},
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "owner_user_id": uuid4(),
        "visibility": "private",
        "category": None,
        "icon": None,
        "response_style": "objetivo",
        "max_tool_calls": 5,
        "requires_confirmation_for_write": True,
        "published_version": 1,
        "published_at": datetime.now(timezone.utc),
        "published_config": {
            "name": "Demo",
            "description": "desc",
            "systemPrompt": "prompt",
            "metadata": {"icebreakers": ["Oi"]},
        },
    }
    base.update(overrides)
    return ChatAgent(**base)


def test_has_unpublished_changes_detects_draft_diff():
    agent = _agent(name="Demo alterado")

    assert has_unpublished_changes(agent) is True


def test_normalize_draft_payload_maps_fields():
    draft = normalize_draft_payload(
        {
            "name": "Novo",
            "systemPrompt": "instruções",
            "metadata": {"capabilities": {"actions": True}},
            "maxToolCalls": 8,
        }
    )

    assert draft is not None
    assert draft["name"] == "Novo"
    assert draft["systemPrompt"] == "instruções"
    assert draft["maxToolCalls"] == 8


def test_preview_agent_uses_draft_overlay():
    repository = MagicMock()
    simulate = MagicMock()
    simulate.execute.return_value = {"answerPreview": "ok"}

    agent = _agent()
    user_id = str(uuid4())
    agent_id = str(agent.id)

    repository.get_for_preview.return_value = agent
    repository.get_accessible_by_id.return_value = (agent, "owner")

    use_case = PreviewChatAgentUseCase(repository, simulate)
    result = use_case.execute(
        user_id=user_id,
        agent_id=agent_id,
        message="Olá",
        access_token="token",
        draft={"name": "Demo", "systemPrompt": "novo prompt"},
    )

    assert result["answerPreview"] == "ok"
    simulate.execute.assert_called_once()
    kwargs = simulate.execute.call_args.kwargs
    assert kwargs["agent_prompt_override"] == "novo prompt"
    assert kwargs["skip_enabled_check"] is True


def test_publish_agent_increments_version():
    repository = MagicMock()
    agent = _agent(published_version=2)
    user_id = str(uuid4())
    agent_id = str(agent.id)

    published = _agent(published_version=3)
    repository.publish.return_value = published
    repository.get_accessible_by_id.return_value = (published, "owner")

    use_case = PublishChatAgentUseCase(repository)
    result = use_case.execute(user_id=user_id, agent_id=agent_id)

    assert result is not None
    assert result.published_version == 3
    repository.publish.assert_called_once()
