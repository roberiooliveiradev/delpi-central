"""Heurísticas e vocabulário do roteador de intenção."""

from __future__ import annotations


class ChatIntentRouterHeuristicsService:
    @staticmethod
    def intent_router_terms(*path: str) -> tuple[str, ...]:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        return tuple(ChatAssistantContentService.list("intent_router", *path))

    @staticmethod
    def product_router_terms(*path: str) -> tuple[str, ...]:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        return tuple(
            ChatAssistantContentService.list("product_query_intent", "router", *path)
        )
    @staticmethod
    def mixed_compound_steps(message: str) -> tuple[str, ...] | None:
        lowered = message.lower()
        steps: list[str] = []

        has_web = any(
            term in lowered
            for term in (
                "pesquise na web",
                "pesquisa na web",
                "na internet",
                "busque na web",
            )
        )
        has_report = any(
            term in lowered for term in ("relatório", "relatorio", "resumo executivo", "report")
        )

        if has_web and has_report:
            steps.extend(["web_search", "report_compose"])

        has_attachment = any(
            term in lowered
            for term in ("resuma o pdf", "resuma esse pdf", "resuma o anexo", "resuma o arquivo")
        )
        has_canvas = any(term in lowered for term in ("lousa", "canvas"))

        if has_attachment and has_canvas:
            steps.extend(["attachment_summary", "canvas_placement"])

        has_table = "tabela" in lowered or "em tabela" in lowered
        has_chart = any(term in lowered for term in ("gráfico", "grafico", "em pizza", "em barras"))

        if has_table and has_chart:
            steps.extend(["presentation_table", "presentation_chart"])

        if len(steps) < 2:
            return None

        return tuple(steps)

    @staticmethod
    def mixed_task_steps(message: str) -> tuple[str, ...]:
        steps: list[str] = []
        sub = ChatIntentRouterHeuristicsService.operational_sub_intent(message)

        if sub:
            steps.append(sub)
        else:
            steps.append("operational_lookup")

        from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService

        category = ChatTextTaskIntentService.classify(message)

        if category == "email":
            steps.append("email_create")
        else:
            steps.append("text_compose")

        return tuple(steps)

    @staticmethod
    def map_follow_up_sub_intent(follow_type: str | None) -> str | None:
        mapping = {
            "supplier": "supplier_lookup",
            "stock": "stock_lookup",
            "structure": "structure_lookup",
            "structure_exclusivity": "structure_exclusivity_lookup",
            "routing": "guide_lookup",
            "outbound_invoice": "sales_lookup",
        }

        return mapping.get(follow_type or "")

    @staticmethod
    def looks_attachment_summary(message: str) -> bool:
        lowered = message.lower()

        return any(
            term in lowered
            for term in (
                "resuma esse pdf",
                "resuma o pdf",
                "resuma esse arquivo",
                "resuma o anexo",
                "resumir o pdf",
                "resumir esse documento",
            )
        )

    @staticmethod
    def blocks_web_search(message: str) -> bool:
        lowered = message.lower()

        return any(
            term in lowered
            for term in ChatIntentRouterHeuristicsService.intent_router_terms("webBlockTerms")
        )

    @staticmethod
    def looks_web_search(message: str) -> bool:
        from app.domain.services.chat_web_search_intent_service import ChatWebSearchIntentService

        if ChatWebSearchIntentService.matches(message):
            return True

        lowered = message.lower()

        return any(
            phrase in lowered
            for phrase in (
                "pesquise na web",
                "pesquisa na web",
                "procure na internet",
                "busque fonte oficial",
                "busque no site",
                "notícias recentes",
                "noticias recentes",
                "procure datasheet",
                "compare fontes externas",
                "veja fontes externas",
            )
        )

    @staticmethod
    def sql_sub_intent(message: str) -> str | None:
        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService

        return ChatSqlIntentService.router_sub_intent(message)

    @staticmethod
    def looks_presentation(message: str) -> bool:
        lowered = message.lower()

        return any(
            term in lowered
            for term in ChatIntentRouterHeuristicsService.intent_router_terms("presentationTerms")
        )

    @staticmethod
    def presentation_sub_intent(message: str) -> str | None:
        lowered = message.lower()

        if "tabela" in lowered:
            return "table"

        if any(term in lowered for term in ("pizza", "rosca", "barras", "linha", "gráfico", "grafico")):
            return "chart"

        if "kpi" in lowered:
            return "kpi"

        if "árvore" in lowered or "arvore" in lowered:
            return "tree"

        return "presentation"

    @staticmethod
    def operational_ambiguity(
        message: str,
        resolved_params: dict[str, str] | None,
    ) -> tuple[bool, tuple[str, ...]]:
        from app.domain.services.chat_operational_ambiguity_service import (
            ChatOperationalAmbiguityService,
        )

        return ChatOperationalAmbiguityService.resolve(message, resolved_params)

    @staticmethod
    def resolve_department_kpi(message: str):
        from app.domain.services.chat_department_kpi_intent_service import (
            ChatDepartmentKpiIntentService,
        )

        return ChatDepartmentKpiIntentService.resolve(message)

    @staticmethod
    def looks_operational(message: str) -> bool:
        """Operational when keywords hit OR product route predicates already resolve a scope.

        Keywords alone miss routes declared only in ``routePredicates`` / registry
        (e.g. notas fiscais, movimentação interna). Prefer the actionable product
        intent gate over growing ``operationalKeywords`` per symptom.
        """
        lowered = message.lower()

        if any(
            term in lowered
            for term in ChatIntentRouterHeuristicsService.product_router_terms(
                "operationalKeywords"
            )
        ):
            return True

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_product_search_intent_service import (
            ChatProductSearchIntentService,
        )

        if ChatProductSearchIntentService.looks_like_product_search(message):
            return True

        return ChatProductQueryIntentService.has_actionable_product_route_intent(message)

    @staticmethod
    def operational_sub_intent(message: str) -> str | None:
        from app.domain.services.chat_operational_sub_intent_service import (
            ChatOperationalSubIntentService,
        )

        return ChatOperationalSubIntentService.resolve(message)

    @staticmethod
    def looks_rag_document(message: str) -> bool:
        """Consulta a base documental (company-knowledge) — não criação de texto."""
        lowered = str(message or "").lower()

        if any(
            phrase in lowered
            for phrase in ChatIntentRouterHeuristicsService.intent_router_terms(
                "ragDocumentCreateExcludePhrases"
            )
        ):
            return False

        if ChatIntentRouterHeuristicsService._has_inline_text_directive(lowered):
            return False

        return any(
            term in lowered
            for term in ChatIntentRouterHeuristicsService.intent_router_terms("ragDocumentTerms")
        )

    @staticmethod
    def _has_inline_text_directive(lowered: str) -> bool:
        """Diretiva de redação com texto colado (``corrija: …``) não é consulta documental.

        Sem isto, qualquer pedido de correção que cite «documento» ou «anexo» cai na
        base documental e perde a tarefa de texto puro.
        """
        if ":" not in lowered:
            return False

        leads = ChatIntentRouterHeuristicsService.intent_router_terms(
            "ragDocumentInlineDirectiveLeads"
        )

        return any(lowered.startswith(lead) for lead in leads)

    @classmethod
    def previous_assistant_was_documental_rag(cls, previous_messages: list | None) -> bool:
        """Última resposta do assistente veio de consulta documental (F07 continuity)."""
        if not previous_messages:
            return False

        from app.domain.services.chat_conversation_context_service import (
            ChatConversationContextService,
        )

        for message in reversed(list(previous_messages)):
            role = ChatConversationContextService.message_role(message).lower()
            if role not in {"assistant", "ai"}:
                continue

            metadata = ChatConversationContextService.message_metadata(message)
            admin = metadata.get("adminDebug") if isinstance(metadata.get("adminDebug"), dict) else {}
            # API HTTP pode espelhar adminDebug na raiz do dict (não no entity ChatMessage).
            if not admin and isinstance(message, dict):
                top = message.get("adminDebug")
                admin = top if isinstance(top, dict) else {}
            route = admin.get("intentRoute") if isinstance(admin.get("intentRoute"), dict) else {}
            if not route:
                intel = (
                    metadata.get("intelligence")
                    if isinstance(metadata.get("intelligence"), dict)
                    else {}
                )
                route = intel.get("intentRoute") if isinstance(intel.get("intentRoute"), dict) else {}

            decision = str(route.get("decision") or "").strip().lower()
            intent = str(route.get("intent") or "").strip().lower()
            if decision in {"rag_internal", "rag_question"} or intent in {
                "rag_question",
                "rag",
            }:
                return True

            content = ChatConversationContextService.message_content(message).lower()
            if not content and isinstance(message, dict):
                content = str(message.get("answer") or "").lower()
            if any(
                marker in content
                for marker in (
                    "normas técnicas",
                    "base de conhecimento",
                    "política",
                    "glossário",
                    "documentação autorizada",
                )
            ):
                return True

            return False

        return False

    @classmethod
    def looks_like_documental_topic_follow_up(
        cls,
        message: str,
        previous_messages: list | None = None,
    ) -> bool:
        """Resposta curta de tópico após turno RAG (ex.: «terminais» após normas)."""
        if not cls.previous_assistant_was_documental_rag(previous_messages):
            return False

        normalized = " ".join(str(message or "").strip().lower().split())
        if not normalized or len(normalized) > 64:
            return False

        if cls.looks_rag_document(normalized):
            return True

        if cls.looks_self_help(normalized) or cls.looks_conversation_meta(normalized):
            return False

        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        if ChatProductQueryIntentService.extract_product_code(normalized):
            # código isolado após normas (ex.: 1008) ainda é follow-up documental
            if normalized.isdigit() or len(normalized) <= 8:
                return True
            return False

        words = normalized.split()
        if len(words) > 6:
            return False

        if any(ch in normalized for ch in "?!。"):
            return False

        return True

    @classmethod
    def looks_self_help(cls, message: str) -> bool:
        lowered = message.lower()

        return any(
            phrase in lowered
            for phrase in cls.intent_router_terms("selfHelpPhrases")
        )

    @classmethod
    def looks_conversation_meta(cls, message: str) -> bool:
        """Delega ao módulo canônico de message search (família session review)."""
        from app.domain.services.chat_conversation_message_search_service import (
            ChatConversationMessageSearchService,
        )

        return ChatConversationMessageSearchService.is_session_review_request(message)

    @classmethod
    def looks_like_short_context_reply(cls, message: str) -> bool:
        """Resposta curta que só completa parâmetro (filial/data/código) com foco ativo."""
        from app.domain.services.chat_intent_router_content_service import (
            ChatIntentRouterContentService,
        )

        normalized = " ".join(str(message or "").strip().lower().split())
        max_chars = ChatIntentRouterContentService.limit_int(
            "shortContextReplyMaxChars",
            48,
        )

        if not normalized or len(normalized) > max_chars:
            return False

        if cls.looks_conversation_meta(normalized):
            return False

        return any(
            pattern.fullmatch(normalized)
            for pattern in ChatIntentRouterContentService.short_context_reply_patterns()
        )

    @staticmethod
    def looks_identity_question(message: str) -> bool:
        from app.domain.services.chat_assistant_identity_service import (
            ChatAssistantIdentityService,
        )

        return ChatAssistantIdentityService.is_assistant_identity_question(message)

    @staticmethod
    def looks_capabilities_question(message: str) -> bool:
        """Compatibilidade com chamadas legadas."""
        return ChatIntentRouterHeuristicsService.looks_self_help(message)
