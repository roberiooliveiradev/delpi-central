"""Sugestões contextuais de próximo passo (chips) — Fase 3 do playbook."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_agent_personality_service import ChatAgentPersonalityService
from app.domain.services.chat_agent_profile_service import ChatAgentProfileService
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntentService
from app.domain.services.chat_working_memory_service import ChatWorkingMemoryService
from app.infrastructure.content.content_service import ContentService

_PRODUCT_CODE_RE = re.compile(r"\b(\d{5,9})\b")
_PRODUCT_PLACEHOLDER = "{product_code}"
_MFE_PRODUCT_PLACEHOLDER = "{{productCode}}"
_MFE_SEARCH_PLACEHOLDER = "{{searchQuery}}"


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
        previous_messages: list[Any] | None = None,
    ) -> None:
        profile = ChatAgentProfileService.from_workspace(workspace_context)
        personality = ChatAgentPersonalityService.from_profile(profile)

        if not personality.suggest_follow_ups:
            return

        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        if ChatSqlIntentService.is_sql_conversation_turn(message):
            return

        suggestions = cls.build(
            message=message,
            answer=answer,
            tool_calls=tool_calls or [],
            issues=issues,
            workspace_context=workspace_context,
            previous_messages=previous_messages,
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
        previous_messages: list[Any] | None = None,
    ) -> list[dict[str, str]]:
        if (workspace_context or {}).get("textTaskCategory") and not tool_calls:
            outcome = "text"
        else:
            outcome = cls.classify_outcome(
                answer=answer,
                tool_calls=tool_calls,
                issues=issues,
            )
        chips = cls._chip_labels(outcome)

        if not chips:
            return []

        if not cls._operational_actions_ready(workspace_context, outcome):
            return []

        query_map = _playbook().get("followUpQueries") or {}

        suggestions: list[dict[str, str]] = []

        for label in chips[:6]:
            template = str(query_map.get(label) or label).strip()

            if not template:
                continue

            query = cls._template_query(template)

            if not query:
                continue

            suggestions.append({"label": label, "query": query})

        return suggestions

    @classmethod
    def _template_query(cls, template: str) -> str | None:
        """Retorna template com placeholders MFE — preenchimento no clique (sem código fixo)."""
        query = (
            template.replace(_PRODUCT_PLACEHOLDER, _MFE_PRODUCT_PLACEHOLDER)
            .replace("{query}", _MFE_SEARCH_PLACEHOLDER)
            .replace("{topic}", _MFE_SEARCH_PLACEHOLDER)
            .strip()
        )

        return query or None

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

        if any(
            token in paths
            for token in ("/system/tables", "/columns", "/schema", "/relations")
        ) or any(
            isinstance(call, dict)
            and (call.get("metadata") or {}).get("sqlSchemaPrefetch")
            for call in tool_calls
        ):
            return "sql"

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
                "parents",
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
    def _operational_actions_ready(
        cls,
        workspace_context: dict | None,
        outcome: str,
    ) -> bool:
        if outcome == "text":
            return True

        context = workspace_context or {}

        if outcome in {"generic", "empty", "error"}:
            return True

        if outcome in {"product", "stock", "sales", "warning"}:
            return bool(context.get("userActivatedAgent"))

        return bool(context.get("userActivatedAgent") or context.get("actionsEnabled"))

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
        previous_messages: list[Any] | None = None,
    ) -> str | None:
        working_memory = (workspace_context or {}).get("workingMemory") or {}
        entities = working_memory.get("operationalFocus") or {}
        memory_code = str(entities.get("productCode") or "").strip()

        if memory_code:
            normalized = ChatProductQueryIntentService.normalize_product_code(memory_code)

            if ChatProductQueryIntentService.is_plausible_product_code(normalized):
                return normalized

        for code in ChatWorkingMemoryService._extract_codes_from_tool_calls(tool_calls):
            normalized = ChatProductQueryIntentService.normalize_product_code(code)

            if ChatProductQueryIntentService.is_plausible_product_code(normalized):
                return normalized

        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            args = call.get("arguments")

            if isinstance(args, dict):
                parameters = args.get("parameters")

                if isinstance(parameters, dict):
                    raw_code = parameters.get("code")

                    if raw_code not in (None, ""):
                        normalized = ChatProductQueryIntentService.normalize_product_code(
                            str(raw_code),
                        )

                        if ChatProductQueryIntentService.is_plausible_product_code(normalized):
                            return normalized

            metadata = call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            path = str(metadata.get("path") or "")
            code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

            if code:
                return code

            humanized = metadata.get("humanizedSummary")

            if isinstance(humanized, dict):
                title = str(humanized.get("titulo") or "")
                code = ChatProductQueryIntentService.extract_product_code(title)

                if code:
                    return code

        code = ChatProductQueryIntentService.extract_product_code(message)

        if code:
            return code

        code = ChatProductQueryIntentService.extract_last_product_code(answer)

        if code:
            return code

        if previous_messages:
            code = ChatProductQueryIntentService.extract_last_product_code_from_messages(
                previous_messages,
            )

            if code:
                return code

        context = workspace_context or {}
        conversation = context.get("conversationContext") or {}

        if isinstance(conversation, dict):
            for key in ("lastProductCode", "productCode"):
                raw = conversation.get(key)

                if raw:
                    normalized = ChatProductQueryIntentService.normalize_product_code(str(raw))

                    if ChatProductQueryIntentService.is_plausible_product_code(normalized):
                        return normalized

        for source in (message, answer):
            match = _PRODUCT_CODE_RE.search(str(source or ""))

            if match:
                normalized = ChatProductQueryIntentService.normalize_product_code(match.group(1))

                if ChatProductQueryIntentService.is_plausible_product_code(normalized):
                    return normalized

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
