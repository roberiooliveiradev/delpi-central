from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.application.dto.create_chat_agent_request import CreateChatAgentRequest
from app.application.use_cases.chat_agents_use_cases import (
    ChatAgentKeyConflictError,
    ChatAgentPermissionDeniedError,
    CreateChatAgentUseCase,
    ListChatAgentSharesUseCase,
    ListChatAgentsUseCase,
    PreviewChatAgentUseCase,
    RevokeChatAgentShareUseCase,
)


def test_list_agents_can_include_disabled():
    repository = MagicMock()
    repository.list_accessible.return_value = []

    ListChatAgentsUseCase(repository).execute(str(uuid4()), include_disabled=True)

    repository.list_accessible.assert_called_once()
    assert repository.list_accessible.call_args.kwargs["include_disabled"] is True


def test_list_shares_delegates_to_repository():
    agent_id = uuid4()
    user_id = uuid4()
    repository = MagicMock()
    repository.list_shares.return_value = [{"target_user_id": str(uuid4()), "role": "viewer"}]

    result = ListChatAgentSharesUseCase(repository).execute(
        user_id=str(user_id),
        agent_id=str(agent_id),
    )

    repository.list_shares.assert_called_once_with(agent_id, user_id)
    assert len(result) == 1


def test_revoke_share_delegates_to_repository():
    agent_id = uuid4()
    user_id = uuid4()
    target_user_id = uuid4()
    repository = MagicMock()
    repository.revoke_share.return_value = True

    revoked = RevokeChatAgentShareUseCase(repository).execute(
        user_id=str(user_id),
        agent_id=str(agent_id),
        target_user_id=str(target_user_id),
    )

    repository.revoke_share.assert_called_once_with(agent_id, user_id, target_user_id)
    assert revoked is True


def test_preview_agent_denied_for_viewer():
    agent_id = uuid4()
    user_id = uuid4()
    repository = MagicMock()
    repository.get_accessible_by_id.return_value = (MagicMock(), "viewer")

    with pytest.raises(ChatAgentPermissionDeniedError):
        PreviewChatAgentUseCase(repository, MagicMock()).execute(
            user_id=str(user_id),
            agent_id=str(agent_id),
            message="Olá",
            access_token=None,
        )


def test_preview_agent_calls_simulate_for_editor():
    agent_id = uuid4()
    user_id = uuid4()
    repository = MagicMock()
    repository.get_accessible_by_id.return_value = (MagicMock(), "editor")
    simulate = MagicMock()
    simulate.execute.return_value = {"answerPreview": "ok"}

    result = PreviewChatAgentUseCase(repository, simulate).execute(
        user_id=str(user_id),
        agent_id=str(agent_id),
        message="Teste",
        access_token="token",
        generate_answer=True,
    )

    simulate.execute.assert_called_once()
    assert result["answerPreview"] == "ok"


def test_create_agent_maps_integrity_error_to_key_conflict():
    repository = MagicMock()
    repository.create.side_effect = IntegrityError("insert", {}, Exception("dup"))

    with pytest.raises(ChatAgentKeyConflictError):
        CreateChatAgentUseCase(repository).execute(
            CreateChatAgentRequest(
                user_id=str(uuid4()),
                name="Agente",
            )
        )
