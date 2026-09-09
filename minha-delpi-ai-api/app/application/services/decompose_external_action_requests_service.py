"""Decomposição OpenAPI-first de pedidos compostos em subtarefas independentes."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)


@dataclass(frozen=True)
class ExternalActionSubtask:
    text: str
    index: int


class DecomposeExternalActionRequestsService:
    """Parte listas numeradas em subtarefas sem ensinar endpoint/domínio.

    Joiners PT e compoundSignals não são gate de seleção — o planner LLM
    decide N steps. ``presentationCompoundSignals`` só afetam apresentação.
    """

    @classmethod
    def wants_multi_action(cls, message: str | None) -> bool:
        """True quando a mensagem tem ≥2 subtarefas numeradas."""
        text = str(message or "").strip()
        if not text:
            return False
        return len(cls.decompose(text)) > 1

    @classmethod
    def decompose(cls, message: str) -> list[ExternalActionSubtask]:
        text = str(message or "").strip()
        if not text:
            return []

        max_subtasks = OpenApiToolRoutingContentService.int_setting(
            "decomposition",
            "maxSubtasks",
            default=4,
        )

        numbered = cls._split_numbered_list(text)
        if len(numbered) > 1:
            return cls._to_subtasks(numbered, max_subtasks=max_subtasks)

        return [ExternalActionSubtask(text=text, index=0)]

    @classmethod
    def _split_numbered_list(cls, text: str) -> list[str]:
        pattern = str(
            OpenApiToolRoutingContentService.get(
                "decomposition",
                "numberedListPattern",
                default="",
            )
            or ""
        ).strip()
        if not pattern:
            return []

        try:
            compiled = re.compile(pattern, flags=re.IGNORECASE)
        except re.error:
            return []

        matches = list(compiled.finditer(text))
        if len(matches) < 2:
            return []

        prefix = text[: matches[0].start()].strip(" ,.;:")
        parts: list[str] = []
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            body = text[match.end() : end].strip(" ,.;:")
            if not body:
                continue
            parts.append(f"{prefix} {body}".strip() if prefix else body)

        return parts if len(parts) >= 2 else []

    @classmethod
    def _to_subtasks(
        cls,
        parts: list[str],
        *,
        max_subtasks: int,
    ) -> list[ExternalActionSubtask]:
        return [
            ExternalActionSubtask(text=item, index=index)
            for index, item in enumerate(parts[: max(1, max_subtasks)])
        ]
