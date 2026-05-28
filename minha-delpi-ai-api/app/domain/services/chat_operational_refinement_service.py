"""Refinamentos operacionais em cima do turno anterior (filtro de filial, etc.)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


@dataclass(frozen=True)
class OperationalRefinement:
    kind: str
    product_code: str
    branch: str | None = None
    warehouse: str | None = None
    reason: str = ""


class ChatOperationalRefinementService:
    _FILTER_TERMS = (
        "filtre",
        "filtro",
        "filtrar",
        "filtra ",
        "mostre só",
        "mostre so",
        "só a filial",
        "so a filial",
        "apenas filial",
        "somente filial",
        "somente a filial",
        "restrinja",
        "restringe",
        "limitar a filial",
        "limita a filial",
    )
    _BRANCH_RE = re.compile(
        r"\b(?:filial|fil\.?)\s*[_-]?\s*(\d{1,2})\b",
        re.IGNORECASE,
    )
    _WAREHOUSE_RE = re.compile(
        r"\b(?:armaz[eé]m|arm\.?|deposito|depósito)\s*[_-]?\s*(\d{1,3})\b",
        re.IGNORECASE,
    )

    @classmethod
    def detect(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> OperationalRefinement | None:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not cls.looks_like_operational_refinement(normalized):
            return None

        if not cls._has_recent_stock_context(
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return None

        product_code = ChatProductQueryIntentService.extract_product_code(message)

        if not product_code:
            product_code = ChatProductQueryIntentService.resolve_product_code(
                message,
                conversation_context,
            )

        if not product_code and previous_messages:
            product_code = cls._product_code_from_messages(previous_messages)

        if not product_code:
            return None

        branch = cls.extract_branch_code(normalized)
        warehouse = cls.extract_warehouse_code(normalized)

        if branch or warehouse or cls._requires_stock_refinement(normalized):
            return OperationalRefinement(
                kind="stock_refinement",
                product_code=product_code,
                branch=branch,
                warehouse=warehouse,
                reason="A mensagem refina a consulta de estoque já feita nesta conversa.",
            )

        return None

    @classmethod
    def looks_like_operational_refinement(cls, normalized: str) -> bool:
        if any(term in normalized for term in cls._FILTER_TERMS):
            return True

        if "filial" in normalized and any(
            term in normalized
            for term in ("filtre", "filtro", "filtrar", "só", "so", "apenas", "somente")
        ):
            return True

        return False

    @classmethod
    def is_operational_follow_up(
        cls,
        message: str,
        *,
        conversation_context: str | None = None,
        previous_messages: list[Any] | None = None,
    ) -> bool:
        if cls.detect(
            message,
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        ):
            return True

        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not ChatProductQueryIntentService.references_previous_product(message):
            return False

        return cls._has_recent_stock_context(
            conversation_context=conversation_context,
            previous_messages=previous_messages,
        )

    @classmethod
    def extract_branch_code(cls, normalized: str) -> str | None:
        match = cls._BRANCH_RE.search(normalized)

        if not match:
            return None

        return str(match.group(1)).zfill(2)

    @classmethod
    def extract_warehouse_code(cls, normalized: str) -> str | None:
        match = cls._WAREHOUSE_RE.search(normalized)

        if not match:
            return None

        return str(match.group(1)).zfill(2)

    @classmethod
    def _requires_stock_refinement(cls, normalized: str) -> bool:
        return "filial" in normalized or "armazem" in normalized or "armazém" in normalized

    @classmethod
    def _has_recent_stock_context(
        cls,
        *,
        conversation_context: str | None,
        previous_messages: list[Any] | None,
    ) -> bool:
        if conversation_context:
            lowered = conversation_context.lower()

            if "/stock" in lowered or "estoque do produto" in lowered:
                return True

        for item in reversed((previous_messages or [])[-10:]):
            metadata = cls._message_metadata(item)

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

            content = cls._message_content(item).lower()

            if "estoque do produto" in content or "estoque por filial" in content:
                return True

        return False

    @classmethod
    def _product_code_from_messages(cls, previous_messages: list[Any]) -> str | None:
        for item in reversed(previous_messages[-12:]):
            code = ChatProductQueryIntentService.extract_product_code(
                cls._message_content(item)
            )

            if code:
                return code

        return None

    @classmethod
    def _message_metadata(cls, message: Any) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")
            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}

    @classmethod
    def _message_content(cls, message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")
