from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService


@dataclass(frozen=True)
class FakeAgent:
    id: object
    key: str
    name: str
    description: str | None
    system_prompt: str | None
    metadata: dict | None
    response_style: str | None = None
    max_tool_calls: int | None = None
    requires_confirmation_for_write: bool = False


@dataclass(frozen=True)
class FakeSession:
    id: object
    project_id: object | None
    agent_key: str | None


class FakeProjectRepository:
    def get_accessible_by_id(self, project_id, user_id):
        return None


class FakeAgentRepository:
    def __init__(self):
        self.agent = FakeAgent(
            id=uuid4(),
            key="acoes-openapi",
            name="Ações OpenAPI",
            description=None,
            system_prompt="Use actions com cuidado.",
            metadata={"allowed_actions": ["fallback.action"]},
        )

    def get_enabled_by_key(self, key, user_id=None):
        if key == self.agent.key:
            return self.agent
        return None

    def list_enabled_action_ids(self, agent_id, user_id):
        return ["real.action.one", "real.action.two"]


def test_workspace_context_uses_agent_action_table_before_metadata_fallback():
    service = ChatWorkspaceContextService(
        project_repository=FakeProjectRepository(),
        agent_repository=FakeAgentRepository(),
    )

    context = service.build_context(
        session=FakeSession(id=uuid4(), project_id=None, agent_key="acoes-openapi"),
        user_id=uuid4(),
    )

    assert context["agentKey"] == "acoes-openapi"
    assert context["allowedActionIds"] == ["real.action.one", "real.action.two"]


class FakeAgentRepositoryWithoutRows(FakeAgentRepository):
    def list_enabled_action_ids(self, agent_id, user_id):
        return []


def test_workspace_context_falls_back_to_metadata_allowed_actions():
    service = ChatWorkspaceContextService(
        project_repository=FakeProjectRepository(),
        agent_repository=FakeAgentRepositoryWithoutRows(),
    )

    context = service.build_context(
        session=FakeSession(id=uuid4(), project_id=None, agent_key="acoes-openapi"),
        user_id=uuid4(),
    )

    assert context["allowedActionIds"] == ["fallback.action"]
