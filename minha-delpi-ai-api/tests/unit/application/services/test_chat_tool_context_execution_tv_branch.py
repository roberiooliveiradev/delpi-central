"""Execução da tool TV isolada no loop de tools.

Regressão: o import de ``ChatTvDashboardCopilotIntentService`` vivia dentro da
branch de ``execute_external_action``, tornando o nome local à função inteira.
Quando o turno executava só ``tv_dashboard_copilot``, o loop quebrava com
``UnboundLocalError`` e o usuário via «Não consegui gerar a resposta agora».
"""

from __future__ import annotations

from typing import Any

from app.application.services.chat_tool_context_execution_service import (
    ChatToolContextExecutionService,
)
from app.domain.entities.tool_result import ToolResult


class _FakeExecuteToolUseCase:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, request) -> ToolResult:
        self.calls.append(
            {"tool": request.tool_name, "arguments": dict(request.arguments or {})}
        )
        return ToolResult(
            name="tv_dashboard_copilot",
            data={"persisted": True},
            metadata={"ok": True, "mode": "apply", "sensitivity": "write"},
        )


class _FakeFormatter:
    @staticmethod
    def _build_safe_tool_metadata(*, tool_name: str, metadata: dict | None, data: Any) -> dict:
        return dict(metadata or {})

    @staticmethod
    def _format_tool_context(**_kwargs) -> str:
        return "contexto tv"


class _FakeHost:
    def __init__(self) -> None:
        self.execute_tool_use_case = _FakeExecuteToolUseCase()
        self.external_action_repository = None
        self._build_workspace_context = {
            "tvDashboardHostContext": {
                "surface": "tv-dashboard",
                "playlistId": "pl-1",
            }
        }
        self._external_action_formatter = _FakeFormatter()

    @staticmethod
    def _build_response_preview(metadata: dict) -> str:
        return ""

    @staticmethod
    def _is_successful_external_action(metadata: dict) -> bool:
        return bool(metadata.get("ok"))

    @staticmethod
    def _format_tool_error_context(**_kwargs) -> str:
        return "erro tv"


def _execute(arguments: dict) -> tuple[_FakeHost, Any]:
    host = _FakeHost()
    state = ChatToolContextExecutionService().execute_selected_tools(
        host,
        user_id="user-1",
        access_token="tok",
        message="crie um slide",
        raw_message="crie um slide",
        allowed_action_ids=None,
        previous_messages=None,
        selected_tools=[
            {
                "name": "tv_dashboard_copilot",
                "arguments": arguments,
                "reason": "Pedido de mutação no editor TV Dashboard.",
            }
        ],
        on_stream_activity=None,
        paginated_service=None,
    )
    return host, state


def test_tv_tool_alone_executes_without_unbound_local():
    host, state = _execute(
        {
            "mode": "apply",
            "ops": [{"op": "add_blank_slide"}],
            "confirmationPolicy": "direct",
            "risk": "additive",
        }
    )

    assert host.execute_tool_use_case.calls, "a tool TV deveria ter sido executada"
    assert host.execute_tool_use_case.calls[0]["tool"] == "tv_dashboard_copilot"
    assert state.safe_tool_calls[0]["metadata"]["ok"] is True
    # Política direct não bloqueia por confirmação.
    assert state.safe_tool_calls[0]["metadata"].get("blocked") is not True


def test_tv_tool_receives_host_target_from_workspace():
    host, _state = _execute(
        {
            "mode": "apply",
            "ops": [{"op": "add_blank_slide"}],
            "confirmationPolicy": "direct",
        }
    )

    target = host.execute_tool_use_case.calls[0]["arguments"].get("target") or {}
    assert target.get("playlistId") == "pl-1"
