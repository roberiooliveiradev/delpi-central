"""Memória de trabalho estruturada da sessão (entidades, instruções, referências)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_behavior_instruction_service import (
    ChatBehaviorInstructionService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)


class ChatWorkingMemoryService:
    _FOLLOW_UP_PATTERNS = (
        r"\bfornecedores?\b",
        r"\bestoque\b",
        r"\broteiro\b",
        r"\bestrutura\b",
        r"\binspe[cç][aã]o\b",
        r"\bdescri[cç][aã]o\b",
        r"\bmais\s+informa",
        r"\bagora\b",
        r"\bdele\b",
        r"\bdesse\b",
        r"\bdessa\b",
        r"\besse\s+produto\b",
        r"\besse\s+item\b",
    )

    @classmethod
    def build_pre_turn_snapshot(
        cls,
        *,
        message: str,
        previous_messages: list[Any] | None,
    ) -> dict:
        last_entities = cls._extract_last_entities(previous_messages)
        behavior = cls._merge_behavior_instructions(message, previous_messages)
        resolved, used_keys = cls._resolve_references(message, last_entities)

        return {
            "lastEntities": last_entities,
            "behaviorInstructions": behavior,
            "resolvedReferences": resolved,
            "usedMemoryKeys": used_keys,
            "followUpDetected": cls._is_operational_follow_up(message),
        }

    @classmethod
    def build_post_turn_snapshot(
        cls,
        *,
        message: str,
        previous_messages: list[Any] | None,
        tool_calls: list | None,
        pre_snapshot: dict | None = None,
    ) -> dict:
        snapshot = dict(pre_snapshot or cls.build_pre_turn_snapshot(
            message=message,
            previous_messages=previous_messages,
        ))

        entities = dict(snapshot.get("lastEntities") or {})
        for code in cls._extract_codes_from_tool_calls(tool_calls):
            entities["productCode"] = code
            break

        for branch in cls._extract_branches_from_tool_calls(tool_calls):
            entities["branch"] = branch
            break

        snapshot["lastEntities"] = entities
        used = list(snapshot.get("usedMemoryKeys") or [])

        if entities.get("productCode") and "productCode" not in used:
            used.append("productCode")

        if entities.get("branch") and "branch" not in used:
            used.append("branch")

        for key in snapshot.get("behaviorInstructions") or {}:
            memory_key = f"behavior:{key}"

            if memory_key not in used:
                used.append(memory_key)

        snapshot["usedMemoryKeys"] = used
        return snapshot

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str:
        if not snapshot:
            return ""

        lines: list[str] = []
        entities = snapshot.get("lastEntities") or {}

        if entities.get("productCode"):
            lines.append(f"- Produto em foco: {entities['productCode']}.")

        if entities.get("branch"):
            lines.append(f"- Filial em foco: {entities['branch']}.")

        behavior = snapshot.get("behaviorInstructions") or {}

        if behavior.get("responseFormat") == "table":
            lines.append("- Preferência ativa: responder em tabela quando couber.")

        tone = behavior.get("tone")

        if tone == "direct":
            lines.append("- Preferência ativa: tom direto e objetivo.")
        elif tone == "simple":
            lines.append("- Preferência ativa: linguagem simples.")

        resolved = snapshot.get("resolvedReferences") or []

        for item in resolved:
            if not isinstance(item, dict):
                continue

            text = item.get("text")
            value = item.get("value")

            if text and value:
                lines.append(f'- Referência "{text}" → {value}.')

        if not lines:
            return ""

        return "Memória ativa da conversa:\n" + "\n".join(lines)

    @classmethod
    def merge_conversation_context(cls, memory_block: str, conversation_context: str | None) -> str | None:
        memory = str(memory_block or "").strip()
        context = str(conversation_context or "").strip()

        if memory and context:
            return f"{memory}\n\n{context}"

        if memory:
            return memory

        return context or None

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict:
        if not snapshot:
            return {"loaded": False}

        entities = snapshot.get("lastEntities") or {}
        behavior = snapshot.get("behaviorInstructions") or {}

        return {
            "loaded": True,
            "activeEntities": {
                key: value
                for key, value in entities.items()
                if value not in (None, "", [])
            },
            "activeBehaviorInstructions": behavior,
            "resolvedReferences": snapshot.get("resolvedReferences") or [],
            "followUpDetected": bool(snapshot.get("followUpDetected")),
            "usedMemoryKeys": snapshot.get("usedMemoryKeys") or [],
        }

    @classmethod
    def _extract_last_entities(cls, previous_messages: list[Any] | None) -> dict[str, str]:
        entities: dict[str, str] = {}
        code = ChatProductQueryIntentService.extract_last_product_code_from_messages(
            previous_messages,
        )

        if code:
            entities["productCode"] = code

        for item in reversed((previous_messages or [])[-12:]):
            content = cls._message_content(item)

            branch_match = re.search(r"\bfilial\s+(\d{2})\b", content, flags=re.IGNORECASE)

            if branch_match:
                entities["branch"] = branch_match.group(1)
                break

        return entities

    @classmethod
    def _merge_behavior_instructions(
        cls,
        message: str,
        previous_messages: list[Any] | None,
    ) -> dict[str, str]:
        merged: dict[str, str] = {}

        for item in (previous_messages or [])[-8:]:
            if cls._message_role(item) != "user":
                continue

            merged.update(ChatBehaviorInstructionService.detect(cls._message_content(item)))

        merged.update(ChatBehaviorInstructionService.detect(message))
        return merged

    @classmethod
    def _resolve_references(
        cls,
        message: str,
        last_entities: dict[str, str],
    ) -> tuple[list[dict], list[str]]:
        normalized = (message or "").strip().lower()
        used_keys: list[str] = []
        resolved: list[dict] = []

        if not cls._is_operational_follow_up(message):
            return resolved, used_keys

        product_code = last_entities.get("productCode")

        if product_code and not ChatProductQueryIntentService.extract_product_code(message):
            resolved.append(
                {
                    "text": "follow-up operacional",
                    "resolvedTo": "productCode",
                    "value": product_code,
                    "confidence": 0.9,
                }
            )
            used_keys.append("productCode")

        return resolved, used_keys

    @classmethod
    def _is_operational_follow_up(cls, message: str | None) -> bool:
        normalized = (message or "").strip().lower()

        if not normalized:
            return False

        if ChatProductQueryIntentService.extract_product_code(message):
            return False

        return any(re.search(pattern, normalized) for pattern in cls._FOLLOW_UP_PATTERNS)

    @classmethod
    def _extract_codes_from_tool_calls(cls, tool_calls: list | None) -> list[str]:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        codes: list[str] = []

        for tool_call in tool_calls or []:
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict):
                continue

            code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
                str(metadata.get("path") or ""),
            )

            if code:
                codes.append(code)

        return codes

    @classmethod
    def _extract_branches_from_tool_calls(cls, tool_calls: list | None) -> list[str]:
        branches: list[str] = []

        for tool_call in tool_calls or []:
            if not isinstance(tool_call, dict):
                continue

            args = tool_call.get("arguments")

            if not isinstance(args, dict):
                continue

            parameters = args.get("parameters")

            if not isinstance(parameters, dict):
                continue

            branch = parameters.get("branch") or parameters.get("branch_code")

            if branch not in (None, ""):
                branches.append(str(branch))

        return branches

    @staticmethod
    def _message_content(message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("content") or "")

        return str(getattr(message, "content", "") or "")

    @staticmethod
    def _message_role(message: Any) -> str:
        if isinstance(message, dict):
            return str(message.get("role") or "").strip().lower()

        return str(getattr(message, "role", "") or "").strip().lower()
