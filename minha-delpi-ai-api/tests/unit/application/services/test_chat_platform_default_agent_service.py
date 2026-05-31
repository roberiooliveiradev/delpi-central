from datetime import datetime, timezone
from uuid import uuid4

from app.application.services.chat_platform_default_agent_service import (
    ChatPlatformDefaultAgentService,
)
from app.domain.entities.chat_agent import ChatAgent
from app.infrastructure.config import settings as settings_module


class FakeSystemAgentRepository:
    def __init__(self, agent: ChatAgent | None):
        self.agent = agent

    def get_enabled_by_id(self, agent_id, user_id=None):
        if self.agent and agent_id == self.agent.id:
            return self.agent
        return None

    def get_enabled_system_by_name(self, name, user_id=None):
        if self.agent and self.agent.name == name:
            return self.agent
        return None


def test_resolves_platform_agent_by_name(monkeypatch):
    now = datetime.now(timezone.utc)
    agent = ChatAgent(
        id=uuid4(),
        name="Agente Minha DELPI",
        description=None,
        system_prompt="test",
        enabled=True,
        metadata={},
        created_at=now,
        updated_at=now,
        owner_user_id=None,
        visibility="system",
        category=None,
        icon=None,
        response_style=None,
        max_tool_calls=5,
        requires_confirmation_for_write=True,
    )
    monkeypatch.setattr(
        settings_module.Settings,
        "CHAT_PLATFORM_DEFAULT_AGENT_ENABLED",
        True,
    )
    monkeypatch.setattr(settings_module.Settings, "CHAT_PLATFORM_DEFAULT_AGENT_ID", "")
    monkeypatch.setattr(
        settings_module.Settings,
        "CHAT_PLATFORM_DEFAULT_AGENT_NAME",
        "Agente Minha DELPI",
    )

    resolved = ChatPlatformDefaultAgentService.resolve_agent_id(
        FakeSystemAgentRepository(agent),
        uuid4(),
    )

    assert resolved == agent.id
