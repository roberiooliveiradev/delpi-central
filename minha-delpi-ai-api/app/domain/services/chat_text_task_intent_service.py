"""Classifica tarefas administrativas/textuais (sem consulta ERP)."""

from __future__ import annotations

import re

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatTextTaskIntentService:
    _CATEGORY_PATTERNS: dict[str, tuple[str, ...]] = {
        "correct": (
            r"\bcorrij",
            r"\brevise\b",
            r"\bortografia\b",
            r"\barrume\s+o\s+portugu",
            r"\bgramática\b",
            r"\bgramatica\b",
        ),
        "rewrite": (
            r"\breescrev",
            r"\bmelhor(e|ar)\b",
            r"\bdeixe\s+mais\s+formal",
            r"\bmais\s+profissional",
            r"\bmais\s+educad",
            r"\bmais\s+diret",
            r"\bmais\s+simples",
        ),
        "translate": (r"\btraduza\b", r"\btraduzir\b", r"\bpasse\s+para\s+ingl", r"\bpasse\s+para\s+espan"),
        "summarize": (r"\bresuma\b", r"\bresumo\b", r"\bpontos\s+principais\b", r"\bsíntese\b", r"\bsintese\b"),
        "structure": (
            r"\bchecklist\b",
            r"\bata\b",
            r"\bem\s+tópicos\b",
            r"\bem\s+topicos\b",
            r"\blista\s+de\s+pend",
        ),
        "email": (r"\be-?mail\b", r"\bassunto\b", r"\bcobrança\b", r"\bcobranca\b"),
        "message": (r"\bwhatsapp\b", r"\bteams\b", r"\bmensagem\s+curta\b"),
        "write": (r"\bescreva\b", r"\bredija\b", r"\bmonte\b", r"\bcrie\b", r"\bgere\b", r"\belabore\b"),
        "tone_adjust": (r"\bmais\s+firme\b", r"\bmenos\s+agressiv", r"\bajuste\s+o\s+tom\b"),
        "extract_actions": (r"\bpendências\b", r"\bpendencias\b", r"\bpróximos\s+passos\b", r"\bproximos\s+passos\b"),
        "document": (r"\bcomunicado\b", r"\brelatório\b", r"\brelatorio\b", r"\bprocedimento\b"),
    }

    _OPERATIONAL_COMMAND_PATTERNS = (
        r"\bconsulte\b",
        r"\bconsultar\b",
        r"\bliste\s+produtos\b",
        r"\bqual\s+o\s+estoque\b",
        r"\bme\s+fale\s+do\s+produto\b",
        r"\bmostre\s+(o\s+)?faturamento\b",
        r"\bmostre\s+o\s+estoque\b",
        r"\bver\s+estoque\b",
        r"\bestoque\s+do\b",
        r"\bexecute\s+(a\s+)?sql\b",
        r"\bbusque\s+produto\b",
        r"\bverifique\s+o\s+estoque\b",
    )

    _MIXED_CONNECTORS = (
        " e escreva",
        " e redija",
        " e monte",
        " e gere",
        " e depois escreva",
        " e depois redija",
    )

    @classmethod
    def classify(cls, message: str | None) -> str | None:
        normalized = (message or "").strip().lower()

        if len(normalized) < 4:
            return None

        for category, patterns in cls._CATEGORY_PATTERNS.items():
            if any(re.search(pattern, normalized) for pattern in patterns):
                return category

        return None

    @classmethod
    def is_pure_text_task(
        cls,
        message: str | None,
        *,
        previous_messages: list | None = None,
    ) -> bool:
        category = cls.classify(message)

        if not category:
            return False

        if previous_messages:
            from app.domain.services.chat_analysis_intent_service import (
                ChatAnalysisIntentService,
            )

            if ChatAnalysisIntentService.is_email_from_operational_data_request(
                message,
                previous_messages,
            ):
                return False

        if cls.is_mixed_text_and_operational(message):
            return False

        normalized = (message or "").strip().lower()

        if cls._starts_with_text_lead(normalized):
            return True

        if any(re.search(pattern, normalized) for pattern in cls._OPERATIONAL_COMMAND_PATTERNS):
            return False

        if ChatProductQueryIntentService.extract_product_code(message) and category not in {
            "correct",
            "rewrite",
            "translate",
            "summarize",
        }:
            return False

        return True

    @classmethod
    def is_mixed_text_and_operational(cls, message: str | None) -> bool:
        normalized = (message or "").strip().lower()

        if not normalized:
            return False

        has_operational = any(
            re.search(pattern, normalized) for pattern in cls._OPERATIONAL_COMMAND_PATTERNS
        )

        if not has_operational:
            return False

        if any(connector in normalized for connector in cls._MIXED_CONNECTORS):
            return True

        if cls.classify(message) and not cls._starts_with_text_lead(normalized):
            return True

        return False

    @classmethod
    def _starts_with_text_lead(cls, normalized: str) -> bool:
        leads = (
            "corrija",
            "corrigir",
            "traduza",
            "traduzir",
            "resuma",
            "resumir",
            "escreva",
            "escrever",
            "redija",
            "melhore",
            "deixe",
            "revise",
        )

        return any(normalized.startswith(lead) for lead in leads)
