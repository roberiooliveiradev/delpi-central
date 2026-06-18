from uuid import UUID, uuid4

from app.application.dto.update_chat_project_request import UpdateChatProjectRequest
from app.application.use_cases.chat_projects_use_cases import UpdateChatProjectUseCase
from app.domain.entities.chat_project import ChatProject
from datetime import datetime, timezone


class _FakeProjectRepository:
    def __init__(self, project: ChatProject):
        self.project = project
        self.last_update: dict | None = None

    def get_accessible_by_id(self, project_id: UUID, user_id: UUID):
        if self.project.id == project_id and self.project.user_id == user_id:
            return self.project, "owner"
        return None

    def update(self, project_id: UUID, user_id: UUID, *, apply_null=None, **fields):
        self.last_update = {"apply_null": apply_null, **fields}

        if "default_agent_id" in fields or (
            apply_null and "default_agent_id" in apply_null
        ):
            self.project = ChatProject(
                id=self.project.id,
                user_id=self.project.user_id,
                name=self.project.name,
                description=self.project.description,
                instructions=self.project.instructions,
                default_agent_id=fields.get("default_agent_id"),
                visibility=self.project.visibility,
                icon=self.project.icon,
                color=self.project.color,
                archived_at=self.project.archived_at,
                metadata=self.project.metadata,
                created_at=self.project.created_at,
                updated_at=self.project.updated_at,
            )

        return self.project


def _sample_project(*, default_agent_id: UUID | None = None) -> ChatProject:
    now = datetime.now(timezone.utc)
    owner_id = uuid4()

    return ChatProject(
        id=uuid4(),
        user_id=owner_id,
        name="Projeto teste",
        description=None,
        instructions=None,
        default_agent_id=default_agent_id,
        visibility="private",
        icon=None,
        color=None,
        archived_at=None,
        metadata={},
        created_at=now,
        updated_at=now,
    )


def test_update_clears_default_agent_when_explicit_null():
    agent_id = uuid4()
    project = _sample_project(default_agent_id=agent_id)
    repository = _FakeProjectRepository(project)
    use_case = UpdateChatProjectUseCase(repository)

    result = use_case.execute(
        UpdateChatProjectRequest(
            user_id=str(project.user_id),
            project_id=str(project.id),
            default_agent_id=None,
            explicit_default_agent_id=True,
        )
    )

    assert result is not None
    assert result.default_agent_id is None
    assert repository.last_update is not None
    assert repository.last_update["default_agent_id"] is None
    assert "default_agent_id" in repository.last_update["apply_null"]


def test_update_sets_default_agent_when_explicit_uuid():
    project = _sample_project(default_agent_id=None)
    repository = _FakeProjectRepository(project)
    use_case = UpdateChatProjectUseCase(repository)
    agent_id = uuid4()

    result = use_case.execute(
        UpdateChatProjectRequest(
            user_id=str(project.user_id),
            project_id=str(project.id),
            default_agent_id=str(agent_id),
            explicit_default_agent_id=True,
        )
    )

    assert result is not None
    assert result.default_agent_id == str(agent_id)
    assert repository.last_update is not None
    assert repository.last_update["default_agent_id"] == agent_id
    assert repository.last_update["apply_null"] == frozenset()


def test_update_ignores_default_agent_when_not_explicit():
    agent_id = uuid4()
    project = _sample_project(default_agent_id=agent_id)
    repository = _FakeProjectRepository(project)
    use_case = UpdateChatProjectUseCase(repository)

    result = use_case.execute(
        UpdateChatProjectRequest(
            user_id=str(project.user_id),
            project_id=str(project.id),
            name="Novo nome",
        )
    )

    assert result is not None
    assert result.default_agent_id == str(agent_id)
    assert repository.last_update is not None
    assert "default_agent_id" not in repository.last_update
    assert repository.last_update.get("apply_null") in (None, frozenset())
