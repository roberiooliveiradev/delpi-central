"""Extrai texto fonte e referências — playbook editor §38 (TextContextResolver)."""

from __future__ import annotations

import re
from typing import Any


class ChatTextContextResolverService:
    _PREVIOUS_REF = (
        "resposta anterior",
        "texto anterior",
        "mensagem anterior",
        "conversa acima",
        "dados acima",
        "essa conversa",
        "esta conversa",
        "histórico",
    )

    @classmethod
    def resolve(
        cls,
        message: str | None,
        *,
        previous_messages: list | None = None,
    ) -> dict[str, Any]:
        raw = (message or "").strip()
        normalized = raw.lower()

        extracted = cls._extract_inline_text(raw)
        references_previous = any(ref in normalized for ref in cls._PREVIOUS_REF)
        references_canvas = "lousa" in normalized or "canvas" in normalized
        references_attachment = any(
            token in normalized for token in ("anexo", "arquivo", "pdf", "documento anex")
        )

        prior_snippet = None

        if references_previous and previous_messages:
            prior_snippet = cls._latest_assistant_snippet(previous_messages)

        return {
            "hasInlineText": bool(extracted),
            "inlineText": extracted,
            "referencesPrevious": references_previous,
            "referencesCanvas": references_canvas,
            "referencesAttachment": references_attachment,
            "priorSnippet": prior_snippet,
        }

    @classmethod
    def format_prompt_block(cls, context: dict[str, Any] | None) -> str | None:
        if not isinstance(context, dict):
            return None

        lines: list[str] = []

        if context.get("inlineText"):
            snippet = str(context["inlineText"]).strip()

            if len(snippet) > 4000:
                snippet = snippet[:4000] + "…"

            lines.append(f"- Texto fonte na mensagem: «{snippet}»")

        if context.get("priorSnippet") and context.get("referencesPrevious"):
            prior = str(context["priorSnippet"]).strip()

            if len(prior) > 2000:
                prior = prior[:2000] + "…"

            lines.append(f"- Use como base a resposta anterior: «{prior}»")

        if context.get("referencesCanvas"):
            lines.append("- Fonte: conteúdo da lousa ativa (se disponível no histórico).")

        if context.get("referencesAttachment"):
            lines.append("- Fonte: arquivo(s) anexados neste turno.")

        if not lines:
            return None

        return "\n".join(lines)

    @classmethod
    def _extract_inline_text(cls, message: str) -> str | None:
        if not message.strip():
            return None

        colon_match = re.search(
            r"(?:corrija|revise|traduza|resuma|reescreva|melhore|deixe|explique|simplifique)\s*:\s*(.+)",
            message,
            re.IGNORECASE | re.DOTALL,
        )

        if colon_match:
            return colon_match.group(1).strip()

        below_match = re.search(
            r"(?:texto\s+ab(?:aixo|aixo)|abaixo)\s*:?\s*\n+([\s\S]+)",
            message,
            re.IGNORECASE,
        )

        if below_match:
            return below_match.group(1).strip()

        quoted = re.findall(r"«([^»]+)»|\"([^\"]+)\"|'([^']+)'", message)

        for groups in quoted:
            for value in groups:
                if value and len(value.strip()) > 12:
                    return value.strip()

        return None

    @classmethod
    def _latest_assistant_snippet(cls, previous_messages: list) -> str | None:
        for msg in reversed(previous_messages or []):
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else None)

            if role != "assistant":
                continue

            content = getattr(msg, "content", None) or (
                msg.get("content") if isinstance(msg, dict) else None
            )

            if isinstance(content, str) and content.strip():
                return content.strip()

        return None
