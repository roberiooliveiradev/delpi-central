import re

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_INTENT_CONTENT_BUNDLE = "product_query_intent"


class ChatProductQueryIntent:
    DESCRIPTION = "description"
    SUMMARY = "summary"
    ANALYSER = "analyser"
    MULTI_SCOPE = "multi_scope"
    STOCK = "stock"
    SALES = "sales"
    STRUCTURE = "structure"
    PARENTS = "parents"
    FULL = "full"


class ChatProductQueryIntentService:
    @classmethod
    def _terms(cls, *path: str) -> tuple[str, ...]:
        return tuple(
            ChatAssistantContentService.list(_INTENT_CONTENT_BUNDLE, *path)
        )

    @classmethod
    def _header(cls, key: str, *, default: str = "") -> str:
        return ChatAssistantContentService.get(
            _INTENT_CONTENT_BUNDLE,
            "directAnswerHeaders",
            key,
            default=default,
        )

    _ZERO_RECORDS_RE = re.compile(r":\s*0 registro\(s\)\.?$", re.IGNORECASE)
    _PRODUCT_CODE_RE = re.compile(
        r"\b(?:\d[\d.\-/]{2,}\d|\d{4,})\b",
    )
    _SPECIFICATION_TOKEN_RE = re.compile(
        r"^\d+[,.]\d+[-xX]\d+[,.]\d+|\d+[,.]\d+\s*[-xX]\s*\d+[,.]\d+",
        re.IGNORECASE,
    )
    _DATE_TOKEN_RE = re.compile(
        r"^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}$",
        re.IGNORECASE,
    )
    _CALENDAR_YEAR_RE = re.compile(r"^(19|20)\d{2}$")
    _EXAMPLE_CODE_PREFIX_RE = re.compile(
        r"(?:\bex\.?\s*:?|\bexemplo\s*:?|\binforme\s+(?:o\s+)?(?:c[óo]digo|codigo)|\bpor\s+exemplo)\s*$",
        re.IGNORECASE,
    )

    @classmethod
    def detect(cls, message: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        from app.domain.services.chat_drawing_intent_service import (
            ChatDrawingIntentService,
        )

        if ChatDrawingIntentService.is_drawing_analysis_request(message):
            return ChatProductQueryIntent.ANALYSER

        if cls._looks_like_mixed_documental_operational(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_parents_question(normalized):
            return ChatProductQueryIntent.PARENTS

        if cls._looks_like_sale_pricing_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_cost_impact_simulation_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_raw_material_price_intelligence_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_last_purchase_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_purchase_price_history_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_purchase_budget_history_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_directives_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_factory_status_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_production_status_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_shipping_status_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_structure_exclusivity_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_price_analysis_question(normalized):
            return ChatProductQueryIntent.FULL

        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )

        requested_scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(message)

        if len(requested_scopes) >= 2:
            if ChatProductMultiScopePlanningService.should_use_single_analyser(
                requested_scopes,
                message,
            ):
                return ChatProductQueryIntent.ANALYSER

            return ChatProductQueryIntent.MULTI_SCOPE

        if cls._looks_like_full_analyser_question(normalized):
            return ChatProductQueryIntent.ANALYSER

        if cls._looks_like_structure_question(normalized):
            return ChatProductQueryIntent.STRUCTURE

        if cls._looks_like_sales_question(normalized):
            return ChatProductQueryIntent.SALES

        if cls._looks_like_stock_question(normalized):
            return ChatProductQueryIntent.STOCK

        if cls._looks_like_product_summary_question(normalized):
            return ChatProductQueryIntent.SUMMARY

        from app.domain.services.chat_product_overview_intent_service import (
            ChatProductOverviewIntentService,
        )

        if ChatProductOverviewIntentService.is_product_overview_message(message):
            return ChatProductQueryIntent.ANALYSER

        if cls._looks_like_description_question(normalized):
            return ChatProductQueryIntent.DESCRIPTION

        return ChatProductQueryIntent.FULL

    @classmethod
    def _looks_like_mixed_documental_operational(cls, normalized: str) -> bool:
        return any(
            term in normalized for term in cls._terms("mixedDocumental", "documental")
        ) and any(
            term in normalized for term in cls._terms("mixedDocumental", "operational")
        )

    @classmethod
    def references_previous_product(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        terms = [
            *cls._terms("referencesPreviousProduct", "filterTerms"),
            *ChatProductOperationalContentService.list(
                "referencesPreviousProduct",
                "terms",
            ),
        ]

        return any(term in normalized for term in terms) or cls._looks_like_product_followup(
            normalized
        )

    @classmethod
    def _looks_like_product_followup(cls, normalized: str) -> bool:
        has_followup = any(
            term in normalized for term in cls._terms("followUp", "followup")
        )
        has_product_ref = any(
            term in normalized for term in cls._terms("followUp", "productRef")
        )

        return has_followup and has_product_ref

    @classmethod
    def normalize_product_code(cls, raw: str) -> str:
        digits = re.sub(r"\D", "", str(raw or ""))

        if len(digits) >= 4:
            return digits

        return str(raw or "").strip()

    @classmethod
    def _is_example_product_code_token(cls, text: str, match: re.Match[str]) -> bool:
        prefix = text[max(0, match.start() - 64) : match.start()].lower()

        return bool(cls._EXAMPLE_CODE_PREFIX_RE.search(prefix))

    @classmethod
    def is_plausible_product_code(cls, code: str | None) -> bool:
        normalized = str(code or "").strip()

        if not normalized:
            return False

        digits = re.sub(r"\D", "", normalized)

        if len(digits) >= 4:
            return True

        if re.search(r"[-/,]", normalized):
            return False

        return len(digits) >= 3

    @classmethod
    def _is_specification_numeric_token(cls, token: str) -> bool:
        raw = str(token or "").strip()

        if cls._SPECIFICATION_TOKEN_RE.search(raw):
            return True

        if re.search(r"[-/,]", raw):
            digits = re.sub(r"\D", "", raw)

            if len(digits) < 4:
                return True

        return False

    @classmethod
    def extract_product_code(cls, text: str | None) -> str | None:
        if cls._looks_like_lmp_context(text):
            return None

        raw = str(text or "")

        for match in cls._PRODUCT_CODE_RE.finditer(raw):
            token = match.group(0)

            if cls._is_group_code_numeric_token(raw, match):
                continue

            if cls._is_date_numeric_token(token):
                continue

            if cls._is_calendar_year_token(raw, match):
                continue

            if cls._is_specification_numeric_token(token):
                continue

            if cls._is_example_product_code_token(raw, match):
                continue

            if cls._is_phone_contact_token(raw, match):
                continue

            code = cls.normalize_product_code(token)

            if cls.is_plausible_product_code(code):
                return code

        return None

    @classmethod
    def _is_date_numeric_token(cls, token: str) -> bool:
        return bool(cls._DATE_TOKEN_RE.match(str(token or "").strip()))

    @classmethod
    def _is_calendar_year_token(cls, text: str, match: re.Match[str]) -> bool:
        token = str(match.group(0) or "").strip()

        if not cls._CALENDAR_YEAR_RE.match(token):
            return False

        prefix = text[max(0, match.start() - 32) : match.start()].lower()

        if re.search(
            r"(?:\bproduto|\bitem|\bc[oó]digo|\bcode|\brefer[eê]ncia)\s*$",
            prefix,
            flags=re.IGNORECASE,
        ):
            return False

        return True

    @classmethod
    def looks_like_scope_reset_operational_query(cls, message: str | None) -> bool:
        """Consulta agregada/temporal — não reaproveitar productCode da sessão."""
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        if any(
            marker in normalized
            for marker in cls._terms("scopeReset", "markers")
        ):
            return True

        if cls.references_previous_product(message):
            return False

        if re.search(r"\b20\d{2}\b", normalized) and any(
            term in normalized for term in cls._terms("scopeReset", "temporal")
        ):
            return True

        return False

    @classmethod
    def should_inherit_product_code(cls, message: str | None) -> bool:
        if cls.looks_like_scope_reset_operational_query(message):
            return False

        if cls.extract_product_code(message):
            return True

        if cls.references_previous_product(message):
            return True

        from app.domain.services.chat_follow_up_intent_service import (
            ChatFollowUpIntentService,
        )

        return ChatFollowUpIntentService.is_operational_follow_up(message)

    @classmethod
    def _is_phone_contact_token(cls, text: str, match: re.Match[str]) -> bool:
        token = str(match.group(0) or "").strip()
        window = text[max(0, match.start() - 18) : min(len(text), match.end() + 18)]

        if re.search(r"\(\s*\d{2}\s*\)\s*[\d\s\-–]{5,}", window):
            return True

        if re.fullmatch(r"\d{3,4}-\d{4}", token):
            return True

        digits = re.sub(r"\D", "", token)

        if len(digits) in {7, 8}:
            prefix = text[max(0, match.start() - 12) : match.start()]

            if ")" in prefix or re.search(r"\(\s*\d{2}", prefix):
                return True

        return False

    @classmethod
    def _is_group_code_numeric_token(cls, text: str, match: re.Match[str]) -> bool:
        """Evita confundir «grupo 1008» com código de produto 1008."""
        prefix = text[max(0, match.start() - 48) : match.start()].lower()

        if re.search(
            r"(?:\bgrupo|\bgroup_code|\bdo\s+grupo|\bpelo\s+grupo|\bde\s+grupo)\s*$",
            prefix,
            flags=re.IGNORECASE,
        ):
            return True

        if re.search(r"\bgrupo\s+de\s+produtos?\s*$", prefix, flags=re.IGNORECASE):
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(text)

        if "grupo" in normalized and re.search(
            rf"\bgrupo\s+{re.escape(match.group(0).lower())}\b",
            normalized,
        ):
            return True

        return False

    @classmethod
    def _looks_like_lmp_context(cls, text: str | None) -> bool:
        normalized = str(text or "").lower()

        return any(term in normalized for term in cls._terms("lmpContext"))

    @classmethod
    def extract_last_product_code(cls, text: str | None) -> str | None:
        raw = str(text or "")
        last_code: str | None = None

        for match in cls._PRODUCT_CODE_RE.finditer(raw):
            if cls._is_group_code_numeric_token(raw, match):
                continue

            if cls._is_date_numeric_token(match.group(0)):
                continue

            if cls._is_specification_numeric_token(match.group(0)):
                continue

            if cls._is_example_product_code_token(raw, match):
                continue

            if cls._is_phone_contact_token(raw, match):
                continue

            code = cls.normalize_product_code(match.group(0))

            if cls.is_plausible_product_code(code):
                last_code = code

        return last_code

    @classmethod
    def extract_last_product_code_from_messages(
        cls,
        previous_messages: list | None,
    ) -> str | None:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        for item in reversed((previous_messages or [])[-16:]):
            metadata = cls._message_metadata(item)

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
                    str(tool_meta.get("path") or "")
                )

                if code and cls.is_plausible_product_code(code):
                    return code

            content = cls._message_content(item)

            if cls._message_field_role(item) == "assistant":
                lowered = ChatMessageNormalizationService.normalize_for_matching(content)

                if (
                    "informe o codigo" in lowered
                    or "informe o codigo do produto" in lowered
                    or ("codigo do produto" in lowered and "ex." in lowered)
                ):
                    continue

            code = cls.extract_product_code(content)

            if code:
                return code

        return None

    @classmethod
    def _message_field_role(cls, message) -> str:
        if isinstance(message, dict):
            return str(message.get("role") or "").strip().lower()

        return str(getattr(message, "role", "") or "").strip().lower()

    @classmethod
    def _looks_like_explicit_playbook_product_scope(cls, normalized: str) -> bool:
        """Playbook fabril/MP/PA — não herdar intent de consulta anterior (ex.: estoque)."""
        return (
            cls._looks_like_factory_status_question(normalized)
            or cls._looks_like_production_status_question(normalized)
            or cls._looks_like_shipping_status_question(normalized)
            or cls._looks_like_structure_exclusivity_question(normalized)
            or cls._looks_like_cost_impact_simulation_question(normalized)
            or cls._looks_like_raw_material_price_intelligence_question(normalized)
            or cls._looks_like_last_purchase_question(normalized)
            or cls._looks_like_purchase_price_history_question(normalized)
            or cls._looks_like_purchase_budget_history_question(normalized)
            or cls._looks_like_sale_pricing_question(normalized)
            or cls._looks_like_price_analysis_question(normalized)
        )

    @classmethod
    def infer_intent_from_recent_tool(cls, previous_messages: list | None) -> str | None:
        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        segment = ChatRouteContextService.infer_product_route_segment_from_recent_tool(
            previous_messages
        )

        if not segment:
            return None

        intent = ChatRouteContextService.intent_for_product_segment(segment)

        if intent:
            return intent

        if ChatRouteContextService.is_product_route_segment(segment):
            return ChatProductQueryIntent.FULL

        return None

    @classmethod
    def resolve_product_intent(
        cls,
        message: str,
        *,
        previous_messages: list | None = None,
    ) -> str:
        from app.domain.services.chat_product_description_resolution_service import (
            ChatProductDescriptionResolutionService,
        )

        if ChatProductDescriptionResolutionService.looks_like_description_lookup(message):
            return ChatProductQueryIntent.FULL

        intent = cls.detect(message)

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if intent != ChatProductQueryIntent.FULL:
            if (
                cls._looks_like_explicit_playbook_product_scope(normalized)
                or cls._looks_like_price_analysis_question(normalized)
            ):
                return ChatProductQueryIntent.FULL

            return intent

        if cls._looks_like_explicit_playbook_product_scope(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_price_analysis_question(normalized):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_product_sub_intent(normalized):
            return intent

        inherited = cls.infer_intent_from_recent_tool(previous_messages)

        if not inherited:
            return intent

        if cls.extract_product_code(message) or cls.references_previous_product(message):
            if cls._looks_like_explicit_playbook_product_scope(normalized):
                return ChatProductQueryIntent.FULL

            if cls._looks_like_price_analysis_question(normalized):
                return ChatProductQueryIntent.FULL

            return inherited

        return inherited

    @classmethod
    def resolve_product_code(
        cls,
        message: str,
        conversation_context: str | None = None,
        *,
        previous_messages: list | None = None,
        user_context_items: list | None = None,
        operational_focus: dict | None = None,
        memory_snapshot: dict | None = None,
    ) -> str | None:
        from app.domain.services.chat_product_description_resolution_service import (
            ChatProductDescriptionResolutionService,
        )

        drill_code = ChatProductDescriptionResolutionService.extract_code_from_drilldown_message(
            message,
        )

        if drill_code:
            return drill_code

        description_query = ChatProductDescriptionResolutionService.extract_description_query(
            message,
        )

        if description_query:
            resolved = ChatProductDescriptionResolutionService.resolve_code_from_history(
                description_query,
                previous_messages=previous_messages,
            )

            if resolved:
                return resolved

        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
        )

        if ChatProductionOperationalIntentService.matches_rest_route(message):
            return cls.extract_product_code(message)

        if cls.looks_like_scope_reset_operational_query(message):
            return cls.extract_product_code(message)

        code = cls.extract_product_code(message)

        if code:
            return code

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        from app.domain.services.chat_route_context_service import (
            ChatRouteContextService,
        )

        if not (
            cls.references_previous_product(message)
            or cls._looks_like_sales_question(normalized)
            or cls._looks_like_stock_question(normalized)
            or cls._looks_like_stock_scope_reset_question(normalized)
            or cls._looks_like_description_question(normalized)
            or cls._looks_like_product_summary_question(normalized)
            or cls._looks_like_structure_question(normalized)
            or cls._looks_like_parents_question(normalized)
            or cls._looks_like_product_sub_intent(normalized)
            or ChatRouteContextService.segment_from_message(message)
            or ChatRouteContextService.resolve_product_route_segment(
                message,
                previous_messages=previous_messages,
            )
        ):
            return None

        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        from app.domain.services.chat_snapshot_operational_focus import (
            ChatSnapshotOperationalFocus,
        )

        if memory_snapshot and user_context_items is None and operational_focus is None:
            if isinstance(memory_snapshot, dict):
                user_context_items = memory_snapshot.get("userContextItems")
                operational_focus = ChatSnapshotOperationalFocus.get(memory_snapshot)

        if user_context_items is not None:
            code = ChatUserContextItemService.resolve_product_code_from_items(
                user_context_items,
            )

            if code:
                return code

        if isinstance(operational_focus, dict):
            token = str(operational_focus.get("productCode") or "").strip()

            if token and cls.is_plausible_product_code(token):
                return token

        if conversation_context:
            code = ChatUserContextItemService.resolve_product_code_from_context_prompt(
                conversation_context,
            )

            if code:
                return code

        if previous_messages:
            code = cls.extract_last_product_code_from_messages(previous_messages)

            if code:
                return code

        if conversation_context:
            return cls.extract_last_product_code(conversation_context)

        return None

    @classmethod
    def _message_metadata(cls, message) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}

    @classmethod
    def _message_content(cls, message) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")

    @classmethod
    def format_direct_answer(
        cls,
        humanized: dict,
        *,
        intent: str,
        path: str | None = None,
    ) -> str | None:
        normalized_path = str(path or "").lower()

        if intent in {
            ChatProductQueryIntent.MULTI_SCOPE,
            ChatProductQueryIntent.STOCK,
            ChatProductQueryIntent.PARENTS,
        } or (
            intent == ChatProductQueryIntent.FULL
            and cls._is_product_operational_path(normalized_path)
        ):
            brief = cls._format_product_scope_brief(
                humanized,
                intent=intent,
                path=normalized_path,
            )

            if brief:
                return brief

        if intent == ChatProductQueryIntent.STRUCTURE:
            from app.domain.services.chat_product_structure_presentation_service import (
                ChatProductStructurePresentationService,
            )

            dados = humanized.get("dados")

            if isinstance(dados, dict):
                formatted = ChatProductStructurePresentationService.format_markdown(
                    dados,
                    source_path=humanized.get("sourcePath"),
                )

                if formatted:
                    return formatted

        lines = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line).strip()
        ]

        if not lines:
            return None

        title = str(humanized.get("titulo") or "").strip()

        if intent == ChatProductQueryIntent.DESCRIPTION:
            parts = [title] if title else []
            parts.append(lines[0])
            return "\n\n".join(parts)

        filtered = [line for line in lines if not cls._ZERO_RECORDS_RE.search(line)]
        parts = [title] if title else []
        parts.extend(filtered or lines)
        return "\n\n".join(parts)

    @classmethod
    def _is_product_operational_path(cls, path: str) -> bool:
        return any(
            segment in path
            for segment in (
                "/stock",
                "/parents",
                "/guide",
                "/inspection",
                "/structure",
            )
        )

    @classmethod
    def _format_product_scope_brief(
        cls,
        humanized: dict,
        *,
        intent: str,
        path: str,
    ) -> str | None:
        lines = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line).strip() and not cls._ZERO_RECORDS_RE.search(str(line).strip())
        ]

        if not lines:
            return None

        title = str(humanized.get("titulo") or "").strip()
        header = title or cls._header("default", default="Consulta do produto")
        body = "\n\n".join(lines[:3])

        if intent == ChatProductQueryIntent.STOCK or "/stock" in path:
            header = title or cls._header("stock", default="Estoque do produto")

        if intent == ChatProductQueryIntent.PARENTS or "/parents" in path:
            header = title or cls._header("parents", default="Onde o item é usado")

        return f"**{header}**\n\n{body}"

    @classmethod
    def _filter_stock_lines(cls, lines: list[str]) -> list[str]:
        stock_lines = []

        for line in lines:
            lowered = line.lower()

            if any(
                token in lowered
                for token in cls._terms("stock", "lineTokens")
            ):
                stock_lines.append(line)

        return stock_lines

    @classmethod
    def _looks_like_stock_scope_reset_question(cls, normalized: str) -> bool:
        return any(
            term in normalized for term in cls._terms("stock", "scopeReset")
        )

    @classmethod
    def _looks_like_sales_question(cls, normalized: str) -> bool:
        if cls._looks_like_sale_pricing_question(normalized):
            return False

        if cls._looks_like_stock_question(normalized):
            return False

        if any(
            term in normalized for term in cls._terms("sales", "excludeBilling")
        ):
            return False

        from app.domain.services.chat_department_kpi_intent_service import (
            ChatDepartmentKpiIntentService,
        )

        if ChatDepartmentKpiIntentService.resolve(normalized):
            return False

        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )

        if any(
            term in normalized for term in cls._terms("sales", "explicitPhrases")
        ):
            return True

        if ChatProductPluralPhrasingService.matches_scope_linked_to_products(
            normalized,
            scope="sales",
        ):
            return True

        has_product_ref = ChatProductPluralPhrasingService.has_product_entity_reference(
            normalized
        )

        return has_product_ref and any(
            term in normalized for term in cls._terms("sales", "productSaleTerms")
        )

    @classmethod
    def _has_product_scope_reference(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )

        return bool(
            cls.extract_product_code(normalized)
            or ChatProductPluralPhrasingService.has_product_entity_reference(
                normalized
            )
        )

    @classmethod
    def _looks_like_billing_question(cls, normalized: str) -> bool:
        if not any(term in normalized for term in cls._terms("billing", "terms")):
            return False

        return cls._has_product_scope_reference(normalized)

    @classmethod
    def _looks_like_factory_status_question(cls, normalized: str) -> bool:
        if cls._looks_like_production_status_question(normalized):
            factory_only = any(
                term in normalized
                for term in cls._terms("factoryStatus", "terms")
            ) or any(
                marker in normalized
                for marker in (
                    "fabril",
                    "fabrica",
                    "fábrica",
                    "completo na fabrica",
                    "completo na fábrica",
                    "factory-status",
                    "factory status",
                )
            )

            if not factory_only:
                return False

        if any(term in normalized for term in cls._terms("factoryStatus", "terms")):
            if any(
                term in normalized
                for term in cls._terms("factoryStatus", "excludeWhenProductionPlaybook")
            ) and not any(
                marker in normalized
                for marker in ("fabril", "fabrica", "fábrica", "completo na")
            ):
                return False

            return True

        if any(term in normalized for term in cls._terms("factoryStatus", "colloquialTerms")):
            return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
                normalized
            ) is not None

        lowered = normalized.lower()

        return cls._has_product_scope_reference(normalized) and any(
            marker in lowered
            for marker in ("fabril", "fabrica", "fábrica")
        )

    @classmethod
    def _looks_like_production_status_question(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._terms("productionStatus", "terms")):
            return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
                normalized
            ) is not None

        lowered = normalized.lower()

        if not cls._has_product_scope_reference(normalized):
            return False

        production_markers = (
            "apontamento",
            " sh6010",
            "ordem de produc",
            "ordem de produ",
            " op ",
            " ops ",
            "playbook produtivo",
        )

        return any(marker in lowered for marker in production_markers)

    @classmethod
    def _looks_like_shipping_status_question(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._terms("shippingStatus", "terms")):
            if any(
                term in normalized
                for term in cls._terms("shippingStatus", "excludeWhenQualityInspection")
            ) and not any(
                marker in normalized
                for marker in (
                    "expedicao",
                    "expedição",
                    "inspecao final",
                    "inspeção final",
                    "liberado para exped",
                    "shipping-status",
                )
            ):
                return False

            return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
                normalized
            ) is not None

        lowered = normalized.lower()

        if not cls._has_product_scope_reference(normalized):
            return False

        shipping_markers = (
            "inspecao final",
            "inspeção final",
            "liberado para exped",
            "quantidade exped",
            "quanto exped",
            "pa finalizado",
            "pa liberado",
        )

        return any(marker in lowered for marker in shipping_markers)

    @classmethod
    def _looks_like_exclusive_raw_material_catalog_question(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._terms("exclusiveRawMaterialCatalog", "excludeTerms")):
            return False

        has_catalog_term = any(
            term in normalized for term in cls._terms("exclusiveRawMaterialCatalog", "terms")
        )
        exclusivity_markers = (
            "exclusiv",
            "mp exclus",
            "materia prima exclus",
            "materia-prima exclus",
            "materias-primas exclus",
        )
        has_exclusivity = has_catalog_term or any(
            marker in normalized for marker in exclusivity_markers
        )
        if not has_exclusivity:
            return False

        if cls._looks_like_structure_exclusivity_question(normalized):
            return False

        if cls.extract_product_code(normalized) and cls._has_product_scope_reference(normalized):
            return False

        return any(
            marker in normalized
            for marker in cls._terms("exclusiveRawMaterialCatalog", "globalMarkers")
        )

    @classmethod
    def _looks_like_structure_exclusivity_question(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._terms("structureExclusivity", "terms")):
            if not cls.extract_product_code(normalized) and any(
                marker in normalized
                for marker in cls._terms("exclusiveRawMaterialCatalog", "globalMarkers")
            ):
                return False

            return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
                normalized
            ) is not None

        lowered = normalized.lower()

        if not cls._has_product_scope_reference(normalized):
            return False

        if not cls.extract_product_code(normalized) and any(
            marker in normalized
            for marker in cls._terms("exclusiveRawMaterialCatalog", "globalMarkers")
        ):
            return False

        exclusivity_markers = (
            "exclusiv",
            "mp exclus",
            "materia prima exclus",
            "matéria-prima exclus",
            "matéria prima exclus",
        )

        return any(marker in lowered for marker in exclusivity_markers)

    @classmethod
    def _looks_like_sale_pricing_question(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._terms("salePricing", "terms"))

    @classmethod
    def _looks_like_price_analysis_question(cls, normalized: str) -> bool:
        if not re.search(r"\banalis", normalized):
            return False

        if not any(term in normalized for term in cls._terms("priceAnalysis", "terms")):
            return False

        if any(
            term in normalized
            for term in cls._terms("analyser", "genericAnalysisExclude")
        ):
            return False

        if cls._looks_like_production_status_question(normalized):
            return False

        if cls._looks_like_raw_material_price_intelligence_question(normalized):
            return False

        return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
            normalized
        ) is not None

    @classmethod
    def _looks_like_raw_material_price_intelligence_question(cls, normalized: str) -> bool:
        if cls._looks_like_sale_pricing_question(normalized):
            return False

        if cls._looks_like_cost_impact_simulation_question(normalized):
            return False

        if any(term in normalized for term in cls._terms("purchasePriceHistory", "terms")):
            return False

        if any(term in normalized for term in cls._terms("purchaseBudgetHistory", "terms")):
            return False

        if any(
            term in normalized
            for term in cls._terms("rawMaterialPriceIntelligence", "excludeWhenSalePricing")
        ):
            return False

        if any(term in normalized for term in cls._terms("rawMaterialPriceIntelligence", "terms")):
            return (
                cls._has_product_scope_reference(normalized)
                or cls.extract_product_code(normalized) is not None
                or cls._looks_like_raw_material_scope_shorthand(normalized)
            )

        return False

    @classmethod
    def _looks_like_raw_material_scope_shorthand(cls, normalized: str) -> bool:
        if re.search(r"\bmp\b", normalized):
            return True

        return any(
            marker in normalized
            for marker in (
                "materia prima",
                "materia-prima",
                "mate prima",
            )
        )

    @classmethod
    def _looks_like_cost_impact_simulation_question(cls, normalized: str) -> bool:
        if any(
            term in normalized
            for term in cls._terms("costImpactSimulation", "excludeWhenFactoryStatus")
        ) and not any(
            marker in normalized
            for marker in (
                "impacto",
                "pareto",
                "simul",
                "reajuste",
                "cost-impact",
            )
        ):
            return False

        if any(term in normalized for term in cls._terms("costImpactSimulation", "terms")):
            return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
                normalized
            ) is not None

        lowered = normalized.lower()

        if not cls._has_product_scope_reference(normalized):
            return False

        cost_markers = (
            "impacto de custo",
            "impacto no custo",
            "materiais que mais impactam",
            "materiais que impactam",
            "pareto",
            "simular aumento",
            "simule aumento",
            "reajuste percentual",
            "ranking custo",
        )

        return any(marker in lowered for marker in cost_markers)

    @classmethod
    def _looks_like_directives_question(cls, normalized: str) -> bool:
        if not any(term in normalized for term in cls._terms("directives", "terms")):
            return False

        return cls.extract_product_code(normalized) is not None or cls._has_product_scope_reference(
            normalized
        )

    @classmethod
    def _looks_like_last_purchase_question(cls, normalized: str) -> bool:
        if cls._looks_like_directives_question(normalized):
            return False

        if cls._looks_like_raw_material_price_intelligence_question(normalized):
            return False

        if cls._looks_like_sale_pricing_question(normalized):
            return False

        if any(term in normalized for term in cls._terms("lastPurchase", "terms")):
            return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
                normalized
            ) is not None

        if (
            ("ultima compra" in normalized or "última compra" in normalized)
            and any(marker in normalized for marker in ("icms", "fornecedor", " nf"))
        ):
            return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
                normalized
            ) is not None

        return False

    @classmethod
    def _looks_like_purchase_price_history_question(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._terms("purchasePriceHistory", "terms")):
            return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
                normalized
            ) is not None

        return False

    @classmethod
    def _looks_like_purchase_budget_history_question(cls, normalized: str) -> bool:
        if cls._looks_like_raw_material_price_intelligence_question(normalized):
            return False

        if any(term in normalized for term in cls._terms("purchaseBudgetHistory", "terms")):
            return cls._has_product_scope_reference(normalized) or cls.extract_product_code(
                normalized
            ) is not None

        return False

    @classmethod
    def _looks_like_stock_question(cls, normalized: str) -> bool:
        if any(
            term in normalized
            for term in cls._terms("stock", "excludeAggregateWithoutCode")
        ) and not cls.extract_product_code(normalized):
            return False

        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )

        if ChatProductPluralPhrasingService.matches_scope_linked_to_products(
            normalized,
            scope="stock",
        ):
            return True

        return any(term in normalized for term in cls._terms("stock", "terms"))

    @classmethod
    def _looks_like_generic_product_analysis_question(cls, normalized: str) -> bool:
        """«Analise produto …» sem escopo operacional explícito → analyser integrado."""
        if "produt" not in normalized:
            return False

        if not re.search(r"\banalis", normalized):
            return False

        if any(
            term in normalized
            for term in cls._terms("analyser", "genericAnalysisExclude")
        ):
            return False

        if any(
            term in normalized for term in cls._terms("operationalAmbiguityScopeTerms")
        ):
            return False

        return True

    @classmethod
    def _looks_like_full_analyser_question(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if any(
            term in normalized for term in cls._terms("analyser", "fullQuestion")
        ):
            return True

        if cls._looks_like_generic_product_analysis_question(normalized):
            return True

        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )

        scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(message)

        return ChatProductMultiScopePlanningService.should_use_single_analyser(
            scopes,
            message,
        )

    @classmethod
    def _looks_like_product_summary_question(cls, normalized: str) -> bool:
        if any(
            term in normalized for term in cls._terms("analyser", "summaryExclude")
        ):
            return False

        if any(
            term in normalized for term in cls._terms("analyser", "summaryExplicit")
        ):
            return True

        if "resumo" not in normalized:
            return False

        if any(
            term in normalized
            for term in cls._terms("analyser", "summaryExcludeWhenResumo")
        ):
            return False

        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )

        return ChatProductPluralPhrasingService.has_product_entity_reference(normalized)

    @classmethod
    def _looks_like_description_question(cls, normalized: str) -> bool:
        from app.domain.services.chat_technical_description_intent_service import (
            ChatTechnicalDescriptionIntentService,
        )

        if ChatTechnicalDescriptionIntentService.requires_normas_knowledge(normalized):
            return False

        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )

        if ChatProductPluralPhrasingService.matches_scope_linked_to_products(
            normalized,
            scope="description",
        ):
            return True

        return any(term in normalized for term in cls._terms("description", "terms"))

    @classmethod
    def has_actionable_product_route_intent(
        cls,
        message: str,
        *,
        normalized: str | None = None,
        route_segment: str | None = None,
    ) -> bool:
        """Indica se a mensagem tem escopo operacional explícito para ranking heurístico."""
        if route_segment:
            return True

        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message
        )

        if (
            cls.refine_operational_intent_from_full(message, normalized=normalized_text)
            != ChatProductQueryIntent.FULL
        ):
            return True

        operational_markers = (
            cls._looks_like_directives_question,
            cls._looks_like_sale_pricing_question,
            cls._looks_like_cost_impact_simulation_question,
            cls._looks_like_raw_material_price_intelligence_question,
            cls._looks_like_last_purchase_question,
            cls._looks_like_purchase_price_history_question,
            cls._looks_like_purchase_budget_history_question,
            cls._looks_like_factory_status_question,
            cls._looks_like_production_status_question,
            cls._looks_like_shipping_status_question,
            cls._looks_like_structure_exclusivity_question,
            cls._looks_like_billing_question,
            cls._looks_like_price_analysis_question,
            cls._looks_like_full_analyser_question,
            cls._looks_like_exclusive_raw_material_catalog_question,
        )

        if any(marker(normalized_text) for marker in operational_markers):
            return True

        from app.domain.services.chat_product_overview_intent_service import (
            ChatProductOverviewIntentService,
        )

        if ChatProductOverviewIntentService.is_product_overview_message(message):
            return True

        if cls._looks_like_product_sub_intent(normalized_text):
            return True

        if cls._looks_like_product_summary_route_question(normalized_text):
            return True

        return False

    @classmethod
    def _looks_like_purchases_route_question(cls, normalized: str) -> bool:
        if not any(term in normalized for term in cls._terms("purchases", "terms")):
            return False

        return not (
            cls._looks_like_last_purchase_question(normalized)
            or cls._looks_like_purchase_price_history_question(normalized)
            or cls._looks_like_purchase_budget_history_question(normalized)
            or cls._looks_like_raw_material_price_intelligence_question(normalized)
        )

    @classmethod
    def _looks_like_product_summary_route_question(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._terms("analyser", "summaryExplicit")):
            return True

        return (
            "resumo" in normalized
            and "completo" not in normalized
            and "ficha" not in normalized
            and "kaizen" not in normalized
        )

    @classmethod
    def _looks_like_guide_route_question(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._terms("router", "guideTerms"))

    @classmethod
    def _looks_like_generic_pricing_route_question(cls, normalized: str) -> bool:
        if cls._looks_like_sale_pricing_question(normalized):
            return False

        return any(term in normalized for term in cls._terms("router", "priceTerms"))

    @classmethod
    def _looks_like_invoices_route_question(cls, normalized: str) -> bool:
        return any(term in normalized for term in cls._terms("invoices", "terms"))

    @classmethod
    def _looks_like_suppliers_route_question(cls, normalized: str) -> bool:
        if not any(term in normalized for term in cls._terms("suppliers", "terms")):
            return False

        return bool(re.search(r"\bfornece\b", normalized)) or "fornecedor" in normalized

    @classmethod
    def _looks_like_inspection_route_question(cls, normalized: str) -> bool:
        if not any(term in normalized for term in cls._terms("inspection", "terms")):
            return False

        return not cls._looks_like_shipping_status_question(normalized)

    @classmethod
    def refine_operational_intent_from_full(
        cls,
        message: str,
        *,
        normalized: str | None = None,
    ) -> str:
        """Refina intent FULL para escopo operacional explícito na mensagem."""
        normalized_text = normalized or ChatMessageNormalizationService.normalize_for_matching(
            message
        )

        if cls._looks_like_explicit_playbook_product_scope(normalized_text):
            return ChatProductQueryIntent.FULL

        if cls._looks_like_structure_question(normalized_text):
            return ChatProductQueryIntent.STRUCTURE

        if cls._looks_like_sales_question(normalized_text):
            return ChatProductQueryIntent.SALES

        if cls._looks_like_stock_question(normalized_text):
            return ChatProductQueryIntent.STOCK

        if cls._looks_like_parents_question(normalized_text):
            return ChatProductQueryIntent.PARENTS

        if cls._looks_like_description_question(normalized_text):
            return ChatProductQueryIntent.DESCRIPTION

        if cls._looks_like_full_analyser_question(normalized_text):
            return ChatProductQueryIntent.ANALYSER

        from app.domain.services.chat_product_multi_scope_planning_service import (
            ChatProductMultiScopePlanningService,
        )

        scopes = ChatProductMultiScopePlanningService.extract_requested_scopes(message)

        if len(scopes) == 1:
            scope_to_intent = {
                "structure": ChatProductQueryIntent.STRUCTURE,
                "stock": ChatProductQueryIntent.STOCK,
                "parents": ChatProductQueryIntent.PARENTS,
                "sales": ChatProductQueryIntent.SALES,
                "profile": ChatProductQueryIntent.DESCRIPTION,
            }
            mapped = scope_to_intent.get(scopes[0])

            if mapped:
                return mapped

        return ChatProductQueryIntent.FULL

    @classmethod
    def _looks_like_parents_question(cls, normalized: str) -> bool:
        if re.search(
            r"\bonde\b(?:\s+(?:o|os|a|as|esse|este)\s+(?:produto|produtos|item|itens))?\s+.*?\b(?:e\s+)?usad[oa]s?\b",
            normalized,
        ):
            return True

        if re.search(r"\bonde\s+(?:sao|e|estao|estão)\s+usad[oa]s?\b", normalized):
            return True

        if re.search(
            r"\bem\s+quais\s+produtos\s+(?:sao|e|estao|estão)\s+usad[oa]s?\b",
            normalized,
        ):
            return True

        if re.search(
            r"\bem\s+quais\s+itens\s+(?:sao|e|estao|estão)\s+usad[oa]s?\b",
            normalized,
        ):
            return True

        return any(term in normalized for term in cls._terms("parents", "terms"))

    @classmethod
    def _looks_like_structure_question(cls, normalized: str) -> bool:
        from app.domain.services.chat_product_plural_phrasing_service import (
            ChatProductPluralPhrasingService,
        )

        return ChatProductPluralPhrasingService.matches_scope_linked_to_products(
            normalized,
            scope="structure",
        )

    @classmethod
    def _looks_like_product_sub_intent(cls, normalized: str) -> bool:
        """Reconhece perguntas sobre aspectos específicos de um produto que
        implicam necessidade de código (ex: 'qual o roteiro?', 'fornecedores?')."""
        return any(
            term in normalized for term in cls._terms("productSubIntent", "terms")
        )
