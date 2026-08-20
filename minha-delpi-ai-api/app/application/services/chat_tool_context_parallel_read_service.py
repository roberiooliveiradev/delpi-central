"""Execução paralela de leituras OpenAPI independentes (E4.S3).

Writes e deps ficam serializadas no loop canônico de
``ChatToolContextExecutionService``; aqui só o batch de HTTP reads.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable

from app.application.dto.execute_tool_request import ExecuteToolRequest
from app.application.services.chat_tool_context_content_service import (
    ChatToolContextContentService,
)
from app.domain.entities.tool_result import ToolResult
from app.domain.services.chat_write_confirmation_service import (
    ChatWriteConfirmationService,
)


@dataclass(frozen=True)
class ParallelReadOutcome:
    index: int
    result: ToolResult | None = None
    error: BaseException | None = None


class ChatToolContextParallelReadService:
    @classmethod
    def enabled(cls) -> bool:
        node = ChatToolContextContentService.get_node("execution")
        if not isinstance(node, dict):
            return True
        return bool(node.get("parallelReadsEnabled", True))

    @classmethod
    def max_workers(cls) -> int:
        node = ChatToolContextContentService.get_node("execution")
        raw = node.get("parallelReadMaxWorkers") if isinstance(node, dict) else None
        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 4

    @classmethod
    def min_batch(cls) -> int:
        node = ChatToolContextContentService.get_node("execution")
        raw = node.get("parallelReadMinBatch") if isinstance(node, dict) else None
        try:
            return max(2, int(raw))
        except (TypeError, ValueError):
            return 2

    @classmethod
    def resolve_action_row(
        cls,
        *,
        host: Any,
        selected_tool: dict,
    ) -> dict | None:
        if str(selected_tool.get("name") or "") != "execute_external_action":
            return None
        arguments = dict(selected_tool.get("arguments") or {})
        action_id = str(arguments.get("actionId") or arguments.get("action_id") or "")
        if not action_id or not getattr(host, "external_action_repository", None):
            return None
        bundle = host.external_action_repository.get_action_for_execution(action_id)
        action = (bundle or {}).get("action") if bundle else None
        return action if isinstance(action, dict) else None

    @classmethod
    def is_parallel_candidate(
        cls,
        *,
        host: Any,
        selected_tool: dict,
        raw_message: str,
    ) -> bool:
        if not cls.enabled():
            return False
        if str(selected_tool.get("name") or "") != "execute_external_action":
            return False
        action = cls.resolve_action_row(host=host, selected_tool=selected_tool)
        if not ChatWriteConfirmationService.is_parallel_safe_read(action):
            return False
        if ChatWriteConfirmationService.should_block_execution(
            message=raw_message,
            action=action,
        ):
            return False
        return True

    @classmethod
    def plan_batches(cls, candidates: list[bool]) -> list[list[int]]:
        """Agrupa índices consecutivos True em lotes elegíveis (≥ min_batch)."""
        batches: list[list[int]] = []
        current: list[int] = []
        min_size = cls.min_batch()

        for index, eligible in enumerate(candidates):
            if eligible:
                current.append(index)
                continue
            if len(current) >= min_size:
                batches.append(current)
            current = []

        if len(current) >= min_size:
            batches.append(current)

        return batches

    @classmethod
    def execute_batch(
        cls,
        *,
        host: Any,
        user_id: str,
        access_token: str,
        selected_tools: list[dict],
        indices: list[int],
        prepare_arguments: Callable[[dict], dict] | None = None,
    ) -> dict[int, ParallelReadOutcome]:
        """Dispara HTTP dos índices em paralelo; retorna mapa índice → outcome."""
        if len(indices) < cls.min_batch():
            return {}

        workers = min(cls.max_workers(), len(indices))
        outcomes: dict[int, ParallelReadOutcome] = {}

        def _run(index: int) -> ParallelReadOutcome:
            selected = selected_tools[index]
            arguments = dict(selected.get("arguments") or {})
            if prepare_arguments is not None:
                arguments = prepare_arguments(selected)
            try:
                result = host.execute_tool_use_case.execute(
                    ExecuteToolRequest(
                        user_id=user_id,
                        access_token=access_token,
                        tool_name=str(selected.get("name") or "execute_external_action"),
                        arguments=arguments,
                    )
                )
                return ParallelReadOutcome(index=index, result=result)
            except BaseException as exc:  # noqa: BLE001 — propaga ao pós-processo
                return ParallelReadOutcome(index=index, error=exc)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_run, index): index for index in indices}
            for future in as_completed(futures):
                outcome = future.result()
                outcomes[outcome.index] = outcome

        return outcomes
