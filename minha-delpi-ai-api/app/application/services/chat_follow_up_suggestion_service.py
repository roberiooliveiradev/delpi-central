"""Sugestões contextuais de próximo passo (chips) — Fase 3 do playbook."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_agent_personality_service import ChatAgentPersonalityService
from app.domain.services.chat_agent_profile_service import ChatAgentProfileService
from app.infrastructure.content.content_service import ContentService

_PRODUCT_CODE_RE = re.compile(r"\b(\d{5,9})\b")


@lru_cache(maxsize=1)
def _playbook() -> dict[str, Any]:
    return ContentService.personality_playbook()


class ChatFollowUpSuggestionService:
    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        message: str,
        answer: str,
        tool_calls: list | None,
        workspace_context: dict | None,
        issues: list[str] | None = None,
    ) -> None:
        profile = ChatAgentProfileService.from_workspace(workspace_context)
        personality = ChatAgentPersonalityService.from_profile(profile)

        if not personality.suggest_follow_ups:
            return

        suggestions = cls.build(
            message=message,
            answer=answer,
            tool_calls=tool_calls or [],
            issues=issues,
            workspace_context=workspace_context,
        )

        if suggestions:
            metadata["followUpSuggestions"] = suggestions
            metadata["followUpOutcome"] = cls.classify_outcome(
                answer=answer,
                tool_calls=tool_calls or [],
                issues=issues,
            )

    @classmethod
    def build(
        cls,
        *,
        message: str,
        answer: str,
        tool_calls: list,
        issues: list[str] | None = None,
        workspace_context: dict | None = None,
    ) -> list[dict[str, str]]:
        outcome = cls.classify_outcome(
            answer=answer,
            tool_calls=tool_calls,
            issues=issues,
        )
        chips = cls._chip_labels(outcome)

        if not chips:
            return []

        product_code = cls._resolve_product_code(
            message=message,
            answer=answer,
            tool_calls=tool_calls,
            workspace_context=workspace_context,
        )
        query_map = _playbook().get("followUpQueries") or {}

        suggestions: list[dict[str, str]] = []

        for label in chips[:6]:
            template = str(query_map.get(label) or label).strip()

            if not template:
                continue

            query = template

            if product_code:
                query = query.replace("{product_code}", product_code)

            suggestions.append({"label": label, "query": query})

        return suggestions

    @classmethod
    def classify_outcome(
        cls,
        *,
        answer: str,
        tool_calls: list,
        issues: list[str] | None = None,
    ) -> str:
        if issues:
            return "error"

        lowered = str(answer or "").lower()

        if cls._looks_like_empty(lowered):
            return "empty"

        if cls._looks_like_warning(lowered):
            return "warning"

        paths = " ".join(
            str((call or {}).get("path") or (call or {}).get("metadata", {}).get("path") or "")
            for call in tool_calls
            if isinstance(call, dict)
        ).lower()

        if any(token in paths for token in ("/stock", "estoque", "supplies/stock")):
            return "stock"

        if any(token in paths for token in ("/sales", "/billing", "vendas", "faturamento")):
            return "sales"

        if any(
            token in paths
            for token in (
                "/products/",
                "structure",
                "estrutura",
                "analyser",
                "fornecedor",
                "supplier",
            )
        ) or any(token in lowered for token in ("produto", "estrutura", "fornecedor")):
            return "product"

        return "generic"

    @classmethod
    def assess_risk_level(
        cls,
        *,
        answer: str,
        tool_calls: list,
        issues: list[str] | None = None,
    ) -> int:
        if issues:
            return 3

        outcome = cls.classify_outcome(
            answer=answer,
            tool_calls=tool_calls,
            issues=issues,
        )

        if outcome == "error":
            return 3

        if outcome in {"empty", "warning"}:
            return 2

        if outcome == "generic":
            return 1

        return 0

    @classmethod
    def _chip_labels(cls, outcome: str) -> list[str]:
        chips = (_playbook().get("followUpChips") or {}).get(outcome) or []

        if chips:
            return [str(item).strip() for item in chips if str(item).strip()]

        generic = (_playbook().get("followUpChips") or {}).get("generic") or []

        return [str(item).strip() for item in generic if str(item).strip()]

    @classmethod
    def _resolve_product_code(
        cls,
        *,
        message: str,
        answer: str,
        tool_calls: list,
        workspace_context: dict | None,
    ) -> str | None:
        for source in (message, answer):
            match = _PRODUCT_CODE_RE.search(str(source or ""))

            if match:
                return match.group(1)

        for call in tool_calls:
            if not isinstance(call, dict):
                continue

            path = str(call.get("path") or call.get("metadata", {}).get("path") or "")
            match = _PRODUCT_CODE_RE.search(path)

            if match:
                return match.group(1)

        context = workspace_context or {}
        conversation = context.get("conversationContext") or {}

        if isinstance(conversation, dict):
            code = conversation.get("lastProductCode") or conversation.get("productCode")

            if code:
                return str(code).strip()

        return None

    @staticmethod
    def _looks_like_empty(lowered: str) -> bool:
        markers = (
            "não encontrei",
            "nao encontrei",
            "não retornou",
            "nao retornou",
            "sem registros",
            "nenhum registro",
            "não achei",
            "nao achei",
        )

        return any(marker in lowered for marker in markers)

    @staticmethod
    def _looks_like_warning(lowered: str) -> bool:
        markers = (
            "atenção",
            "atencao",
            "risco",
            "divergência",
            "divergencia",
            "validação",
            "validacao",
        )

        return any(marker in lowered for marker in markers)
