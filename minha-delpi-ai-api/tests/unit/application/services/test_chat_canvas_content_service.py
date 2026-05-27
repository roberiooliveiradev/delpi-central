from datetime import datetime, timezone
from uuid import uuid4

from app.application.services.chat_canvas_content_service import ChatCanvasContentService
from app.domain.entities.chat_message import ChatMessage


def _assistant_message(content: str) -> ChatMessage:
    now = datetime.now(timezone.utc)
    return ChatMessage(
        id=uuid4(),
        session_id=uuid4(),
        role="assistant",
        content=content,
        metadata=None,
        created_at=now,
    )


def test_resolve_returns_markdown_from_last_assistant():
    assistant = _assistant_message("## Perfil\n\nVocê é o analista João.")

    action = ChatCanvasContentService.resolve(
        "coloque na lousa",
        [assistant],
        {"capabilities": {"canvas": True}},
    )

    assert action is not None
    assert action.open_payload is not None
    assert "Perfil" in action.open_payload.title
    assert "João" in action.open_payload.markdown
    assert "lousa" in action.answer.lower()


def test_resolve_without_assistant_history():
    action = ChatCanvasContentService.resolve(
        "coloque em canva",
        [],
        {"capabilities": {"canvas": True}},
    )

    assert action is not None
    assert action.open_payload is None
    assert "ainda não há" in action.answer.lower()


def test_resolve_when_canvas_disabled():
    action = ChatCanvasContentService.resolve(
        "coloque na lousa",
        [_assistant_message("Conteúdo")],
        {"capabilities": {"canvas": False}},
    )

    assert action is not None
    assert action.open_payload is None
    assert "não está habilitada" in action.answer.lower()
