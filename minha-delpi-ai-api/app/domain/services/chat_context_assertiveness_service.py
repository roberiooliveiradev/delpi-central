"""Pontua assertividade contextual do turno (Fase 5 — avaliação automática)."""

from __future__ import annotations

import re
from typing import Any


class ChatContextAssertivenessService:
    @classmethod
    def evaluate_turn(
        cls,
        *,
        message: str,
        answer: str,
        tool_calls: list | None,
        snapshot: dict | None,
    ) -> dict:
        flags: list[str] = []
        score = 100.0

        snapshot = snapshot or {}
        entities = snapshot.get("operationalFocus") or {}
        resolved = snapshot.get("resolvedReferences") or []
        follow_up = bool(snapshot.get("followUpDetected"))
        product_in_memory = str(entities.get("productCode") or "").strip()

        message_codes = cls._extract_product_codes(message)
        tool_paths = cls._tool_paths(tool_calls)

        if follow_up and product_in_memory:
            if not message_codes and not cls._path_mentions_product(tool_paths, product_in_memory):
                flags.append("follow_up_without_entity_reuse")
                score -= 35.0
            elif cls._path_mentions_product(tool_paths, product_in_memory):
                flags.append("follow_up_entity_reused")

        if message_codes and product_in_memory and message_codes[-1] != product_in_memory:
            if follow_up and not any(
                str(item.get("value") or "") == message_codes[-1]
                for item in resolved
                if isinstance(item, dict)
            ):
                flags.append("stale_product_context")
                score -= 20.0

        if cls._asks_for_code_again(answer) and product_in_memory:
            flags.append("unnecessary_code_request")
            score -= 25.0

        if cls._answer_has_none_placeholders(answer):
            flags.append("humanized_none_fields")
            score -= 40.0

        wrong_action = cls._supplier_question_wrong_action(message, tool_paths)

        if wrong_action:
            flags.append(wrong_action)
            score -= 30.0

        score = max(0.0, min(100.0, round(score, 1)))

        return {
            "score": score,
            "flags": flags,
            "followUpDetected": follow_up,
            "followUpResolved": "follow_up_entity_reused" in flags,
        }

    @staticmethod
    def _extract_product_codes(message: str) -> list[str]:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )

        code = ChatProductQueryIntentService.extract_product_code(message)

        return [code] if code else []

    @staticmethod
    def _tool_paths(tool_calls: list | None) -> list[str]:
        paths: list[str] = []

        for tool_call in tool_calls or []:
            if not isinstance(tool_call, dict):
                continue

            metadata = tool_call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("path"):
                paths.append(str(metadata["path"]))

        return paths

    @staticmethod
    def _path_mentions_product(paths: list[str], product_code: str) -> bool:
        token = str(product_code or "").strip()

        if not token:
            return False

        return any(token in path for path in paths)

    @staticmethod
    def _asks_for_code_again(answer: str) -> bool:
        lowered = (answer or "").lower()

        return (
            "informe o código" in lowered
            or "informe o codigo" in lowered
            or "qual o código do produto" in lowered
        )

    @staticmethod
    def _answer_has_none_placeholders(answer: str) -> bool:
        return bool(re.search(r"\*\*None\*\*|: None\.|None,", answer or ""))

    @staticmethod
    def _supplier_question_wrong_action(message: str, paths: list[str]) -> str | None:
        lowered = (message or "").lower()

        if not re.search(r"\bfornec", lowered):
            return None

        if not paths:
            return None

        if any("/analyser" in path for path in paths) and not any(
            "supplier" in path.lower() or "fornec" in path.lower()
            for path in paths
        ):
            return "supplier_intent_used_analyser"

        return None
