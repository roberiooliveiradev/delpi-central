"""E4.S3 — parallel reads e classificação read-safe."""

from __future__ import annotations

import time
from typing import Any

from app.application.services.chat_tool_context_execution_service import (
    ChatToolContextExecutionService,
)
from app.application.services.chat_tool_context_parallel_read_service import (
    ChatToolContextParallelReadService,
)
from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.entities.tool_result import ToolResult
from app.domain.services.chat_assistant_content_service import (
    invalidate_assistant_content_cache,
)
from app.domain.services.chat_write_confirmation_service import (
    ChatWriteConfirmationService,
)

configure_domain_infrastructure_ports()
invalidate_assistant_content_cache("tool_context")


def test_is_parallel_safe_read_get_and_sql():
    assert ChatWriteConfirmationService.is_parallel_safe_read(
        {"method": "GET", "sensitivity": "read", "path": "/products/1/stock"}
    )
    assert ChatWriteConfirmationService.is_parallel_safe_read(
        {"method": "POST", "sensitivity": "sql", "path": "/data/sql"}
    )
    assert not ChatWriteConfirmationService.is_parallel_safe_read(
        {"method": "POST", "sensitivity": "write", "path": "/orders"}
    )
    assert not ChatWriteConfirmationService.is_parallel_safe_read(
        {"method": "DELETE", "sensitivity": "destructive", "path": "/x"}
    )


def test_plan_batches_requires_min_consecutive():
    assert ChatToolContextParallelReadService.plan_batches([True]) == []
    assert ChatToolContextParallelReadService.plan_batches([True, True]) == [[0, 1]]
    assert ChatToolContextParallelReadService.plan_batches(
        [True, False, True, True, True]
    ) == [[2, 3, 4]]


class _SlowRepo:
    def get_action_for_execution(self, action_id: str) -> dict:
        return {
            "action": {
                "id": action_id,
                "method": "GET",
                "sensitivity": "read",
                "path": f"/products/{action_id}/stock",
            }
        }


class _SlowExecute:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self._lock_times: list[float] = []

    def execute(self, request) -> ToolResult:
        action_id = str((request.arguments or {}).get("actionId") or "")
        self.calls.append(action_id)
        started = time.perf_counter()
        time.sleep(0.08)
        self._lock_times.append(time.perf_counter() - started)
        return ToolResult(
            name="execute_external_action",
            data={"actionId": action_id},
            metadata={"ok": True, "actionId": action_id, "path": f"/p/{action_id}"},
        )


class _Formatter:
    @staticmethod
    def _build_safe_tool_metadata(*, tool_name: str, metadata: dict | None, data: Any) -> dict:
        return dict(metadata or {})

    @staticmethod
    def _format_tool_context(**_kwargs) -> str:
        return "ok"


class _Host:
    def __init__(self) -> None:
        self.execute_tool_use_case = _SlowExecute()
        self.external_action_repository = _SlowRepo()
        self._build_workspace_context = {}
        self._external_action_formatter = _Formatter()
        self._auxiliary_service = type(
            "Aux",
            (),
            {"_try_sql_error_recovery": staticmethod(lambda **_k: None)},
        )()

    @staticmethod
    def _build_response_preview(metadata: dict) -> str:
        return ""

    @staticmethod
    def _is_successful_external_action(metadata: dict) -> bool:
        return bool(metadata.get("ok"))

    @staticmethod
    def _format_tool_error_context(**_kwargs) -> str:
        return "err"


class _Paginated:
    def maybe_consolidate(self, **kwargs):
        return kwargs["base_data"], kwargs["base_metadata"], None


def test_execute_selected_tools_runs_independent_reads_in_parallel():
    host = _Host()
    tools = [
        {
            "name": "execute_external_action",
            "arguments": {"actionId": "a1", "path": "/p/a1"},
            "reason": "stock a",
        },
        {
            "name": "execute_external_action",
            "arguments": {"actionId": "a2", "path": "/p/a2"},
            "reason": "stock b",
        },
    ]

    started = time.perf_counter()
    state = ChatToolContextExecutionService().execute_selected_tools(
        host,
        user_id="u1",
        access_token="tok",
        message="estoque dos dois",
        raw_message="estoque dos dois",
        allowed_action_ids=["a1", "a2"],
        previous_messages=None,
        selected_tools=tools,
        on_stream_activity=None,
        paginated_service=_Paginated(),
    )
    elapsed = time.perf_counter() - started

    assert len(state.safe_tool_calls) == 2
    assert [c["metadata"].get("actionId") for c in state.safe_tool_calls] == ["a1", "a2"]
    assert set(host.execute_tool_use_case.calls) == {"a1", "a2"}
    # Sequencial seria ~0.16s; paralelo deve ficar bem abaixo de 0.15s com folga.
    assert elapsed < 0.15
