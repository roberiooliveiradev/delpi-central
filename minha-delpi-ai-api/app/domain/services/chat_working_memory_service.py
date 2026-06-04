"""Memória de trabalho da sessão — contexto, instruções e referências.

Foco operacional (código, filial, etc.) é exposto só como itens de contexto
(`userContextItems`, kind «context»). ``operationalFocus`` é cache derivado por
``ChatUserContextItemService.sync_operational_focus`` — uso interno (tools,
follow-up), nunca editável pelo usuário.
"""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_behavior_instruction_service import (
    ChatBehaviorInstructionService,
)
from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)


class ChatWorkingMemoryService:

    @classmethod
    def build_pre_turn_snapshot(
        cls,
        *,
        message: str,
        previous_messages: list[Any] | None,
    ) -> dict:
        carryover_entities, previous_product_codes = cls._extract_carryover_from_history(
            previous_messages
        )
        operational_focus = cls._extract_operational_focus_from_messages(previous_messages)
        operational_focus = {**carryover_entities, **operational_focus}
        cls._annotate_product_code_source(
            operational_focus,
            message=message,
            previous_messages=previous_messages,
        )
        behavior = cls._merge_behavior_instructions(message, previous_messages)
        from app.domain.services.chat_email_preference_service import (
            ChatEmailPreferenceService,
        )
        from app.domain.services.chat_text_correction_preference_service import (
            ChatTextCorrectionPreferenceService,
        )

        from app.domain.services.chat_text_task_preference_service import (
            ChatTextTaskPreferenceService,
        )

        behavior = ChatEmailPreferenceService.merge_into_behavior(message, behavior)
        behavior = ChatTextCorrectionPreferenceService.merge_into_behavior(message, behavior)
        behavior = ChatTextTaskPreferenceService.merge_into_behavior(message, behavior)

        snapshot = {
            "operationalFocus": operational_focus,
            "behaviorInstructions": behavior,
        }
        ChatEmailPreferenceService.apply_to_snapshot(snapshot, message=message)
        ChatTextCorrectionPreferenceService.apply_to_snapshot(snapshot, message=message)
        ChatTextTaskPreferenceService.apply_to_snapshot(snapshot, message=message)
        email_preferences = snapshot.get("emailPreferences") or {}
        text_correction_preferences = snapshot.get("textCorrectionPreferences") or {}

        resolved, used_keys = ChatReferenceResolutionService.resolve(
            message,
            operational_focus,
        )
        follow_up = ChatFollowUpIntentService.is_operational_follow_up(message)

        return cls._sync_focus_to_context_items(
            {
                "operationalFocus": operational_focus,
                "previousProductCodes": previous_product_codes,
                "behaviorInstructions": behavior,
                "emailPreferences": email_preferences,
                "textCorrectionPreferences": text_correction_preferences,
                "resolvedReferences": resolved,
                "usedMemoryKeys": used_keys,
                "followUpDetected": follow_up,
                "followUpType": ChatFollowUpIntentService.follow_up_type(message)
                if follow_up
                else None,
            }
        )

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

        previous_product_codes = list(snapshot.get("previousProductCodes") or [])

        if snapshot.get("persistedMemoryCleared"):
            entities: dict[str, str] = {}
            previous_product_codes = []
        else:
            entities = dict(snapshot.get("operationalFocus") or {})

        for code in cls._extract_codes_from_tool_calls(tool_calls):
            cls._record_product_switch(
                entities,
                previous_product_codes,
                code,
            )
            break

        explicit_code = ChatProductQueryIntentService.extract_product_code(message)

        if explicit_code:
            cls._record_product_switch(
                entities,
                previous_product_codes,
                explicit_code,
            )

        for branch in cls._extract_branches_from_tool_calls(tool_calls):
            entities["branch"] = branch
            break

        cls._annotate_product_code_source(
            entities,
            message=message,
            previous_messages=previous_messages,
            tool_calls=tool_calls,
        )

        snapshot["operationalFocus"] = entities
        snapshot["previousProductCodes"] = previous_product_codes[-8:]
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

        from app.domain.services.chat_email_preference_service import (
            ChatEmailPreferenceService,
        )
        from app.domain.services.chat_text_correction_preference_service import (
            ChatTextCorrectionPreferenceService,
        )
        from app.domain.services.chat_text_task_preference_service import (
            ChatTextTaskPreferenceService,
        )

        ChatEmailPreferenceService.apply_to_snapshot(snapshot, message=message)
        ChatTextCorrectionPreferenceService.apply_to_snapshot(snapshot, message=message)
        ChatTextTaskPreferenceService.apply_to_snapshot(snapshot, message=message)

        return cls._sync_focus_to_context_items(snapshot)

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str:
        if not snapshot:
            return ""

        lines: list[str] = []

        last_action = snapshot.get("lastAction")

        if isinstance(last_action, dict) and last_action.get("name"):
            params = last_action.get("params") or {}
            param_hint = ", ".join(f"{k}={v}" for k, v in params.items() if v)

            if param_hint:
                lines.append(
                    f"- Última consulta: {last_action['name']} ({param_hint})."
                )
            else:
                lines.append(f"- Última consulta: {last_action['name']}.")

        behavior = snapshot.get("behaviorInstructions") or {}

        if behavior.get("responseFormat") == "table":
            lines.append("- Preferência ativa: responder em tabela quando couber.")

        email_raw = behavior.get("emailWriting")

        if email_raw:
            import json

            try:
                email_prefs = json.loads(email_raw) if isinstance(email_raw, str) else email_raw
            except json.JSONDecodeError:
                email_prefs = {}

            if isinstance(email_prefs, dict):
                from app.domain.services.chat_email_preference_service import (
                    ChatEmailPreferenceService,
                )

                pref_block = ChatEmailPreferenceService.format_prompt_block(
                    {k: bool(v) for k, v in email_prefs.items()}
                )

                if pref_block:
                    lines.append(pref_block.replace("Preferências de e-mail nesta sessão:", "- E-mail:"))

        correction_raw = behavior.get("textCorrection")

        if correction_raw:
            import json

            try:
                correction_prefs = (
                    json.loads(correction_raw)
                    if isinstance(correction_raw, str)
                    else correction_raw
                )
            except json.JSONDecodeError:
                correction_prefs = {}

            if isinstance(correction_prefs, dict):
                from app.domain.services.chat_text_correction_preference_service import (
                    ChatTextCorrectionPreferenceService,
                )

                correction_block = ChatTextCorrectionPreferenceService.format_prompt_block(
                    {k: bool(v) for k, v in correction_prefs.items()}
                )

                if correction_block:
                    lines.append(
                        correction_block.replace(
                            "Preferências de correção nesta sessão:",
                            "- Correção:",
                        )
                    )

        text_raw = behavior.get("textTaskWriting")

        if text_raw:
            import json

            try:
                text_prefs = json.loads(text_raw) if isinstance(text_raw, str) else text_raw
            except json.JSONDecodeError:
                text_prefs = {}

            if isinstance(text_prefs, dict) and text_prefs:
                from app.domain.services.chat_text_task_preference_service import (
                    ChatTextTaskPreferenceService,
                )

                text_block = ChatTextTaskPreferenceService.format_prompt_block(
                    {"workingMemory": {"preferences": {"textTask": text_prefs}}}
                )

                if text_block:
                    lines.append(
                        text_block.replace(
                            "Preferências textuais da sessão:",
                            "- Texto:",
                        )
                    )

        tone = behavior.get("tone")

        if tone == "direct":
            lines.append("- Preferência ativa: tom direto e objetivo.")
        elif tone == "simple":
            lines.append("- Preferência ativa: linguagem simples.")
        elif tone == "formal":
            lines.append("- Preferência ativa: tom formal.")

        if behavior.get("answerLength") == "short":
            lines.append("- Preferência ativa: respostas curtas.")

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

        behavior = snapshot.get("behaviorInstructions") or {}
        context_items = cls._merged_user_context_items(snapshot)

        return {
            "loaded": True,
            "activeContextItems": [
                str(item.get("label") or "").strip()
                for item in context_items
                if isinstance(item, dict) and item.get("label")
            ],
            "activeBehaviorInstructions": behavior,
            "emailPreferences": snapshot.get("emailPreferences") or {},
            "resolvedReferences": snapshot.get("resolvedReferences") or [],
            "followUpDetected": bool(snapshot.get("followUpDetected")),
            "usedMemoryKeys": snapshot.get("usedMemoryKeys") or [],
            "clearedThisTurn": bool(snapshot.get("persistedMemoryCleared")),
        }

    @classmethod
    def _extract_carryover_from_history(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[dict[str, str], list[str]]:
        for item in reversed(previous_messages or []):
            if cls._message_role(item) != "assistant":
                continue

            metadata = item.get("metadata") if isinstance(item, dict) else None

            if not isinstance(metadata, dict):
                continue

            snapshot = metadata.get("contextSnapshot")

            if not isinstance(snapshot, dict):
                continue

            entities = snapshot.get("operationalFocus") or {}
            previous_codes = [
                str(code).strip()
                for code in (snapshot.get("previousProductCodes") or [])
                if str(code).strip()
            ]

            if isinstance(entities, dict) and entities:
                return dict(entities), previous_codes

            if previous_codes:
                return {}, previous_codes

        return {}, []

    @classmethod
    def _record_product_switch(
        cls,
        entities: dict[str, str],
        previous_product_codes: list[str],
        new_code: str,
    ) -> None:
        token = str(new_code or "").strip()
        previous = str(entities.get("productCode") or "").strip()

        if previous and previous != token and previous not in previous_product_codes:
            previous_product_codes.append(previous)

        if token:
            entities["productCode"] = token

    @classmethod
    def _extract_operational_focus_from_messages(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, str]:
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
    def _merged_user_context_items(cls, snapshot: dict | None) -> list[dict[str, Any]]:
        """Une itens persistidos com foco operacional derivado do snapshot."""
        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        snap = snapshot or {}
        items = [
            item
            for item in (snap.get("userContextItems") or [])
            if isinstance(item, dict) and item.get("id")
        ]
        auto = ChatUserContextItemService.auto_items_from_entities(
            snap.get("operationalFocus") or {},
            items,
        )

        if auto:
            items = (items + auto)[-12:]

        return items

    @classmethod
    def _sync_focus_to_context_items(cls, snapshot: dict) -> dict:
        """Persiste foco operacional apenas em userContextItems."""
        result = dict(snapshot)
        merged = cls._merged_user_context_items(result)

        if merged:
            result["userContextItems"] = merged

        return result

    @classmethod
    def build_context_chips(cls, snapshot: dict | None) -> list[dict[str, str]]:
        if not snapshot:
            return []

        from app.domain.services.chat_user_context_item_service import (
            ChatUserContextItemService,
        )

        chips: list[dict[str, str]] = list(
            ChatUserContextItemService.chips_from_items(
                cls._merged_user_context_items(snapshot),
            )
        )
        behavior = snapshot.get("behaviorInstructions") or {}

        from app.domain.services.chat_email_preference_service import (
            ChatEmailPreferenceService,
        )

        chips.extend(
            ChatEmailPreferenceService.build_context_chips(snapshot.get("emailPreferences"))
        )

        from app.domain.services.chat_text_correction_preference_service import (
            ChatTextCorrectionPreferenceService,
        )

        chips.extend(
            ChatTextCorrectionPreferenceService.build_context_chips(
                snapshot.get("textCorrectionPreferences")
            )
        )

        if behavior.get("responseFormat") == "table":
            chips.append({"label": "Tabela", "kind": "format", "value": "table"})

        tone = behavior.get("tone")

        if tone == "direct":
            chips.append({"label": "Tom direto", "kind": "tone", "value": "direct"})
        elif tone == "simple":
            chips.append({"label": "Linguagem simples", "kind": "tone", "value": "simple"})
        elif tone == "formal":
            chips.append({"label": "Tom formal", "kind": "tone", "value": "formal"})

        if behavior.get("answerLength") == "short":
            chips.append({"label": "Respostas curtas", "kind": "preference", "value": "short"})

        if behavior.get("finalVersionOnly"):
            chips.append({"label": "Só versão final", "kind": "preference", "value": "final_only"})

        return chips

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

    _PRODUCT_CONTEXT_TOKENS = (
        "produto",
        "sku",
        "ficha do",
        "cadastro do",
        "estoque",
        "fornecedor",
        "fornece",
        "estrutura do",
        "roteiro",
        "inspecao",
        "inspeção",
        "onde e usado",
        "onde é usado",
        "componentes",
        "where used",
        "bom do",
    )

    @classmethod
    def _message_has_product_context(cls, *texts: Any) -> bool:
        for text in texts:
            normalized = ChatMessageNormalizationService.normalize_for_matching(text)

            if normalized and any(
                token in normalized for token in cls._PRODUCT_CONTEXT_TOKENS
            ):
                return True

        return False

    @classmethod
    def _recent_product_tool_code(cls, previous_messages: list[Any] | None) -> str | None:
        from app.domain.services.chat_analysis_intent_service import (
            ChatAnalysisIntentService,
        )

        for item in reversed((previous_messages or [])[-16:]):
            metadata = item.get("metadata") if isinstance(item, dict) else None

            if not isinstance(metadata, dict):
                continue

            for tool_call in reversed(metadata.get("toolCalls") or []):
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                code = ChatAnalysisIntentService.extract_product_code_from_tool_path(
                    str(tool_meta.get("path") or ""),
                )

                if code:
                    return code

        return None

    @classmethod
    def _annotate_product_code_source(
        cls,
        entities: dict[str, str],
        *,
        message: str,
        previous_messages: list[Any] | None = None,
        tool_calls: list | None = None,
    ) -> None:
        """Define a proveniência do productCode para itens de contexto (auto).

        Só códigos com origem forte (tool de produto executada ou menção
        explícita a produto) viram item de contexto. Códigos inferidos de
        outra consulta (ex.: cliente em SQL) não entram no contexto ativo.
        """
        code = str(entities.get("productCode") or "").strip()

        if not code:
            entities.pop("productCodeSource", None)
            return

        tool_codes: set[str] = set(cls._extract_codes_from_tool_calls(tool_calls))
        recent_tool = cls._recent_product_tool_code(previous_messages)

        if recent_tool:
            tool_codes.add(recent_tool)

        if code in tool_codes:
            entities["productCodeSource"] = "tool"
            return

        if cls._message_has_product_context(message):
            entities["productCodeSource"] = "explicit"
            return

        for item in reversed((previous_messages or [])[-6:]):
            if cls._message_role(item) != "user":
                continue

            content = cls._message_content(item)

            if code in content and cls._message_has_product_context(content):
                entities["productCodeSource"] = "explicit"
                return

        entities["productCodeSource"] = "inferred"

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
