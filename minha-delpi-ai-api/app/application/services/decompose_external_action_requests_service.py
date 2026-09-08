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
    """Parte mensagens longas em subtarefas sem ensinar endpoint/domínio.

    Joiners e limites vêm de ``openapi_tool_routing.json`` (assistant content).
    """

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
        joiners = OpenApiToolRoutingContentService.list_setting(
            "decomposition",
            "joiners",
        )
        if not joiners:
            return [ExternalActionSubtask(text=text, index=0)]

        pattern = "|".join(
            re.escape(str(item).strip())
            for item in joiners
            if str(item).strip()
        )
        if not pattern:
            return [ExternalActionSubtask(text=text, index=0)]

        parts = [
            part.strip(" ,.;")
            for part in re.split(f"(?:{pattern})", text, flags=re.IGNORECASE)
            if part and part.strip(" ,.;")
        ]
        if len(parts) <= 1:
            return [ExternalActionSubtask(text=text, index=0)]

        # Keep short tails attached to previous when they look like synthesis-only.
        min_chars = OpenApiToolRoutingContentService.int_setting(
            "decomposition",
            "minSubtaskChars",
            default=12,
        )
        merged: list[str] = []
        for part in parts:
            if merged and len(part) < min_chars:
                merged[-1] = f"{merged[-1]} {part}".strip()
            else:
                merged.append(part)

        return [
            ExternalActionSubtask(text=item, index=index)
            for index, item in enumerate(merged[: max(1, max_subtasks)])
        ]
