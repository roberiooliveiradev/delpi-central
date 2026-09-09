"""Clarify/unknown_tool são sinais do planner — não vão ao executor HTTP."""

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
        raise AssertionError(f"planner signal should not execute: {request.tool_name}")


class _FakeHost:
    def __init__(self) -> None:
        self.execute_tool_use_case = _FakeExecuteToolUseCase()
        self.external_action_repository = None
        self._build_workspace_context = {}
        self._external_action_formatter = None

    @staticmethod
    def _build_response_preview(metadata: dict) -> str:
        return ""

    @staticmethod
    def _is_successful_external_action(metadata: dict) -> bool:
        return bool(metadata.get("ok"))

    @staticmethod
    def _format_tool_error_context(**_kwargs) -> str:
        return "erro"


def test_clarify_external_action_is_not_executed():
    host = _FakeHost()
    state = ChatToolContextExecutionService().execute_selected_tools(
        host,
        user_id="user-1",
        access_token="tok",
        message="taxa de fechamento filial 01 em agosto 2026",
        raw_message="Qual a taxa de fechamento da filial 01 em agosto 2026?",
        allowed_action_ids=None,
        previous_messages=None,
        selected_tools=[
            {
                "name": "clarify_external_action",
                "arguments": {
                    "message": "Informe o período em YYYY-MM-DD.",
                },
                "reason": "Invalid format for parameter: start_date",
            }
        ],
        on_stream_activity=None,
        paginated_service=None,
    )

    assert host.execute_tool_use_case.calls == []
    assert state.direct_answer == "Informe o período em YYYY-MM-DD."
    assert state.safe_tool_calls[0]["metadata"]["skippedExecution"] is True
    assert "Tool not found" not in str(state.safe_tool_calls[0]["metadata"])


def test_unknown_tool_sibling_is_not_executed():
    host = _FakeHost()
    state = ChatToolContextExecutionService().execute_selected_tools(
        host,
        user_id="user-1",
        access_token="tok",
        message="estoque do produto",
        raw_message="estoque do produto",
        allowed_action_ids=None,
        previous_messages=None,
        selected_tools=[
            {
                "name": "unknown_tool",
                "arguments": {"message": "Não identifiquei a ação."},
                "reason": "no matching action",
            }
        ],
        on_stream_activity=None,
        paginated_service=None,
    )

    assert host.execute_tool_use_case.calls == []
    assert state.direct_answer == "Não identifiquei a ação."
