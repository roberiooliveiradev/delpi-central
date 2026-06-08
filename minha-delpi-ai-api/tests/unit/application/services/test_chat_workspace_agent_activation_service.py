from uuid import uuid4

from app.application.services.chat_workspace_agent_activation_service import (
    ChatWorkspaceAgentActivationService,
)


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
