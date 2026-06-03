"""Detecção e resolução de contradições de memória — Playbook §32 / Fase 7."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_behavior_instruction_service import (
    ChatBehaviorInstructionService,
)


class ChatMemoryContradictionService:
    _GROUPS: tuple[tuple[str, dict[str, str]], ...] = (
        (
            "answerLength",
            {
                "short": r"\b(?:respostas?\s+curtas?|seja\s+conciso|resumo\s+curto)\b",
                "long": r"\b(?:respostas?\s+completas?|detalhad[ao]s?|aprofund)\b",
            },
        ),
        (
            "tone",
            {
                "direct": r"\b(?:seja\s+direto|resposta\s+direta|sem\s+enrola)\b",
                "simple": r"\b(?:linguagem\s+simples|explique\s+simples)\b",
                "formal": r"\b(?:tom\s+formal|sempre\s+formal)\b",
            },
        ),
        (
            "responseFormat",
            {
                "table": r"\b(?:em\s+tabela|formato\s+tabela|sempre\s+em\s+tabela)\b",
                "topics": r"\b(?:em\s+t[oó]picos|responda\s+em\s+t[oó]picos)\b",
            },
        ),
    )

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict, *, message: str | None) -> dict:
        result = dict(snapshot)
        behavior = dict(result.get("behaviorInstructions") or {})
        normalized = (message or "").strip().lower()
        detected = ChatBehaviorInstructionService.detect(message)
        superseded: list[dict[str, str]] = []

        for field, variants in cls._GROUPS:
            current = behavior.get(field) or detected.get(field)

            if not current:
                continue

            for variant_key, pattern in variants.items():
                if variant_key == current:
                    continue

                if re.search(pattern, normalized, re.IGNORECASE):
                    superseded.append(
                        {
                            "field": field,
                            "previous": str(current),
                            "replacement": variant_key,
                        }
                    )
                    behavior[field] = variant_key
                    detected[field] = variant_key

        corrections = list((result.get("conversationState") or {}).get("userCorrections") or [])

        if corrections:
            for item in corrections[-3:]:
                if isinstance(item, dict) and item.get("content"):
                    superseded.append(
                        {
                            "field": "userCorrection",
                            "previous": "inferido",
                            "replacement": str(item["content"])[:120],
                        }
                    )

        if superseded:
            existing = list(result.get("supersededMemory") or [])
            result["supersededMemory"] = (existing + superseded)[-12:]
            result["memoryContradictionResolved"] = True
            result["behaviorInstructions"] = behavior

            for entry in superseded:
                field = entry.get("field")

                if field and field != "userCorrection":
                    prefs = dict(result.get("userPreferences") or {})
                    prefs[field] = entry.get("replacement")
                    result["userPreferences"] = prefs

        return result

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        superseded = (snapshot or {}).get("supersededMemory") or []

        if not superseded:
            return None

        last = superseded[-1]

        if not isinstance(last, dict):
            return None

        field = str(last.get("field") or "")
        previous = str(last.get("previous") or "")
        replacement = str(last.get("replacement") or "")

        if field == "userCorrection":
            return (
                "Contradição resolvida: priorizar a correção recente do usuário "
                f"({replacement})."
            )

        return (
            f"Preferência atualizada: {field} passou de «{previous}» para «{replacement}» "
            "(não usar o valor antigo)."
        )

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        superseded = (snapshot or {}).get("supersededMemory") or []

        return {
            "resolved": bool((snapshot or {}).get("memoryContradictionResolved")),
            "count": len(superseded),
            "last": superseded[-1] if superseded else None,
        }
