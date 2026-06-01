"""Padrões SQL avançados (CTE, window) — Playbook §25–31."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatSqlQueryPatternAdvisorService:
    _PATTERNS: tuple[tuple[tuple[str, ...], str, str], ...] = (
        (
            ("compar", "periodo", "período", "mes anterior", "mês anterior", "ano anterior"),
            "period_compare_cte",
            "Use CTEs para isolar período atual e anterior antes do JOIN final.",
        ),
        (
            ("ranking", "top ", "maior", "menor", "por categoria"),
            "window_rank",
            "Use ROW_NUMBER() ou RANK() OVER (PARTITION BY ... ORDER BY ...) para ranking.",
        ),
        (
            ("ultimo registro", "último registro", "mais recente por", "deduplic"),
            "window_dedup",
            "Use ROW_NUMBER() OVER (PARTITION BY chave ORDER BY data DESC) = 1 para deduplicar.",
        ),
        (
            ("variacao", "variação", "percentual", "%"),
            "percent_change",
            "Calcule variação com NULLIF no denominador para evitar divisão por zero.",
        ),
        (
            ("pivot", "cruzad", "matriz"),
            "conditional_agg",
            "Para pivot simples, use SUM(CASE WHEN ...) GROUP BY dimensão.",
        ),
        (
            ("coorte", "cohort"),
            "cohort_cte",
            "Monte coorte em CTE base e agregue retenção/conversão em etapa seguinte.",
        ),
    )

    @classmethod
    def recommend(cls, message: str | None) -> dict[str, Any]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        patterns: list[dict[str, str]] = []
        hints: list[str] = []

        if not normalized:
            return {"patterns": patterns, "hints": hints}

        for triggers, code, guidance in cls._PATTERNS:
            if any(trigger in normalized for trigger in triggers):
                patterns.append({"code": code, "guidance": guidance})
                hints.append(code)

        return {"patterns": patterns, "hints": hints}
