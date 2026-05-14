from dataclasses import dataclass
from uuid import uuid4

from app.application.services.chat_knowledge_scope_service import (
    ChatKnowledgeScopeService,
)


@dataclass
class FakeSession:
    id: object
    project_id: object | None = None


def test_build_filters_includes_global_session_project_and_agent():
    user_id = uuid4()
    session_id = uuid4()
    project_id = uuid4()

    service = ChatKnowledgeScopeService()

    filters = service.build_filters(
        user_id=user_id,
        session=FakeSession(
            id=session_id,
            project_id=project_id,
        ),
        workspace_context={
            "project": {
                "id": str(project_id),
            },
            "agentKey": "minha-delpi-chat",
        },
    )

    assert filters == {
        "user_id": str(user_id),
        "session_id": str(session_id),
        "project_id": str(project_id),
        "agent_key": "minha-delpi-chat",
        "include_global": True,
    }


def test_build_filters_uses_session_project_when_workspace_project_is_missing():
    user_id = uuid4()
    session_id = uuid4()
    project_id = uuid4()

    service = ChatKnowledgeScopeService()

    filters = service.build_filters(
        user_id=user_id,
        session=FakeSession(
            id=session_id,
            project_id=project_id,
        ),
        workspace_context={
            "project": None,
            "agentKey": None,
        },
    )

    assert filters["user_id"] == str(user_id)
    assert filters["session_id"] == str(session_id)
    assert filters["project_id"] == str(project_id)
    assert filters["agent_key"] is None
    assert filters["include_global"] is True


def test_build_filters_without_project_keeps_project_id_none():
    user_id = uuid4()
    session_id = uuid4()

    service = ChatKnowledgeScopeService()

    filters = service.build_filters(
        user_id=user_id,
        session=FakeSession(
            id=session_id,
            project_id=None,
        ),
        workspace_context={},
    )

    assert filters["user_id"] == str(user_id)
    assert filters["session_id"] == str(session_id)
    assert filters["project_id"] is None
    assert filters["agent_key"] is None
    assert filters["include_global"] is True
