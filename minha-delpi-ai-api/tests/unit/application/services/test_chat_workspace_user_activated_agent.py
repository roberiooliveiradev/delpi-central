from uuid import uuid4

from app.application.services.chat_workspace_context_service import (
    ChatWorkspaceContextService,
)


class FakeSession:
    def __init__(self, *, agent_id=None, project_id=None):
        self.agent_id = agent_id
        self.project_id = project_id


class FakeAgent:
    def __init__(self, agent_id):
        self.id = agent_id
        self.name = "Agente teste"
        self.description = None
        self.system_prompt = "prompt"
        self.metadata = {}
        self.category = None
        self.response_style = None
        self.max_tool_calls = 5
        self.requires_confirmation_for_write = True


class FakeAgentRepository:
    def __init__(self, agent: FakeAgent):
        self.agent = agent

    def get_enabled_by_id(self, agent_id, user_id=None):
        if agent_id == self.agent.id:
            return self.agent
        return None

    def list_enabled_action_ids(self, agent_id, user_id):
        return ["action.one"]

    def list_enabled_provider_keys(self, agent_id, user_id):
        return ["api-externa"]


def test_user_not_activated_when_only_platform_implicit_agent(monkeypatch):
    agent_id = uuid4()
    agent = FakeAgent(agent_id)
    service = ChatWorkspaceContextService(
        project_repository=None,
        agent_repository=FakeAgentRepository(agent),
    )

    monkeypatch.setattr(
        "app.application.services.chat_workspace_context_service.ChatPlatformDefaultAgentService.resolve_agent_id",
        lambda *_args, **_kwargs: agent_id,
    )

    context = service.build_context(
        session=FakeSession(),
        user_id=uuid4(),
    )

    assert context["actionsEnabled"] is True
    assert context["userActivatedAgent"] is False


def test_user_activated_when_session_has_agent_id(monkeypatch):
    agent_id = uuid4()
    agent = FakeAgent(agent_id)
    service = ChatWorkspaceContextService(
        project_repository=None,
        agent_repository=FakeAgentRepository(agent),
    )

    monkeypatch.setattr(
        "app.application.services.chat_workspace_context_service.ChatPlatformDefaultAgentService.resolve_agent_id",
        lambda *_args, **_kwargs: None,
    )

    context = service.build_context(
        session=FakeSession(agent_id=agent_id),
        user_id=uuid4(),
    )

    assert context["userActivatedAgent"] is True
