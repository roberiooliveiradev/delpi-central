"""Extrai entidades, ações, apresentação, lousa e anexos do histórico da sessão."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService


class ChatConversationMemoryExtractor:
    _PERIOD_PATTERNS: tuple[tuple[str, str], ...] = (
        (r"\búltimos?\s+30\s+dias\b", "last_30_days"),
        (r"\bultimos?\s+30\s+dias\b", "last_30_days"),
        (r"\búltimos?\s+7\s+dias\b", "last_7_days"),
        (r"\bultimos?\s+7\s+dias\b", "last_7_days"),
        (r"\búltimo\s+m[eê]s\b", "last_month"),
        (r"\bultimo\s+m[eê]s\b", "last_month"),
        (r"\beste\s+m[eê]s\b", "current_month"),
    )

    _ACTION_FROM_PATH: tuple[tuple[str, str], ...] = (
        ("/stock", "stock_lookup"),
        ("/analyser", "product_analyser"),
        ("/description", "product_description"),
        ("/routing", "routing_lookup"),
        ("/structure", "structure_lookup"),
        ("/sales", "sales_lookup"),
    )

    @classmethod
    def enrich_snapshot(
        cls,
        snapshot: dict,
        *,
        previous_messages: list[Any] | None,
        tool_calls: list | None = None,
        attachments: list | None = None,
        agent_id: str | None = None,
        project_id: str | None = None,
    ) -> dict:
        result = dict(snapshot)
        entities = dict(result.get("operationalFocus") or {})

        period = cls._extract_period_from_messages(previous_messages)

        if period and not entities.get("period"):
            entities["period"] = period

        result["operationalFocus"] = entities
        result["lastAction"] = cls._extract_last_action(previous_messages, tool_calls)
        result["lastPresentation"] = cls._extract_last_presentation(previous_messages)
        result["canvas"] = cls._extract_canvas_state(previous_messages)
        result["lastAttachment"] = cls._extract_last_attachment(
            previous_messages,
            attachments,
        )

        if agent_id:
            result["activeAgentId"] = str(agent_id)

        if project_id:
            result["activeProjectId"] = str(project_id)

        return result

    @classmethod
    def _extract_period_from_messages(
        cls,
        previous_messages: list[Any] | None,
    ) -> str | None:
        for item in reversed(previous_messages or []):
            if cls._message_role(item) != "user":
                continue

            content = cls._message_content(item).lower()

            for pattern, value in cls._PERIOD_PATTERNS:
                if re.search(pattern, content, flags=re.IGNORECASE):
                    return value

        return None

    @classmethod
    def _extract_last_action(
        cls,
        previous_messages: list[Any] | None,
        tool_calls: list | None = None,
    ) -> dict[str, Any] | None:
        calls = list(tool_calls or [])

        if not calls:
            for item in reversed(previous_messages or []):
                metadata = cls._message_metadata(item)

                if cls._message_role(item) != "assistant":
                    continue

                stored = metadata.get("toolCalls") or []

                if stored:
                    calls = stored
                    break

        for tool_call in reversed(calls):
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            path = str(metadata.get("path") or "")
            action_name = cls._action_name_from_path(path)
            params: dict[str, Any] = {}

            code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

            if code:
                params["productCode"] = code

            args = tool_call.get("arguments")

            if isinstance(args, dict):
                inner = args.get("parameters")

                if isinstance(inner, dict):
                    for key in ("branch", "branch_code", "period"):
                        if inner.get(key) not in (None, ""):
                            params[key if key != "branch_code" else "branch"] = str(
                                inner[key]
                            )

            result_type = cls._result_type_from_metadata(metadata)

            return {
                "name": action_name,
                "params": params,
                "resultType": result_type,
                "path": path,
            }

        return None

    @classmethod
    def _extract_last_presentation(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        for item in reversed(previous_messages or []):
            if cls._message_role(item) != "assistant":
                continue

            metadata = cls._message_metadata(item)
            tool_calls = metadata.get("toolCalls") or []

            for tool_call in reversed(tool_calls):
                if not isinstance(tool_call, dict):
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                presentation = tool_meta.get("presentation")

                if isinstance(presentation, dict):
                    ptype = str(presentation.get("type") or "").strip()

                    if ptype:
                        return {
                            "type": ptype,
                            "title": presentation.get("title"),
                            "messageId": cls._message_id(item),
                        }

                text_presentation = tool_meta.get("textPresentation")

                if isinstance(text_presentation, dict):
                    return {
                        "type": "text",
                        "title": text_presentation.get("title"),
                        "messageId": cls._message_id(item),
                    }

            if metadata.get("contextSnapshot"):
                return {"type": "chat", "messageId": cls._message_id(item)}

        return None

    @classmethod
    def _extract_canvas_state(
        cls,
        previous_messages: list[Any] | None,
    ) -> dict[str, Any] | None:
        version = 0

        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)
            canvas_open = metadata.get("canvasOpen")

            if not isinstance(canvas_open, dict):
                continue

            markdown = str(canvas_open.get("markdown") or "").strip()

            if not markdown:
                continue

            version += 1

            return {
                "active": True,
                "title": str(canvas_open.get("title") or "Lousa").strip(),
                "lastUpdatedFromMessageId": cls._message_id(item),
                "lastContentType": "markdown",
                "version": version,
            }

        return {"active": False} if previous_messages else None

    @classmethod
    def _extract_last_attachment(
        cls,
        previous_messages: list[Any] | None,
        attachments: list | None,
    ) -> dict[str, Any] | None:
        if attachments:
            last = attachments[-1] if isinstance(attachments, list) else attachments

            if isinstance(last, dict):
                return {
                    "filename": last.get("filename") or last.get("name"),
                    "type": last.get("mimeType") or last.get("type"),
                    "parsed": bool(last.get("parsed") or last.get("textExtracted")),
                }

        for item in reversed(previous_messages or []):
            metadata = cls._message_metadata(item)
            msg_attachments = metadata.get("attachments") or []

            if not msg_attachments:
                continue

            last = msg_attachments[-1]

            if isinstance(last, dict):
                return {
                    "filename": last.get("filename") or last.get("name"),
                    "type": last.get("mimeType") or last.get("type"),
                    "parsed": bool(last.get("parsed")),
                    "messageId": cls._message_id(item),
                }

        return None

    @classmethod
    def _action_name_from_path(cls, path: str) -> str:
        lowered = (path or "").lower()

        for fragment, name in cls._ACTION_FROM_PATH:
            if fragment in lowered:
                return name

        return "external_action"

    @classmethod
    def _result_type_from_metadata(cls, metadata: dict) -> str:
        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            ptype = str(presentation.get("type") or "").strip()

            if ptype == "table":
                return "table"

            if ptype in {"chart", "line", "bar", "pie"}:
                return "chart"

        if metadata.get("textPresentation"):
            return "text_block"

        return "unknown"

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

    @staticmethod
    def _message_metadata(message: Any) -> dict:
        if isinstance(message, dict):
            meta = message.get("metadata")

            return meta if isinstance(meta, dict) else {}

        meta = getattr(message, "metadata", None)

        return meta if isinstance(meta, dict) else {}

    @staticmethod
    def _message_id(message: Any) -> str | None:
        if isinstance(message, dict):
            mid = message.get("id")

            return str(mid) if mid is not None else None

        mid = getattr(message, "id", None)

        return str(mid) if mid is not None else None
