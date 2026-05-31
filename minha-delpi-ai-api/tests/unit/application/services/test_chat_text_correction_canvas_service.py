"""Correção textual com atualização da lousa."""

from types import SimpleNamespace

from app.application.services.chat_text_correction_canvas_service import (
    ChatTextCorrectionCanvasService,
)


def _msg(metadata: dict | None = None, role: str = "assistant"):
    return SimpleNamespace(
        role=role,
        metadata=metadata or {},
    )


def test_load_active_canvas_from_history():
    messages = [
        _msg(
            {
                "canvasOpen": {
                    "title": "Rascunho",
                    "markdown": "O estoque esta baixo.",
                    "sourceMessageId": "abc-123",
                }
            }
        ),
    ]

    markdown, title, source_id = ChatTextCorrectionCanvasService.load_active_canvas(messages)

    assert "estoque" in markdown
    assert title == "Rascunho"
    assert source_id == "abc-123"


def test_resolve_canvas_open_after_correction():
    messages = [
        _msg(
            {
                "canvasOpen": {
                    "title": "Comunicado",
                    "markdown": "Texto original com erro.",
                }
            }
        ),
    ]
    workspace = {"agent": {"capabilities": {"canvas": True}}}

    payload = ChatTextCorrectionCanvasService.resolve_canvas_open_after_correction(
        message="corrija o texto da lousa",
        answer="Segue a versão corrigida:\n\nTexto original sem erro.",
        previous_messages=messages,
        workspace_context=workspace,
    )

    assert payload is not None
    assert "sem erro" in payload.markdown
    assert payload.title == "Comunicado"


def test_resolve_canvas_open_skips_without_canvas_content():
    payload = ChatTextCorrectionCanvasService.resolve_canvas_open_after_correction(
        message="corrija o texto da lousa",
        answer="Segue a versão corrigida:\n\nSó chat.",
        previous_messages=[],
        workspace_context={"agent": {"capabilities": {"canvas": True}}},
    )

    assert payload is None
