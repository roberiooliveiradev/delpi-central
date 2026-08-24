from types import SimpleNamespace

from app.application.services.chat_tool_context_service import ChatToolContextService


def test_emit_partial_tool_calls_filters_primary_ok_actions():
    host = ChatToolContextService.__new__(ChatToolContextService)
    captured: list[tuple[list[dict], int]] = []

    execution = SimpleNamespace(
        safe_tool_calls=[
            {
                "name": "execute_external_action",
                "metadata": {"ok": True, "path": "/products/1/stock"},
            },
            {
                "name": "execute_web_search",
                "metadata": {"ok": True},
            },
        ]
    )

    host._emit_partial_tool_calls(
        execution,
        on_tool_calls_partial=lambda tool_calls, wave: captured.append((tool_calls, wave)),
        wave=1,
    )

    assert len(captured) == 1
    tool_calls, wave = captured[0]
    assert wave == 1
    assert len(tool_calls) == 1
    assert tool_calls[0]["metadata"]["compositionRole"] == "primary"
