import re

from app.domain.services.chat_analysis_intent_vocabulary_service import (
    ChatAnalysisIntentVocabularyService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatAnalysisIntentService:
    """Detecta pedidos de comparação, apontamentos e insights (sem nova consulta operacional)."""

    @classmethod
    def _comparison_terms(cls) -> tuple[str, ...]:
        return ChatAnalysisIntentVocabularyService.terms("comparisonTerms")

    @classmethod
    def _data_interpretation_terms(cls) -> tuple[str, ...]:
        return ChatAnalysisIntentVocabularyService.terms("dataInterpretationTerms")

    @classmethod
    def _interpretation_short_commands(cls) -> tuple[str, ...]:
        return ChatAnalysisIntentVocabularyService.terms("interpretationShortCommands")

    @classmethod
    def _sql_result_interpretation_terms(cls) -> tuple[str, ...]:
        return ChatAnalysisIntentVocabularyService.terms("sqlResultInterpretationTerms")

    @classmethod
    def _data_reference_terms(cls) -> tuple[str, ...]:
        return ChatAnalysisIntentVocabularyService.terms("dataReferenceTerms")

    @classmethod
    def _data_reference_pronouns(cls) -> tuple[str, ...]:
        return ChatAnalysisIntentVocabularyService.terms("dataReferencePronouns")

    @classmethod
    def _email_from_data_terms(cls) -> tuple[str, ...]:
        return ChatAnalysisIntentVocabularyService.terms("emailFromDataTerms")

    _STRUCTURE_PATH_RE = re.compile(
        r"/products/(?P<code>[^/]+)/structure",
        re.IGNORECASE,
    )
    _PRODUCT_PATH_RE = re.compile(
        r"/products/(?P<code>[^/]+)(?:/(?P<segment>[^/?]+))?",
        re.IGNORECASE,
    )
    _PRODUCT_COLLECTION_PATH_CODES = frozenset({"search"})
    _PATH_PLACEHOLDER_RE = re.compile(r"^\{[^}]+\}$")

    @classmethod
    def is_email_from_operational_data_request(
        cls,
        message: str,
        previous_messages: list | None = None,
    ) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if not any(term in normalized for term in cls._email_from_data_terms()):
            return False

        return bool(
            previous_messages
            and cls._has_recent_successful_tool_data(previous_messages)
        )

    @classmethod
    def is_data_interpretation_request(
        cls,
        message: str,
        previous_messages: list | None = None,
    ) -> bool:
        """Pedido para interpretar dados já obtidos na conversa (sem nova consulta)."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        from app.domain.services.chat_presentation_format_refinement_service import (
            ChatPresentationFormatRefinementService,
        )

        if ChatPresentationFormatRefinementService.looks_like_format_refinement(message):
            return False

        if previous_messages and cls._has_recent_successful_tool_data(previous_messages):
            if cls._is_sql_result_interpretation_request(normalized):
                return True

        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        if ChatSqlIntentService.is_sql_conversation_turn(message):
            return False

        if ChatSqlQueryRefinementService.is_sql_follow_up(
            message,
            previous_messages=previous_messages,
        ):
            return False

        if cls.is_email_from_operational_data_request(message, previous_messages):
            return True

        if cls._matches_short_interpretation_command(normalized, previous_messages):
            return True

        if previous_messages and cls._has_recent_successful_tool_data(previous_messages):
            if any(
                term in normalized
                for term in (
                    "nao entendi",
                    "não entendi",
                    "nao entendi o que",
                    "não entendi o que",
                )
            ):
                return True

        if not any(term in normalized for term in cls._data_interpretation_terms()):
            return False

        if any(term in normalized for term in cls._data_reference_terms()):
            return bool(
                previous_messages
                and cls._has_recent_successful_tool_data(previous_messages)
            )

        if previous_messages and cls._has_recent_successful_tool_data(previous_messages):
            if any(term in normalized for term in cls._data_reference_pronouns()):
                return True

            if any(
                term in normalized
                for term in (
                    "os dados",
                    "o resultado",
                    "a tabela",
                    "a consulta",
                )
            ):
                return True

        return False

    @classmethod
    def _is_sql_result_interpretation_request(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._sql_result_interpretation_terms()):
            return True

        if any(
            term in normalized
            for term in ("interprete", "interpreta", "analise", "analisa")
        ):
            if "resultado" in normalized and (
                "consulta" in normalized or "sql" in normalized
            ):
                return True

            if any(
                term in normalized
                for term in (
                    "ultima consulta",
                    "última consulta",
                    "consulta anterior",
                )
            ):
                return True

        return False

    @classmethod
    def _matches_short_interpretation_command(
        cls,
        normalized: str,
        previous_messages: list | None,
    ) -> bool:
        if not previous_messages or not cls._has_recent_successful_tool_data(previous_messages):
            return False

        for command in cls._interpretation_short_commands():
            if normalized == command:
                return True

            if normalized.startswith(f"{command} "):
                tail = normalized[len(command) + 1 :].strip()

                if not tail or any(
                    token in tail
                    for token in (
                        "isso",
                        "isto",
                        "dados",
                        "resultado",
                        "tabela",
                        "consulta",
                        "acima",
                    )
                ):
                    return True

        return False

    @classmethod
    def _has_recent_successful_tool_data(
        cls,
        previous_messages: list,
        *,
        limit: int = 10,
    ) -> bool:
        for item in reversed(previous_messages[-limit:]):
            if isinstance(item, dict):
                metadata = item.get("metadata")
            else:
                metadata = getattr(item, "metadata", None)

            if not isinstance(metadata, dict):
                continue

            research = metadata.get("webSearchResearch")

            if isinstance(research, dict):
                status = str(research.get("searchStatus") or "").strip()

                if status == "success" or int(research.get("sourceCount") or 0) > 0:
                    return True

            for tool_call in metadata.get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                name = str(tool_call.get("name") or "")

                if name == "web_search":
                    tool_meta = tool_call.get("metadata") or {}

                    if tool_meta.get("ok") is True:
                        return True

                    data = tool_call.get("data")

                    if isinstance(data, dict) and str(data.get("searchStatus") or "") == "success":
                        return True

                    continue

                if name != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if tool_meta.get("ok"):
                    return True

        return False

    @classmethod
    def is_data_reference_without_tool_data(
        cls,
        message: str,
        previous_messages: list | None = None,
    ) -> bool:
        """Pedido de interpretação que referencia dados anteriores, mas sem consulta prévia."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        from app.domain.services.chat_sql_intent_service import ChatSqlIntentService
        from app.domain.services.chat_sql_query_refinement_service import (
            ChatSqlQueryRefinementService,
        )

        if ChatSqlIntentService.is_sql_conversation_turn(message):
            return False

        if ChatSqlQueryRefinementService.is_sql_follow_up(
            message,
            previous_messages=previous_messages,
        ):
            return False

        from app.domain.services.chat_web_search_history_service import (
            ChatWebSearchHistoryService,
        )
        from app.domain.services.chat_web_search_source_follow_up_service import (
            ChatWebSearchSourceFollowUpService,
        )

        if ChatWebSearchSourceFollowUpService.is_web_research_follow_up_request(
            normalized
        ):
            return False

        if ChatWebSearchHistoryService.has_recent_web_search(previous_messages or []):
            if any(
                term in normalized
                for term in (
                    "fonte",
                    "link",
                    "url",
                    "pesquisa web",
                    "busca na web",
                    "internet",
                    "parametr",
                    "divergenc",
                )
            ):
                return False

        if cls._has_recent_successful_tool_data(previous_messages or []):
            return False

        if any(term in normalized for term in cls._data_reference_terms()):
            return True

        if "acima" in normalized and any(
            term in normalized for term in cls._data_interpretation_terms()
        ):
            return True

        return normalized in cls._interpretation_short_commands()

    @classmethod
    def is_comparison_or_insight_request(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if cls._looks_like_single_product_fetch(normalized):
            return False

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            return False

        if any(term in normalized for term in cls._comparison_terms()):
            return True

        if ("as duas" in normalized or "os dois" in normalized or "ambos" in normalized) and any(
            token in normalized
            for token in (
                "estrutura",
                "produto",
                "item",
                "bom",
                "consulta",
                "resultado",
            )
        ):
            return True

        return False

    @classmethod
    def _looks_like_single_product_fetch(cls, normalized: str) -> bool:
        if ChatProductQueryIntentService._looks_like_production_status_question(normalized):
            return True

        if ChatProductQueryIntentService._looks_like_shipping_status_question(normalized):
            return True

        if ChatProductQueryIntentService._looks_like_structure_exclusivity_question(normalized):
            return True

        if ChatProductQueryIntentService._looks_like_factory_status_question(normalized):
            return True

        if ChatProductQueryIntentService._looks_like_raw_material_price_intelligence_question(
            normalized
        ):
            return True

        if ChatProductQueryIntentService._looks_like_cost_impact_simulation_question(normalized):
            return True

        if ChatProductQueryIntentService._looks_like_last_purchase_question(normalized):
            return True

        if any(
            term in normalized
            for term in (
                "ficha completa",
                "analise completa",
                "análise completa",
                "informacoes completas",
                "informações completas",
                "analisador do produto",
                "analisador completo",
                "analise produtiva",
                "análise produtiva",
                "status completo na fabrica",
                "status completo na fábrica",
            )
        ):
            return "compar" not in normalized and "versus" not in normalized

        return False

    @classmethod
    def extract_all_product_codes(cls, *texts: str | None) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []

        for text in texts:
            if not text:
                continue

            raw = str(text)

            for match in ChatProductQueryIntentService._PRODUCT_CODE_RE.finditer(raw):
                if ChatProductQueryIntentService._is_group_code_numeric_token(raw, match):
                    continue

                if ChatProductQueryIntentService._is_date_numeric_token(match.group(0)):
                    continue

                if ChatProductQueryIntentService._is_example_product_code_token(raw, match):
                    continue

                code = ChatProductQueryIntentService.normalize_product_code(match.group(0))

                if not code or code in seen:
                    continue

                seen.add(code)
                ordered.append(code)

        return ordered

    @classmethod
    def _message_uses_active_context_products(cls, message: str) -> bool:
        """Pergunta operacional sem código explícito — pode usar todos os produtos do contexto."""
        from app.domain.services.chat_message_normalization_service import (
            ChatMessageNormalizationService,
        )
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        if ChatProductQueryIntentService.extract_product_code(message):
            return False

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if ChatProductQueryIntentService.references_previous_product(message):
            return True

        if ChatRouteContextService.is_product_route_segment(
            ChatRouteContextService.segment_from_message(message)
        ):
            return True

        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )

        return (
            ChatProductQueryIntentService._looks_like_stock_question(normalized)
            or ChatProductQueryIntentService._looks_like_structure_question(normalized)
            or ChatProductQueryIntentService._looks_like_sales_question(normalized)
            or ChatProductQueryIntentService._looks_like_product_summary_question(normalized)
            or ChatProductQueryIntentService._looks_like_description_question(normalized)
            or ChatProductQueryIntentService._looks_like_parents_question(normalized)
            or ChatProductPluralPhrasingService.mentions_plural_products(normalized)
            or any(
                term in normalized
                for term in (
                    "preco",
                    "preço",
                    "pricing",
                    "fornecedor",
                    "fornece",
                    "fornecedores",
                    "roteiro",
                    "roteiros",
                    "inspecao",
                    "inspeção",
                    "inspecoes",
                    "inspeções",
                    "compra",
                    "compras",
                )
            )
        )

    @classmethod
    def extract_product_codes_for_action_planning(
        cls,
        message: str,
        conversation_context: str | None = None,
        *,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> list[str]:
        """Códigos para planejar consultas paralelas à API.

        Se a mensagem atual já traz código(s), não puxa códigos extras do histórico
        (evita N× estoque quando o usuário pergunta só de um produto).
        Com vários produtos em ``userContextItems``, consulta todos (ex.: «estoque»).
        """
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        codes_in_message = cls.extract_all_product_codes(message)

        if codes_in_message:
            return codes_in_message

        context_codes: list[str] = []

        if isinstance(memory_snapshot, dict):
            context_codes = ChatUserContextItemService.resolve_all_product_codes_from_items(
                memory_snapshot.get("userContextItems"),
            )

        if (
            not context_codes
            and conversation_context
            and cls._message_uses_active_context_products(message)
        ):
            context_codes = ChatUserContextItemService.resolve_all_product_codes_from_context_prompt(
                conversation_context,
            )

        if context_codes and cls._message_uses_active_context_products(message):
            return context_codes

        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        if (
            ChatProductQueryIntentService.references_previous_product(message)
            or ChatRouteContextService.is_product_route_segment(
                ChatRouteContextService.segment_from_message(message)
            )
        ):
            code = ChatProductQueryIntentService.resolve_product_code(
                message,
                conversation_context,
                previous_messages=previous_messages,
                memory_snapshot=memory_snapshot,
            )

            return [code] if code else []

        return []

    @classmethod
    def looks_like_path_placeholder(cls, value: str | None) -> bool:
        token = str(value or "").strip()

        if not token:
            return False

        return bool(cls._PATH_PLACEHOLDER_RE.match(token))

    @classmethod
    def extract_product_code_from_tool_path(cls, path: str | None) -> str | None:
        if not path:
            return None

        match = cls._PRODUCT_PATH_RE.search(str(path))

        if not match:
            return None

        raw_code = str(match.group("code") or "").strip()

        if cls.looks_like_path_placeholder(raw_code):
            return None

        if raw_code.lower() in cls._PRODUCT_COLLECTION_PATH_CODES:
            return None

        normalized = ChatProductQueryIntentService.normalize_product_code(raw_code)

        if not ChatProductQueryIntentService.is_plausible_product_code(normalized):
            return None

        return normalized

    @classmethod
    def extract_product_path_segment(cls, path: str | None) -> str | None:
        if not path:
            return None

        match = cls._PRODUCT_PATH_RE.search(str(path))

        if not match or not match.group("segment"):
            return None

        return str(match.group("segment")).strip().lower()
