from dataclasses import dataclass
from uuid import UUID, uuid4

from app.application.services.chat_workspace_context_service import ChatWorkspaceContextService

FAKE_AGENT_ID = UUID("11111111-1111-4111-8111-111111111111")


@dataclass(frozen=True)
class FakeAgent:
    id: object
    name: str
    description: str | None
    system_prompt: str | None
    metadata: dict | None
    category: str | None = None
    response_style: str | None = None
    max_tool_calls: int | None = None
    requires_confirmation_for_write: bool = False


@dataclass(frozen=True)
class FakeSession:
    id: object
    project_id: object | None
    agent_id: object | None


class FakeProjectRepository:
    def get_accessible_by_id(self, project_id, user_id):
        return None


class FakeAgentRepository:
    def __init__(self):
        self.agent = FakeAgent(
            id=FAKE_AGENT_ID,
            name="Ações OpenAPI",
            description=None,
            system_prompt="Use actions com cuidado.",
            metadata={"allowed_actions": ["fallback.action"]},
        )

    def get_enabled_by_id(self, agent_id, user_id=None):
        if agent_id == self.agent.id:
            return self.agent
        return None

    def list_enabled_action_ids(self, agent_id, user_id):
        return ["real.action.one", "real.action.two"]

    def list_enabled_provider_keys(self, agent_id, user_id):
        return ["api-delpi"]


def test_workspace_context_uses_agent_action_table_before_metadata_fallback():
    service = ChatWorkspaceContextService(
        project_repository=FakeProjectRepository(),
        agent_repository=FakeAgentRepository(),
    )

    context = service.build_context(
        session=FakeSession(id=uuid4(), project_id=None, agent_id=FAKE_AGENT_ID),
        user_id=uuid4(),
    )

    assert context["agentId"] == str(FAKE_AGENT_ID)
    assert context["allowedActionIds"] == ["real.action.one", "real.action.two"]


class FakeAgentRepositoryWithoutRows(FakeAgentRepository):
    def list_enabled_action_ids(self, agent_id, user_id):
        return []

    def list_enabled_provider_keys(self, agent_id, user_id):
        return []


def test_workspace_context_falls_back_to_metadata_allowed_actions():
    service = ChatWorkspaceContextService(
        project_repository=FakeProjectRepository(),
        agent_repository=FakeAgentRepositoryWithoutRows(),
    )

    context = service.build_context(
        session=FakeSession(id=uuid4(), project_id=None, agent_id=FAKE_AGENT_ID),
        user_id=uuid4(),
    )

    assert context["allowedActionIds"] == ["fallback.action"]
