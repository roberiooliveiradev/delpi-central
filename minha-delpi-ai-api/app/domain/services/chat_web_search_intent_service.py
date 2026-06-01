"""Heurísticas e disponibilidade da tool interna web_search."""

from __future__ import annotations

import re

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.web_search_query_service import WebSearchQueryService
from app.infrastructure.config.settings import Settings


class ChatWebSearchIntentService:
    _TRIGGER_TERMS = (
        "pesquise na internet",
        "pesquisa na internet",
        "busque na internet",
        "busca na internet",
        "pesquisa profunda na web",
        "pesquisa profunda na internet",
        "busca profunda na web",
        "busca profunda na internet",
        "pesquise na web",
        "pesquisa na web",
        "busque na web",
        "busca na web",
        "pesquise online",
        "pesquisa online",
        "google",
        "duckduckgo",
        "na internet sobre",
        "web sobre",
    )

    _STRIP_PATTERNS = (
        r"^(?:por favor[, ]*)?",
        r"^(?:me )?",
        r"^(?:pode )?",
        r"^(?:voce |você )?",
        r"(?:pesquise|pesquisa|busque|busca)(?: na internet| na web| online)?(?: sobre| por)?",
        r"(?:na internet|na web|online)",
        r"(?:sobre|por)\s+(?:a\s+)?(?:empresa|companhia)\s+",
        r"(?:sobre|por)\s+",
        r"^(?:a\s+)?(?:empresa|companhia)\s+",
    )

    @classmethod
    def is_feature_enabled(cls) -> bool:
        if not Settings.CHAT_WEB_SEARCH_ENABLED:
            return False

        from app.application.services.chat_intelligence_settings_service import (
            ChatIntelligenceSettingsService,
        )

        resolved = ChatIntelligenceSettingsService().resolve()
        return bool(resolved.web_search_enabled)

    @classmethod
    def matches(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        return bool(normalized) and any(term in normalized for term in cls._TRIGGER_TERMS)

    @classmethod
    def blocks_external_action_selection(cls, message: str) -> bool:
        """Busca explícita na web não dispara actions OpenAPI no mesmo turno."""
        raw = str(message or "").strip()

        if not cls.matches(raw):
            return False

        if not cls.is_feature_enabled():
            return True

        from app.domain.services.chat_web_search_integration_service import (
            ChatWebSearchIntegrationService,
        )

        if ChatWebSearchIntegrationService.should_allow_operational_companion(raw):
            return False

        return True

    @classmethod
    def format_disabled_notice(cls, message: str | None = None) -> str:
        query = cls.extract_query(message or "") if message else ""

        detail = (
            f" Consulta identificada: **{query}**." if query else ""
        )

        return (
            "A **pesquisa na web** não está habilitada neste ambiente "
            "(configure `CHAT_WEB_SEARCH_ENABLED=true` e um provedor, por exemplo SearXNG).\n\n"
            "Não usei busca de produtos no ERP para esta pergunta — ela pedia fontes públicas na internet."
            f"{detail}"
        )

    @classmethod
    def resolve(
        cls,
        message: str,
        *,
        attachment_context: str | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        if not cls.is_feature_enabled():
            return None

        raw = str(message or "").strip()

        if not raw or not cls.matches(raw):
            return None

        from app.domain.services.chat_web_search_planning_service import (
            ChatWebSearchPlanningService,
        )

        from app.domain.services.chat_web_search_integration_service import (
            ChatWebSearchIntegrationService,
        )

        integration = ChatWebSearchIntegrationService.resolve(
            raw,
            attachment_context=attachment_context,
            previous_messages=previous_messages,
        )
        plan = ChatWebSearchPlanningService.plan(raw, integration=integration)

        if not plan:
            return None

        reason = "A pergunta solicita informação pública na internet."

        if plan.prefer_official:
            reason = "A pergunta solicita informação pública com preferência por fontes oficiais."

        if plan.mode == "deep":
            reason = (
                f"{reason} Modo de pesquisa profunda "
                f"({len(plan.queries)} consulta(s) planejada(s))."
            )

        if integration:
            if integration.mode == "internal_product":
                reason = (
                    f"{reason} Integração com consulta interna do produto "
                    f"{integration.product_code or 'informado'}."
                )
            elif integration.mode == "attachment_compare":
                reason = f"{reason} Integração com anexo para comparação de fontes."
            elif integration.mode == "source_compare":
                reason = f"{reason} Comparação explícita entre fontes."
            elif integration.mode == "technical_table":
                reason = f"{reason} Resposta técnica com tabela comparativa."

        arguments: dict = {
            "query": plan.primary_query(),
            "plannedQueries": list(plan.queries),
            "limit": plan.max_results,
            "searchMode": plan.mode,
            "searchIntent": plan.intent,
            "preferOfficial": plan.prefer_official,
        }

        if integration:
            arguments["integrationMode"] = integration.mode

            if integration.product_code:
                arguments["integrationProductCode"] = integration.product_code

            if integration.attachment_label:
                arguments["integrationAttachment"] = integration.attachment_label

            if integration.synthesis_note:
                arguments["integrationSynthesisNote"] = integration.synthesis_note

        return {
            "name": "web_search",
            "arguments": arguments,
            "reason": reason,
        }

    @classmethod
    def extract_query(cls, message: str) -> str:
        query = str(message or "").strip()
        normalized = ChatMessageNormalizationService.normalize_for_matching(query) or query

        for pattern in cls._STRIP_PATTERNS:
            normalized = re.sub(pattern, " ", normalized, flags=re.IGNORECASE).strip()

        normalized = re.sub(r"\s+", " ", normalized).strip(" ?.")

        sanitized = WebSearchQueryService.sanitize_query(normalized)

        return sanitized or normalized or query
