from uuid import uuid4

from app.application.services.chat_workspace_agent_activation_service import (
    ChatWorkspaceAgentActivationService,
)


class FakeSession:
    def __init__(self, *, agent_id=None, project_id=None, user_id=None, session_id=None):
        self.agent_id = agent_id
        self.project_id = project_id
        self.user_id = user_id or uuid4()
        self.id = session_id or uuid4()


def test_resolve_explicit_agent_prefers_session_over_request():
    session_id = uuid4()
    request_id = uuid4()

    resolved = ChatWorkspaceAgentActivationService.resolve_explicit_agent_id(
        session_agent_id=session_id,
        request_agent_id=request_id,
    )

    assert resolved == session_id


def test_resolve_explicit_agent_returns_none_without_user_choice():
    assert (
        ChatWorkspaceAgentActivationService.resolve_explicit_agent_id(
            session_agent_id=None,
            request_agent_id=None,
        )
        is None
    )


def test_user_not_activated_without_explicit_agent_even_if_actions_exist():
    assert (
        ChatWorkspaceAgentActivationService.is_user_activated(
            session_agent_id=None,
            request_agent_id=None,
            actions_enabled=True,
        )
        is False
    )


def test_user_activated_when_session_has_agent_and_actions():
    agent_id = uuid4()

    assert (
        ChatWorkspaceAgentActivationService.is_user_activated(
            session_agent_id=agent_id,
            request_agent_id=None,
            actions_enabled=True,
        )
        is True
    )


def test_operational_tools_disabled_in_common_chat_workspace():
    assert (
        ChatWorkspaceAgentActivationService.operational_tools_enabled(
            {
                "userActivatedAgent": False,
                "actionsEnabled": True,
            }
        )
        is False
    )


def test_operational_tools_enabled_with_active_agent():
    assert (
        ChatWorkspaceAgentActivationService.operational_tools_enabled(
            {
                "userActivatedAgent": True,
                "actionsEnabled": True,
            }
        )
        is True
    )


def test_resolve_chat_mode_defaults_to_common_without_agent_id():
    assert (
        ChatWorkspaceAgentActivationService.resolve_chat_mode_for_request(
            chat_mode=None,
            request_agent_id=None,
        )
        == "common"
    )


def test_sync_session_project_binding_persists_request_project():
    project_id = uuid4()
    session = FakeSession(project_id=None)
    persisted: list[object] = []

    def update_session_project_id(*, session_id, user_id, project_id):
        persisted.append(project_id)

    ChatWorkspaceAgentActivationService.sync_session_project_binding(
        session=session,
        request_project_id=str(project_id),
        update_session_project_id=update_session_project_id,
    )

    assert session.project_id == project_id
    assert persisted == [project_id]


def test_sync_session_project_binding_clears_project_when_null():
    project_id = uuid4()
    session = FakeSession(project_id=project_id)
    cleared: list[object] = []

    def update_session_project_id(*, session_id, user_id, project_id):
        cleared.append(project_id)

    ChatWorkspaceAgentActivationService.sync_session_project_binding(
        session=session,
        request_project_id=None,
        update_session_project_id=update_session_project_id,
    )

    assert session.project_id is None
    assert cleared == [None]


def test_sync_session_agent_binding_clears_legacy_agent_on_common_chat():
    agent_id = uuid4()
    session = FakeSession(agent_id=agent_id)
    cleared: list[object] = []

    def update_session_agent_id(*, session_id, user_id, agent_id):
        cleared.append(agent_id)

    ChatWorkspaceAgentActivationService.sync_session_agent_binding(
        session=session,
        request_agent_id=None,
        chat_mode="common",
        update_session_agent_id=update_session_agent_id,
    )

    assert session.agent_id is None
    assert cleared == [None]
