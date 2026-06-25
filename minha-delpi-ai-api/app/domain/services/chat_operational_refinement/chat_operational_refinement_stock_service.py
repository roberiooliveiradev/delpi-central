"""Delegate — refinamento operacional."""

from __future__ import annotations

import json
import re
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntent,
    ChatProductQueryIntentService,
)
from app.domain.services.chat_route_context_service import (
    ChatRouteContextService,
)

from app.domain.services.chat_operational_refinement.chat_operational_refinement_facade_access import (
    refinement_service,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_models import (
    OperationalRefinement,
    RecentPaginatedAction,
)
from app.domain.services.chat_operational_refinement.chat_operational_refinement_vocabulary import (
    ChatOperationalRefinementVocabulary as VOCAB,
)



class ChatOperationalRefinementStockService:
    @classmethod
    def plan_stock_follow_ups(cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> list[OperationalRefinement]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not refinement_service()._has_recent_stock_context(
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return []

        product_codes = refinement_service()._collect_recent_stock_product_codes(previous_messages)

        if not product_codes:
            code = ChatProductQueryIntentService.resolve_product_code(
                message,
                conversation_context,
                previous_messages=previous_messages,
            )

            if code:
                product_codes = [code]

        if not product_codes:
            return []

        if refinement_service().looks_like_stock_scope_reset(normalized):
            return [
                OperationalRefinement(
                    kind="stock_reset",
                    product_code=code,
                    reason=(
                        "A mensagem pede o estoque completo novamente, sem filtro de filial."
                    ),
                )
                for code in product_codes
            ]

        if not refinement_service().looks_like_operational_refinement(normalized):
            return []

        branch = refinement_service().extract_branch_code(normalized)
        warehouse = refinement_service().extract_warehouse_code(normalized)

        if not branch and not warehouse and not refinement_service()._requires_stock_refinement(normalized):
            return []

        return [
            OperationalRefinement(
                kind="stock_refinement",
                product_code=code,
                branch=branch,
                warehouse=warehouse,
                reason="A mensagem refina a consulta de estoque já feita nesta conversa.",
            )
            for code in product_codes
        ]

    @classmethod
    def _has_recent_stock_context(cls,
        *,
        conversation_context: str | None,
        previous_messages: list[Any] | None,
    ) -> bool:
        if conversation_context:
            lowered = conversation_context.lower()

            if "/stock" in lowered or "estoque do produto" in lowered:
                return True

        for item in reversed((previous_messages or [])[-10:]):
            metadata = refinement_service()._message_metadata(item)

            for tool_call in metadata.get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").lower()
                action_id = str(tool_meta.get("actionId") or "").lower()

                if "/stock" in path or "product_stock" in action_id or "get_product_stock" in action_id:
                    return True

            content = refinement_service()._message_content(item).lower()

            if "estoque do produto" in content or "estoque por filial" in content:
                return True

        return False

    @classmethod
    def _collect_recent_stock_product_codes(cls,
        previous_messages: list[Any] | None,
    ) -> list[str]:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        for item in reversed((previous_messages or [])[-14:]):
            batch_codes: list[str] = []

            for tool_call in refinement_service()._message_metadata(item).get("toolCalls") or []:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata") or {}

                if not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "").lower()
                action_id = str(tool_meta.get("actionId") or "").lower()

                if "/stock" not in path and "product_stock" not in action_id:
                    continue

                code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

                if not code:
                    arguments = tool_call.get("arguments") or {}
                    parameters = arguments.get("parameters") or {}

                    if isinstance(parameters, dict):
                        for key in (
                            "code",
                            "product_code",
                            "productcode",
                            "codigo",
                            "cod_produto",
                        ):
                            raw = parameters.get(key)

                            if not raw:
                                continue

                            candidate = ChatProductQueryIntentService.normalize_product_code(
                                str(raw)
                            )

                            if candidate and not ChatAnalysisIntentService.looks_like_path_placeholder(
                                candidate
                            ):
                                code = candidate
                                break

                if code and code not in batch_codes:
                    batch_codes.append(code)

            if batch_codes:
                return batch_codes

        return []

    @classmethod
    def _product_code_from_messages(cls, previous_messages: list[Any]) -> str | None:
        for item in reversed(previous_messages[-12:]):
            code = ChatProductQueryIntentService.extract_product_code(
                refinement_service()._message_content(item)
            )

            if code:
                return code

        return None

