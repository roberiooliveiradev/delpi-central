from datetime import datetime, timezone
from uuid import uuid4

from app.domain.entities.chat_message import ChatMessage
from app.domain.services.chat_message_branch_service import ChatMessageBranchService


def _message(
    *,
    role: str,
    content: str,
    parent_message_id=None,
    created_offset: int = 0,
) -> ChatMessage:
    base = datetime(2026, 5, 30, 12, 0, 0, tzinfo=timezone.utc)
    return ChatMessage(
        id=uuid4(),
        session_id=uuid4(),
        role=role,
        content=content,
        metadata=None,
        created_at=base.replace(second=created_offset),
        parent_message_id=parent_message_id,
    )


def test_build_active_path_follows_leaf():
    root = _message(role="user", content="ola", created_offset=0)
    assistant = _message(
        role="assistant",
        content="oi",
        parent_message_id=root.id,
        created_offset=1,
    )
    user_two = _message(
        role="user",
        content="estoque",
        parent_message_id=assistant.id,
        created_offset=2,
    )
    messages = [root, assistant, user_two]

    path = ChatMessageBranchService.build_active_path(messages, user_two.id)

    assert [item.content for item in path] == ["ola", "oi", "estoque"]


def test_resend_creates_sibling_branch_path():
    root = _message(role="user", content="pergunta", created_offset=0)
    assistant = _message(
        role="assistant",
        content="resposta",
        parent_message_id=root.id,
        created_offset=1,
    )
    user_original = _message(
        role="user",
        content="refine",
        parent_message_id=assistant.id,
        created_offset=2,
    )
    user_branch = _message(
        role="user",
        content="refine filial 02",
        parent_message_id=assistant.id,
        created_offset=3,
    )
    assistant_branch = _message(
        role="assistant",
        content="filial 02",
        parent_message_id=user_branch.id,
        created_offset=4,
    )
    messages = [root, assistant, user_original, user_branch, assistant_branch]

    path = ChatMessageBranchService.build_active_path(messages, assistant_branch.id)

    assert [item.id for item in path] == [
        root.id,
        assistant.id,
        user_branch.id,
        assistant_branch.id,
    ]

    navigation = ChatMessageBranchService.build_user_branch_navigation(messages, path)

    assert navigation[str(user_branch.id)]["currentIndex"] == 2
    assert navigation[str(user_branch.id)]["total"] == 2


def test_build_fork_path_includes_assistant_after_user_on_active_branch():
    root = _message(role="user", content="pergunta", created_offset=0)
    assistant = _message(
        role="assistant",
        content="resposta",
        parent_message_id=root.id,
        created_offset=1,
    )
    user_question = _message(
        role="user",
        content="refine",
        parent_message_id=assistant.id,
        created_offset=2,
    )
    user_answer = _message(
        role="assistant",
        content="refine ok",
        parent_message_id=user_question.id,
        created_offset=3,
    )
    messages = [root, assistant, user_question, user_answer]

    path = ChatMessageBranchService.build_fork_path(
        messages,
        user_question.id,
        user_answer.id,
    )

    assert [item.role for item in path] == ["user", "assistant", "user", "assistant"]
    assert path[-1].content == "refine ok"


def test_build_fork_path_omits_assistant_when_resending_user_message():
    root = _message(role="user", content="pergunta", created_offset=0)
    assistant = _message(
        role="assistant",
        content="resposta",
        parent_message_id=root.id,
        created_offset=1,
    )
    messages = [root, assistant]

    path = ChatMessageBranchService.build_fork_path(
        messages,
        root.id,
        assistant.id,
        include_assistant_reply=False,
    )

    assert [item.role for item in path] == ["user"]
    assert path[-1].content == "pergunta"
