from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.application.use_cases.chat_agents_use_cases import (
    AGENT_EXPORT_VERSION,
    ExportChatAgentUseCase,
    ImportChatAgentUseCase,
)
from app.domain.entities.chat_agent import ChatAgent
from app.domain.exceptions.chat_exceptions import InvalidChatSessionInputError


def _agent() -> ChatAgent:
    now = datetime.now(timezone.utc)
    return ChatAgent(
        id=uuid4(),
        key="rh-agent",
        name="RH",
        description="desc",
        system_prompt="prompt",
        enabled=True,
        metadata={"icebreakers": ["Olá"]},
        owner_user_id=uuid4(),
        visibility="private",
        category="rh",
        icon="bot",
        response_style="objetivo",
        max_tool_calls=5,
        requires_confirmation_for_write=True,
        created_at=now,
        updated_at=now,
    )


def test_export_agent_builds_portable_bundle():
    agent = _agent()
    repository = MagicMock()
    repository.get_accessible_by_id.return_value = (agent, "owner")
    repository.list_action_providers.return_value = [
        {
            "providerKey": "core",
            "enabled": True,
            "allowRead": True,
            "allowWrite": False,
            "allowAdmin": False,
            "requiresConfirmationForWrite": True,
        }
    ]
    repository.list_actions.return_value = [
        {
            "providerKey": "core",
            "actionId": "list-users",
            "enabled": True,
            "sensitivity": "read",
            "requiresConfirmation": False,
        }
    ]

    result = ExportChatAgentUseCase(repository).execute(
        user_id=str(uuid4()),
        agent_id=str(agent.id),
    )

    assert result is not None
    assert result["exportVersion"] == AGENT_EXPORT_VERSION
    assert result["agent"]["name"] == "RH"
    assert result["actionProviders"][0]["providerKey"] == "core"
    assert result["actions"][0]["actionId"] == "list-users"


def test_import_agent_rejects_unsupported_version():
    repository = MagicMock()

    with pytest.raises(InvalidChatSessionInputError):
        ImportChatAgentUseCase(repository).execute(
            user_id=str(uuid4()),
            payload={"exportVersion": 99, "agent": {"name": "X"}},
        )


def test_import_agent_creates_agent_and_applies_actions():
    agent = _agent()
    repository = MagicMock()
    repository.create.return_value = agent

    payload = {
        "exportVersion": AGENT_EXPORT_VERSION,
        "suggestedKey": "rh-agent",
        "agent": {
            "name": "RH importado",
            "description": "desc",
            "systemPrompt": "prompt",
            "metadata": {},
        },
        "actionProviders": [
            {
                "providerKey": "core",
                "enabled": True,
                "allowRead": True,
                "allowWrite": False,
                "allowAdmin": False,
                "requiresConfirmationForWrite": True,
            }
        ],
        "actions": [],
    }

    result = ImportChatAgentUseCase(repository).execute(
        user_id=str(uuid4()),
        payload={"export": payload, "applyActions": True},
    )

    repository.create.assert_called_once()
    repository.apply_exported_action_configuration.assert_called_once()
    assert result.name == "RH"
