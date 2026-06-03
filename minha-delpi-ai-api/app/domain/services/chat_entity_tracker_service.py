"""Rastreamento de entidades ativas — Playbook memória e contexto (Fase 2 / §10)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_follow_up_intent_service import ChatFollowUpIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_sql_memory_workspace_service import (
    ChatSqlMemoryWorkspaceService,
)


class ChatEntityTrackerService:
    _ORDER_RE = re.compile(r"\bpedido\s+(\d{4,})\b", re.IGNORECASE)
    _BRANCH_IN_MSG_RE = re.compile(
        r"\bfilial\s+(\d{1,4})\b|\bbranch\s+(\d{1,4})\b",
        re.IGNORECASE,
    )

    @classmethod
    def apply_to_snapshot(
        cls,
        snapshot: dict,
        *,
        message: str | None,
        previous_messages: list[Any] | None = None,
        attachments: list | None = None,
    ) -> dict:
        result = dict(snapshot)
        entities = dict(result.get("lastEntities") or {})
        previous_codes = list(result.get("previousProductCodes") or [])

        cls._merge_from_message(entities, message, previous_codes=previous_codes)
        cls._merge_from_history(entities, previous_messages)
        cls._merge_from_attachments(entities, attachments)

        if previous_codes:
            result["previousProductCodes"] = previous_codes[-8:]

        result["lastEntities"] = entities
        result["activeEntities"] = dict(entities)
        result["referenceHints"] = cls._build_reference_hints(
            message,
            entities,
            result,
        )
        result["lastUsefulMessageId"] = cls._last_assistant_message_id(previous_messages)

        return result

    @classmethod
    def format_prompt_block(cls, snapshot: dict | None) -> str | None:
        hints = (snapshot or {}).get("referenceHints")

        if not isinstance(hints, dict) or not hints:
            return None

        lines = ["Resolução de referências (entidades ativas):"]

        for phrase, resolution in hints.items():
            lines.append(f"- «{phrase}» → {resolution}")

        entities = (snapshot or {}).get("activeEntities") or {}

        if entities.get("lastSqlSnippet"):
            lines.append(
                "- Há SQL recente na sessão; em pedidos de alteração, edite a consulta anterior."
            )

        return "\n".join(lines) if len(lines) > 1 else None

    @classmethod
    def _merge_from_message(
        cls,
        entities: dict[str, str],
        message: str | None,
        *,
        previous_codes: list[str],
    ) -> None:
        normalized = (message or "").strip()

        if not normalized:
            return

        code = ChatProductQueryIntentService.extract_product_code(normalized)

        if code:
            previous = str(entities.get("productCode") or "").strip()

            if previous and previous != code and previous not in previous_codes:
                previous_codes.append(previous)

            entities["productCode"] = code

        branch_match = cls._BRANCH_IN_MSG_RE.search(normalized)

        if branch_match:
            branch = branch_match.group(1) or branch_match.group(2)

            if branch:
                entities["branch"] = branch.strip()

        order_match = cls._ORDER_RE.search(normalized)

        if order_match:
            entities["orderId"] = order_match.group(1)

    @classmethod
    def _merge_from_history(
        cls,
        entities: dict[str, str],
        previous_messages: list[Any] | None,
    ) -> None:
        sql = ChatSqlMemoryWorkspaceService.resolve_current_sql(
            previous_messages=previous_messages,
        )

        if sql:
            entities["lastSqlSnippet"] = sql[:600]

        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)

            if cls._message_role(item) != "assistant":
                continue

            if not entities.get("productCode"):
                for tool in metadata.get("toolCalls") or []:
                    if not isinstance(tool, dict):
                        continue

                    path = str(tool.get("metadata", {}).get("path") or "")
                    code = ChatProductQueryIntentService.extract_product_code(path)

                    if code:
                        entities["productCode"] = code
                        break

            break

    @classmethod
    def _merge_from_attachments(
        cls,
        entities: dict[str, str],
        attachments: list | None,
    ) -> None:
        if not attachments:
            return

        last = attachments[-1] if isinstance(attachments, list) else attachments

        if isinstance(last, dict):
            name = str(last.get("filename") or last.get("name") or "").strip()

            if name:
                entities["lastAttachmentName"] = name

    @classmethod
    def _build_reference_hints(
        cls,
        message: str | None,
        entities: dict[str, str],
        snapshot: dict,
    ) -> dict[str, str]:
        hints: dict[str, str] = {}
        normalized = (message or "").strip().lower()
        product_code = str(entities.get("productCode") or "").strip()
        follow_type = ChatFollowUpIntentService.follow_up_type(message or "")

        if product_code and (
            follow_type == "supplier"
            or re.search(r"\bfornecedores?\b", normalized)
        ):
            hints["fornecedores"] = f"fornecedores do produto {product_code}"

        if product_code and follow_type == "stock":
            hints["estoque"] = f"estoque do produto {product_code}"

        if product_code and (
            follow_type in {"structure", "routing"}
            or re.search(r"\bestrutura\b|\broteiro\b", normalized)
        ):
            hints["consulta"] = f"dados do produto {product_code} (mesmo item em foco)"

        last_action = snapshot.get("lastAction") or {}

        if isinstance(last_action, dict) and last_action.get("name"):
            hints["última consulta"] = str(last_action.get("name"))

        canvas = snapshot.get("canvas") or {}

        if isinstance(canvas, dict) and canvas.get("active"):
            title = str(canvas.get("title") or "Lousa").strip()
            hints["lousa"] = title

        attachment = snapshot.get("lastAttachment") or {}

        if isinstance(attachment, dict) and attachment.get("filename"):
            hints["arquivo"] = str(attachment.get("filename"))

        return hints

    @classmethod
    def _last_assistant_message_id(cls, previous_messages: list[Any] | None) -> str | None:
        for item in reversed(previous_messages or []):
            if cls._message_role(item) != "assistant":
                continue

            message_id = cls._message_id(item)

            if message_id:
                return message_id

        return None

    @staticmethod
    def _message_metadata(item: Any) -> dict:
        if isinstance(item, dict):
            meta = item.get("metadata")

            return meta if isinstance(meta, dict) else {}

        meta = getattr(item, "metadata", None)

        return meta if isinstance(meta, dict) else {}

    @staticmethod
    def _message_role(item: Any) -> str:
        if isinstance(item, dict):
            return str(item.get("role") or "").strip().lower()

        return str(getattr(item, "role", "") or "").strip().lower()

    @staticmethod
    def _message_id(item: Any) -> str | None:
        if isinstance(item, dict):
            value = item.get("id") or item.get("messageId")

            return str(value).strip() if value else None

        value = getattr(item, "id", None)

        return str(value).strip() if value else None
