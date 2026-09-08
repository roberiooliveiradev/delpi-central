"""Decomposição OpenAPI-first de pedidos compostos em subtarefas independentes."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.openapi_tool_routing_content_service import (
    OpenApiToolRoutingContentService,
)


@dataclass(frozen=True)
class ExternalActionSubtask:
    text: str
    index: int


class DecomposeExternalActionRequestsService:
    """Parte mensagens longas em subtarefas sem ensinar endpoint/domínio.

    Joiners, listas numeradas, compoundSignals (domínio) e limites vêm de
    ``openapi_tool_routing.json`` (assistant content).

    ``presentationCompoundSignals`` ("tudo na mesma resposta") NÃO forçam
    multi-action — só afetam apresentação/stack.
    """

    @classmethod
    def wants_multi_action(cls, message: str | None) -> bool:
        """True quando há ≥2 subtarefas de domínio ou signal declarativo de domínio composto.

        Sinais só de apresentação (`presentationCompoundSignals`) não contam.
        """
        text = str(message or "").strip()
        if not text:
            return False

        if len(cls.decompose(text)) > 1:
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(text)
        for signal in OpenApiToolRoutingContentService.list_setting(
            "decomposition",
            "compoundSignals",
        ):
            marker = ChatMessageNormalizationService.normalize_for_matching(signal)
            if marker and marker in normalized:
                return True

        return False

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
        min_chars = OpenApiToolRoutingContentService.int_setting(
            "decomposition",
            "minSubtaskChars",
            default=12,
        )

        numbered = cls._split_numbered_list(text)
        if len(numbered) > 1:
            return cls._to_subtasks(numbered, max_subtasks=max_subtasks)

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

        merged = cls._merge_short_tails(parts, min_chars=min_chars)
        return cls._to_subtasks(merged, max_subtasks=max_subtasks)

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
    def _merge_short_tails(cls, parts: list[str], *, min_chars: int) -> list[str]:
        merged: list[str] = []
        for part in parts:
            if merged and len(part) < min_chars:
                merged[-1] = f"{merged[-1]} {part}".strip()
            else:
                merged.append(part)
        return merged

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
