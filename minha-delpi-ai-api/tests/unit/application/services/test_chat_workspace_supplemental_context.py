from uuid import uuid4

from app.application.services.chat_workspace_context_service import (
    ChatWorkspaceContextService,
)


class FakeSession:
    def __init__(self, *, agent_id=None, project_id=None):
        self.agent_id = agent_id
        self.project_id = project_id


class FakeAgent:
    def __init__(self, agent_id, *, name="Agente", prompt="prompt"):
        self.id = agent_id
        self.name = name
        self.description = None
        self.system_prompt = prompt
        self.metadata = {}
        self.category = None
        self.response_style = None
        self.max_tool_calls = 5
        self.requires_confirmation_for_write = True


class FakeProject:
    def __init__(self, project_id, *, name="Projeto", instructions=None):
        self.id = project_id
        self.name = name
        self.description = "desc"
        self.instructions = instructions
        self.default_agent_id = None
        self.metadata = {}


class FakeAgentRepository:
    def __init__(self, agents: dict):
        self.agents = agents

    def get_enabled_by_id(self, agent_id, user_id=None):
        return self.agents.get(agent_id)

    def list_enabled_action_ids(self, agent_id, user_id):
        return ["action.one"]

    def list_enabled_provider_keys(self, agent_id, user_id):
        return ["api-externa"]


class FakeProjectRepository:
    def __init__(self, projects: dict):
        self.projects = projects

    def get_accessible_by_id(self, project_id, user_id):
        project = self.projects.get(project_id)

        if not project:
            return None

        return project, "owner"


def test_merges_supplemental_agent_prompt_without_actions():
    primary_id = uuid4()
    supplemental_id = uuid4()
    primary = FakeAgent(primary_id, name="Primário", prompt="prompt primário")
    supplemental = FakeAgent(
        supplemental_id,
        name="Suplementar",
        prompt="prompt suplementar",
    )
    service = ChatWorkspaceContextService(
        project_repository=FakeProjectRepository({}),
        agent_repository=FakeAgentRepository(
            {
                primary_id: primary,
                supplemental_id: supplemental,
            }
        ),
    )

    context = service.build_context(
        session=FakeSession(agent_id=primary_id),
        user_id=uuid4(),
        supplemental_agent_ids=[str(supplemental_id)],
    )

    assert context["agent"]["id"] == str(primary_id)
    assert context["actionsEnabled"] is True
    assert "prompt primário" in context["agentPrompt"]
    assert "Agente suplementar: Suplementar" in context["agentPrompt"]
    assert "prompt suplementar" in context["agentPrompt"]
    assert len(context["supplementalAgents"]) == 1


def test_merges_supplemental_project_prompt():
    primary_id = uuid4()
    supplemental_id = uuid4()
    primary = FakeProject(primary_id, name="Projeto A", instructions="instr A")
    supplemental = FakeProject(
        supplemental_id,
        name="Projeto B",
        instructions="instr B",
    )
    service = ChatWorkspaceContextService(
        project_repository=FakeProjectRepository(
            {
                primary_id: primary,
                supplemental_id: supplemental,
            }
        ),
        agent_repository=FakeAgentRepository({}),
    )

    context = service.build_context(
        session=FakeSession(project_id=primary_id),
        user_id=uuid4(),
        supplemental_project_ids=[str(supplemental_id)],
    )

    assert context["project"]["id"] == str(primary_id)
    assert "Projeto atual: Projeto A" in context["projectPrompt"]
    assert "Projeto suplementar: Projeto B" in context["projectPrompt"]
    assert "instr B" in context["projectPrompt"]
    assert len(context["supplementalProjects"]) == 1
