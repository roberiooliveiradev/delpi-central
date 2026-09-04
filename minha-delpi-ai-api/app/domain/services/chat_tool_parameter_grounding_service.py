"""Preenche slots obrigatórios de actions a partir do contexto da conversa."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_snapshot_operational_focus import (
    ChatSnapshotOperationalFocus,
)
from app.domain.services.chat_tool_grounding_context_service import (
    ChatToolGroundingContextService,
)
from app.domain.services.chat_user_context_item_service import (
    ChatUserContextItemService,
)


class ChatToolParameterGroundingService:
    """Last-mile: injeta parâmetros known-from-context antes do validate."""

    _CODE_PARAM_NAMES = frozenset({"code", "productCode", "product_code"})

    @classmethod
    def ground_parameters(
        cls,
        action: dict | None,
        parameters: dict | None,
        *,
        message: str | None = None,
        conversation_context: str | None = None,
        previous_messages: list | None = None,
        memory_snapshot: dict | None = None,
    ) -> dict[str, Any]:
        grounded = dict(parameters or {})
        schema = action.get("parametersSchema") if isinstance(action, dict) else None

        if not isinstance(schema, list) or not schema:
            return grounded

        resolved_message = message if message not in (None, "") else (
            ChatToolGroundingContextService.current_message()
        )
        resolved_conversation = (
            conversation_context
            if conversation_context not in (None, "")
            else ChatToolGroundingContextService.current_conversation_context()
        )
        resolved_previous = (
            previous_messages
            if previous_messages is not None
            else ChatToolGroundingContextService.current_previous_messages()
        )
        resolved_memory = (
            memory_snapshot
            if isinstance(memory_snapshot, dict)
            else ChatToolGroundingContextService.current_memory_snapshot()
        )

        needs_code = cls._schema_needs_product_code(schema, grounded)

        if needs_code and not cls._has_product_code(grounded):
            product_code = cls._resolve_product_code_for_grounding(
                message=resolved_message,
                conversation_context=resolved_conversation,
                previous_messages=resolved_previous,
                memory_snapshot=resolved_memory,
            )

            if product_code:
                target = cls._preferred_code_param_name(schema)
                grounded[target] = product_code

        return cls._retain_schema_parameters(
            schema,
            cls._normalize_code_aliases(schema, grounded),
        )

    @classmethod
    def _retain_schema_parameters(
        cls,
        schema: list,
        parameters: dict,
    ) -> dict[str, Any]:
        """Remove params fora do schema (ex.: branch em rota só com ``code``).

        Follow-ups de filial/período reaproveitam lastAction e injetam filtros
        que a action OpenAPI não declara — o validate falhava com Unknown parameter.
        """
        schema_names = {
            str(parameter.get("name") or "").strip()
            for parameter in schema
            if isinstance(parameter, dict) and str(parameter.get("name") or "").strip()
        }
        if not schema_names:
            return dict(parameters or {})
        return {
            key: value
            for key, value in dict(parameters or {}).items()
            if key in schema_names
        }

    @classmethod
    def _normalize_code_aliases(
        cls,
        schema: list,
        parameters: dict,
    ) -> dict[str, Any]:
        """Alinha aliases (productCode/code) ao nome do schema e remove extras.

        Follow-ups reutilizam ``lastAction.params`` com ``productCode`` (memória),
        enquanto rotas produto tipicamente exigem ``code`` no path — sem isso
        o validate falha com ``Unknown parameter: productCode``.
        """
        grounded = dict(parameters or {})
        schema_names = {
            str(parameter.get("name") or "").strip()
            for parameter in schema
            if isinstance(parameter, dict) and str(parameter.get("name") or "").strip()
        }
        if not schema_names:
            return grounded

        alias_value = None
        for name in ("code", "productCode", "product_code"):
            value = grounded.get(name)
            if value not in (None, ""):
                alias_value = value
                break

        for name in list(grounded):
            if name in cls._CODE_PARAM_NAMES and name not in schema_names:
                grounded.pop(name, None)

        preferred = cls._preferred_code_param_name(schema)
        if (
            alias_value not in (None, "")
            and preferred in schema_names
            and grounded.get(preferred) in (None, "")
        ):
            grounded[preferred] = alias_value

        return grounded

    @classmethod
    def _resolve_product_code_for_grounding(
        cls,
        *,
        message: str | None,
        conversation_context: str | None,
        previous_messages: list | None,
        memory_snapshot: dict | None,
    ) -> str | None:
        """Resolve código mesmo sem sinal de follow-up — a action já foi escolhida."""
        code = ChatProductQueryIntentService.extract_product_code(message or "")

        if code:
            return code

        if isinstance(memory_snapshot, dict):
            from_items = ChatUserContextItemService.resolve_product_code_from_items(
                memory_snapshot.get("userContextItems"),
            )

            if from_items:
                return from_items

            focus = ChatSnapshotOperationalFocus.get(memory_snapshot)

            if isinstance(focus, dict):
                token = str(focus.get("productCode") or "").strip()

                if token and ChatProductQueryIntentService.is_plausible_product_code(token):
                    return token

        code = ChatProductQueryIntentService.resolve_product_code(
            str(message or ""),
            conversation_context,
            previous_messages=previous_messages,
            memory_snapshot=memory_snapshot,
        )

        if code:
            return code

        if conversation_context:
            return ChatUserContextItemService.resolve_product_code_from_context_prompt(
                conversation_context,
            )

        return None

    @classmethod
    def _schema_needs_product_code(
        cls,
        schema: list,
        parameters: dict,
    ) -> bool:
        del parameters

        for parameter in schema:
            if not isinstance(parameter, dict):
                continue

            name = str(parameter.get("name") or "").strip()

            if name not in cls._CODE_PARAM_NAMES:
                continue

            if parameter.get("required") or parameter.get("in") == "path":
                return True

        return False

    @classmethod
    def _has_product_code(cls, parameters: dict) -> bool:
        for name in cls._CODE_PARAM_NAMES:
            value = parameters.get(name)

            if value not in (None, ""):
                return True

        return False

    @classmethod
    def _preferred_code_param_name(cls, schema: list) -> str:
        names = [
            str(parameter.get("name") or "").strip()
            for parameter in schema
            if isinstance(parameter, dict) and str(parameter.get("name") or "").strip()
        ]

        for preferred in ("code", "productCode", "product_code"):
            if preferred in names:
                return preferred

        return "code"
