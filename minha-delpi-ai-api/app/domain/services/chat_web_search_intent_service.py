"""Heurísticas e disponibilidade da tool interna web_search."""

from __future__ import annotations

import re
from functools import lru_cache

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_web_search_query_security_service import (
    ChatWebSearchQuerySecurityService,
)
from app.domain.services.web_search_query_service import WebSearchQueryService
from app.domain.services.chat_domain_config_service import ChatDomainConfigService
from app.domain.services.chat_runtime_intelligence_settings_service import (
    ChatRuntimeIntelligenceSettingsService,
)


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
        if not ChatDomainConfigService.chat_web_search_enabled():
            return False

        return ChatRuntimeIntelligenceSettingsService.web_search_enabled()

    @classmethod
    def is_auto_augment_enabled(cls) -> bool:
        return ChatDomainConfigService.chat_web_search_auto_augment_enabled()

    @classmethod
    def is_explicit_request(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        return bool(normalized) and any(term in normalized for term in cls._TRIGGER_TERMS)

    @classmethod
    def matches(cls, message: str) -> bool:
        return cls.should_use_web_research(message)

    @classmethod
    def is_web_search_plan_eligible(cls, message: str, *, trigger_mode: str = "default") -> bool:
        if trigger_mode == "post_rag_fallback":
            return cls.should_try_web_after_empty_rag(message)

        return cls.matches(message)

    @classmethod
    def should_use_web_research(cls, message: str) -> bool:
        raw = str(message or "").strip()

        if not raw:
            return False

        if cls.is_explicit_request(raw):
            return True

        if cls.should_use_web_for_public_facts(raw):
            return True

        return cls.should_augment_with_web(raw)

    @classmethod
    def should_use_web_for_public_facts(cls, message: str) -> bool:
        if not cls.is_feature_enabled():
            return False

        raw = str(message or "").strip()

        if not raw or cls.is_explicit_request(raw):
            return False

        if cls._is_excluded_from_auto_augment(raw):
            return False

        config = _public_facts_content()
        max_length = int(config.get("maxMessageLength") or 200)
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)

        if len(normalized) > max_length:
            return False

        trigger_terms = tuple(str(item) for item in (config.get("triggerTerms") or ()))

        if not trigger_terms:
            return False

        if not ChatMessageNormalizationService.contains_any(normalized, trigger_terms):
            return False

        exclude_terms = tuple(str(item) for item in (config.get("excludeTerms") or ()))

        if exclude_terms and ChatMessageNormalizationService.contains_any(
            normalized, exclude_terms
        ):
            return False

        return True

    @classmethod
    def should_try_web_after_empty_rag(cls, message: str) -> bool:
        """Pergunta factual externa que não disparou web no pré-tool — tentar após RAG vazio."""
        if not cls.is_feature_enabled():
            return False

        raw = str(message or "").strip()

        if not raw or cls.is_explicit_request(raw):
            return False

        if cls.should_use_web_research(raw):
            return False

        if cls._is_excluded_from_auto_augment(raw):
            return False

        config = _post_rag_fallback_content()
        max_length = int(config.get("maxMessageLength") or 280)
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)

        if len(normalized) > max_length:
            return False

        exclude_terms = tuple(str(item) for item in (config.get("excludeTerms") or ()))

        if exclude_terms and ChatMessageNormalizationService.contains_any(
            normalized, exclude_terms
        ):
            return False

        question_starters = tuple(str(item) for item in (config.get("questionStarters") or ()))

        if question_starters and any(
            normalized.startswith(str(starter).strip().lower())
            for starter in question_starters
            if str(starter).strip()
        ):
            return True

        trigger_terms = tuple(str(item) for item in (config.get("triggerTerms") or ()))

        return bool(
            trigger_terms
            and ChatMessageNormalizationService.contains_any(normalized, trigger_terms)
        )

    @classmethod
    def should_augment_with_web(cls, message: str) -> bool:
        if not cls.is_feature_enabled() or not cls.is_auto_augment_enabled():
            return False

        raw = str(message or "").strip()

        if not raw or cls.is_explicit_request(raw):
            return False

        if cls._is_excluded_from_auto_augment(raw):
            return False

        config = _augmentation_content()
        max_length = int(config.get("maxMessageLength") or 320)
        normalized = ChatMessageNormalizationService.normalize_for_matching(raw)

        if len(normalized) > max_length:
            return False

        trigger_terms = tuple(str(item) for item in (config.get("triggerTerms") or ()))

        if not ChatMessageNormalizationService.contains_any(normalized, trigger_terms):
            return False

        min_topic_length = int(config.get("minTopicLength") or 4)
        topic = cls._extract_augment_topic(raw)

        return len(topic) >= min_topic_length

    @classmethod
    def blocks_external_action_selection(cls, message: str) -> bool:
        """Busca na web (explícita ou auto-augmentada) não dispara actions OpenAPI no mesmo turno."""
        raw = str(message or "").strip()

        if not cls.should_use_web_research(raw):
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
    def resolve_for_post_rag_fallback(
        cls,
        message: str,
        *,
        attachment_context: str | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        return cls._resolve_web_search(
            message,
            attachment_context=attachment_context,
            previous_messages=previous_messages,
            trigger_mode="post_rag_fallback",
        )

    @classmethod
    def resolve(
        cls,
        message: str,
        *,
        attachment_context: str | None = None,
        previous_messages: list | None = None,
    ) -> dict | None:
        return cls._resolve_web_search(
            message,
            attachment_context=attachment_context,
            previous_messages=previous_messages,
            trigger_mode="default",
        )

    @classmethod
    def _resolve_web_search(
        cls,
        message: str,
        *,
        attachment_context: str | None = None,
        previous_messages: list | None = None,
        trigger_mode: str = "default",
    ) -> dict | None:
        if not cls.is_feature_enabled():
            return None

        raw = str(message or "").strip()

        if not raw:
            return None

        if trigger_mode == "post_rag_fallback":
            if not cls.should_try_web_after_empty_rag(raw):
                return None
        elif not cls.should_use_web_research(raw):
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
        security = ChatWebSearchQuerySecurityService.sanitize(
            raw,
            extracted_query=ChatWebSearchIntentService.extract_query(raw),
        )

        if security.blocked:
            return None

        plan = ChatWebSearchPlanningService.plan(
            raw,
            integration=integration,
            base_query_override=security.query if security.redacted else None,
            trigger_mode=trigger_mode,
        )

        if not plan:
            return None

        if trigger_mode == "post_rag_fallback" and not cls.is_explicit_request(raw):
            reason = str(
                _post_rag_fallback_content().get("searchReason")
                or "A base interna não trouxe trechos — busco na internet."
            )
        elif cls.should_use_web_for_public_facts(raw) and not cls.is_explicit_request(raw):
            reason = str(
                _public_facts_content().get("searchReason")
                or "A pergunta pede informação pública atual na internet."
            )
        elif cls.should_augment_with_web(raw) and not cls.is_explicit_request(raw):
            reason = str(
                _augmentation_content().get("augmentReason")
                or (
                    "A pergunta pede contexto público atual — combino conhecimento interno "
                    "com pesquisa na web para maior assertividade."
                )
            )
        elif plan.prefer_official:
            reason = "A pergunta solicita informação pública com preferência por fontes oficiais."
        else:
            reason = "A pergunta solicita informação pública na internet."

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

        if security.redacted or security.warnings:
            arguments["querySecurity"] = {
                "redacted": security.redacted,
                "warnings": list(security.warnings),
            }

        if integration:
            arguments["integrationMode"] = integration.mode

            if integration.product_code:
                arguments["integrationProductCode"] = integration.product_code

            if integration.attachment_label:
                arguments["integrationAttachment"] = integration.attachment_label

            if integration.synthesis_note:
                arguments["integrationSynthesisNote"] = integration.synthesis_note

        if trigger_mode == "post_rag_fallback" and not cls.is_explicit_request(raw):
            arguments["searchTrigger"] = "post_rag_fallback"
        elif cls.should_use_web_for_public_facts(raw) and not cls.is_explicit_request(raw):
            arguments["searchTrigger"] = "public_fact"
        elif cls.should_augment_with_web(raw) and not cls.is_explicit_request(raw):
            arguments["searchTrigger"] = "auto_augment"

        return {
            "name": "web_search",
            "arguments": arguments,
            "reason": reason,
        }

    @classmethod
    def extract_query(cls, message: str) -> str:
        query = str(message or "").strip()
        normalized = ChatMessageNormalizationService.normalize_for_matching(query) or query

        if cls.should_try_web_after_empty_rag(query) and not cls.is_explicit_request(query):
            if not cls.should_use_web_research(query):
                normalized = cls._extract_post_rag_fallback_query(query)
            else:
                normalized = cls._extract_public_fact_query(query)
        elif cls.should_use_web_for_public_facts(query) and not cls.is_explicit_request(query):
            normalized = cls._extract_public_fact_query(query)
        elif cls.should_augment_with_web(query) and not cls.is_explicit_request(query):
            normalized = cls._extract_augment_topic(query)
        else:
            for pattern in cls._STRIP_PATTERNS:
                normalized = re.sub(pattern, " ", normalized, flags=re.IGNORECASE).strip()

        normalized = re.sub(r"\s+", " ", normalized).strip(" ?.")

        sanitized = WebSearchQueryService.sanitize_query(normalized)
        base = sanitized or normalized or query
        security = ChatWebSearchQuerySecurityService.sanitize(query, extracted_query=base)

        if security.blocked:
            return base

        return security.query or base

    @staticmethod
    def _join_query_suffix(normalized: str, suffix_raw: str) -> str:
        base = re.sub(r"\s+", " ", str(normalized or "")).strip(" ?.")
        suffix = re.sub(r"\s+", " ", str(suffix_raw or "")).strip()

        if not base:
            return suffix

        if not suffix:
            return base

        return f"{base} {suffix}"

    @classmethod
    def _extract_post_rag_fallback_query(cls, message: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""
        normalized = re.sub(r"\s+", " ", normalized).strip(" ?.")
        suffix = str(_post_rag_fallback_content().get("querySuffix") or "")

        return cls._join_query_suffix(normalized, suffix)

    @classmethod
    def _extract_public_fact_query(cls, message: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""
        normalized = re.sub(r"\s+", " ", normalized).strip(" ?.")
        suffix = str(_public_facts_content().get("querySuffix") or "")

        return cls._join_query_suffix(normalized, suffix)

    @classmethod
    def _extract_augment_topic(cls, message: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        for pattern in _augmentation_content().get("stripPatterns") or ():
            normalized = re.sub(
                str(pattern),
                " ",
                normalized,
                flags=re.IGNORECASE,
            ).strip()

        normalized = re.sub(r"\s+", " ", normalized).strip(" ?.")
        suffix = str(_augmentation_content().get("querySuffix") or "")

        return cls._join_query_suffix(normalized, suffix)

    @classmethod
    def _is_excluded_from_auto_augment(cls, message: str) -> bool:
        from app.domain.services.chat_intent_router_service import ChatIntentRouterService
        from app.domain.services.chat_small_talk_pattern_service import (
            ChatSmallTalkPatternService,
        )
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
        from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

        if ChatIntentRouterService._blocks_web_search(message):
            return True

        if ChatSmallTalkPatternService.is_small_talk(message):
            return True

        if ChatTextTaskIntentService.is_pure_text_task(message):
            return True

        if ChatSqlIntentService.is_sql_conversation_turn(message):
            return True

        if cls._is_capabilities_question(message):
            return True

        if cls._is_assistant_identity_question(message):
            return True

        exclude_terms = tuple(
            str(item) for item in (_augmentation_content().get("excludeTerms") or ())
        )

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        return bool(
            exclude_terms
            and ChatMessageNormalizationService.contains_any(normalized, exclude_terms)
        )

    @classmethod
    def _is_capabilities_question(cls, message: str) -> bool:
        detection = ChatAssistantContentService.get_node("capabilities", "detection") or {}

        if not isinstance(detection, dict):
            return False

        max_length = int(detection.get("maxMessageLength") or 280)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > max_length:
            return False

        question_terms = tuple(str(item) for item in (detection.get("questionTerms") or ()))

        if ChatMessageNormalizationService.contains_any(message, question_terms):
            return True

        short_help = tuple(str(item) for item in (detection.get("shortHelp") or ()))

        if normalized in short_help:
            return True

        help_prefix_max = int(detection.get("helpPrefixMaxLength") or 80)

        if normalized.startswith(("ajuda ", "help ")) and len(normalized) < help_prefix_max:
            return True

        capaz_tokens = tuple(str(item) for item in (detection.get("capazTokens") or ()))

        return "capaz" in normalized and any(token in normalized for token in capaz_tokens)

    @classmethod
    def _is_assistant_identity_question(cls, message: str) -> bool:
        if cls._is_capabilities_question(message):
            return False

        content = ChatAssistantContentService.load_bundle("identity")
        max_length = int(content.get("maxMessageLength") or 220)
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if len(normalized) > max_length:
            return False

        patterns = content.get("patterns") or {}
        priority = tuple(
            str(item)
            for item in (
                content.get("categoryPriority")
                or ("who", "limits", "origin", "usage", "role", "what")
            )
        )

        for category in priority:
            terms = tuple(str(item) for item in (patterns.get(category) or ()))

            if terms and ChatMessageNormalizationService.contains_any(message, terms):
                return True

        exclusions = tuple(str(item) for item in (content.get("userIdentityExclusions") or ()))

        return bool(
            exclusions and ChatMessageNormalizationService.contains_any(message, exclusions)
        )


@lru_cache(maxsize=1)
def _augmentation_content() -> dict:
    node = ChatAssistantContentService.get_node("web_search", "augmentation")

    return dict(node) if isinstance(node, dict) else {}


@lru_cache(maxsize=1)
def _public_facts_content() -> dict:
    node = ChatAssistantContentService.get_node("web_search", "publicFacts")

    return dict(node) if isinstance(node, dict) else {}


@lru_cache(maxsize=1)
def _post_rag_fallback_content() -> dict:
    node = ChatAssistantContentService.get_node("web_search", "postRagFallback")

    return dict(node) if isinstance(node, dict) else {}
