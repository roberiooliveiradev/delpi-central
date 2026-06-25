"""Resolução de entidades e parâmetros para roteamento de intenção."""

from __future__ import annotations

from typing import Any


class ChatIntentRouterEntityResolutionService:
    @staticmethod
    def working_memory_entities(workspace_context: dict | None) -> dict[str, str]:
        if not isinstance(workspace_context, dict):
            return {}

        working = workspace_context.get("workingMemory")

        if not isinstance(working, dict):
            return {}

        from app.domain.services.chat_snapshot_operational_focus import (
            ChatSnapshotOperationalFocus,
        )

        return ChatSnapshotOperationalFocus.get(working)

    @classmethod
    def resolve_entities_from_memory(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None,
        workspace_context: dict | None = None,
    ) -> dict[str, str] | None:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_reference_resolution_service import (
            ChatReferenceResolutionService,
        )

        wm_entities = cls.working_memory_entities(workspace_context)
        params: dict[str, str] = dict(wm_entities)

        if ChatProductQueryIntentService.looks_like_scope_reset_operational_query(message):
            params.pop("productCode", None)

        if previous_messages:
            from app.domain.services.chat_conversation_memory_extractor import (
                ChatConversationMemoryExtractor,
            )

            snapshot = ChatConversationMemoryExtractor.enrich_snapshot(
                {},
                previous_messages=previous_messages,
            )
            resolved, _keys = ChatReferenceResolutionService.resolve_from_snapshot(
                message,
                snapshot,
            )

            for item in resolved:
                key = str(item.get("key") or "").strip()
                value = str(item.get("value") or "").strip()

                if key and value:
                    params[key] = value

        code_in_message = ChatProductQueryIntentService.extract_product_code(message)
        working = workspace_context.get("workingMemory") if isinstance(workspace_context, dict) else {}
        code = ChatProductQueryIntentService.resolve_product_code(
            message,
            previous_messages=previous_messages,
            memory_snapshot=working if isinstance(working, dict) else None,
        )

        if code and not code_in_message and ChatProductQueryIntentService.should_inherit_product_code(
            message
        ):
            params.setdefault("productCode", code)

        if params:
            return params

        if not code or code_in_message:
            return None

        if not ChatProductQueryIntentService.should_inherit_product_code(message):
            return None

        return {"productCode": code}

    @classmethod
    def build_resolved_params(
        cls,
        message: str,
        *,
        previous_messages: list[Any] | None,
        memory_entities: dict[str, str] | None,
        workspace_context: dict | None = None,
    ) -> dict[str, str] | None:
        from app.domain.services.chat_product_query_intent_service import (
            ChatProductQueryIntentService,
        )
        from app.domain.services.chat_production_operational_intent_service import (
            ChatProductionOperationalIntentService,
            ProductionOperationalIntentKind,
        )

        params: dict[str, str] = dict(cls.working_memory_entities(workspace_context))

        if memory_entities:
            params.update(memory_entities)

        code_in_message = ChatProductQueryIntentService.extract_product_code(message)
        production_kind = ChatProductionOperationalIntentService.resolve(message)

        if production_kind == ProductionOperationalIntentKind.SCHEDULE_TODAY:
            group_code = ChatProductQueryIntentService.resolve_schedule_product_filter_code(
                message,
                product_code=params.get("productCode") or code_in_message,
            )

            if group_code:
                params["productGroup"] = group_code
                params.pop("productCode", None)
            elif code_in_message:
                params["productCode"] = code_in_message
        elif code_in_message:
            params["productCode"] = code_in_message

        return params or None
