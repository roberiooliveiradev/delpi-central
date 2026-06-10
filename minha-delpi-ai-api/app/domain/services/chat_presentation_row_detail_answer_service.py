"""Resposta direta ao detalhar uma linha da última tabela/consulta (drill-down do MFE)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_analysis_intent_vocabulary_service import (
    ChatAnalysisIntentVocabularyService,
)
from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
)
from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)

_CONTENT_BUNDLE = "data_interpretation"
_FIELD_SPLIT_RE = re.compile(r"[;\n]+")
_PAIR_RE = re.compile(r"^(.+?)\s*:\s*(.+)$")
_CODE_KEY_RE = re.compile(
    r"^(code|codigo|cod|id|numero|number|sku|produto|product|product_code|productcode|cod_produto)$",
    re.IGNORECASE,
)


class ChatPresentationRowDetailAnswerService:
    @classmethod
    def looks_like_request(cls, message: str | None) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)

        if not normalized:
            return False

        return any(
            term in normalized
            for term in ChatAnalysisIntentVocabularyService.terms("rowDetailRequestTerms")
        )

    @classmethod
    def build_answer(
        cls,
        message: str,
        previous_messages: list[Any] | None,
    ) -> str | None:
        if not cls.looks_like_request(message):
            return None

        fields = cls._parse_fields_from_message(message)

        if not fields:
            return ChatAssistantContentService.get(
                _CONTENT_BUNDLE,
                "rowDetail",
                "missingFields",
            )

        context = cls._resolve_latest_table_context(previous_messages)

        if not context:
            return ChatAssistantContentService.get(
                _CONTENT_BUNDLE,
                "rowDetail",
                "notFound",
            )

        rows, columns, title = context
        matched = cls._match_row(rows, columns, fields)

        if not matched:
            return ChatAssistantContentService.get(
                _CONTENT_BUNDLE,
                "rowDetail",
                "notFound",
            )

        row, index = matched

        return cls._format_row_detail(
            row=row,
            columns=columns,
            title=title,
            index=index,
            total=len(rows),
        )

    @classmethod
    def _parse_fields_from_message(cls, message: str) -> list[tuple[str, str]]:
        raw = str(message or "").strip()
        lowered = raw.lower()
        marker = "ultimo resultado"

        if marker in lowered:
            start = lowered.index(marker) + len(marker)
            payload = raw[start:].lstrip(" -—:\t")
        else:
            payload = raw

        fields: list[tuple[str, str]] = []

        for chunk in _FIELD_SPLIT_RE.split(payload):
            piece = str(chunk or "").strip().strip(",")

            if not piece:
                continue

            match = _PAIR_RE.match(piece)

            if not match:
                continue

            label = str(match.group(1) or "").strip()
            value = str(match.group(2) or "").strip()

            if label and value:
                fields.append((label, value))

        return fields

    @classmethod
    def _resolve_latest_table_context(
        cls,
        previous_messages: list[Any] | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]], str] | None:
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

                context = cls._table_context_from_metadata(tool_meta)

                if context:
                    return context

        return None

    @classmethod
    def _table_context_from_metadata(
        cls,
        tool_meta: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]], str] | None:
        title = cls._resolve_title(tool_meta)

        for key in ("presentation", "tablePresentation"):
            table = tool_meta.get(key)

            if isinstance(table, dict) and table.get("type") == "table":
                resolved = cls._rows_and_columns(table)

                if resolved:
                    return (*resolved, title)

        bulk = tool_meta.get("tablePresentations")

        if isinstance(bulk, list):
            for table in reversed(bulk):
                if not isinstance(table, dict) or table.get("type") != "table":
                    continue

                resolved = cls._rows_and_columns(table)

                if resolved:
                    table_title = str(table.get("title") or title).strip() or title

                    return (*resolved, table_title)

        humanized = tool_meta.get("humanizedSummary")

        if isinstance(humanized, dict):
            sql_rows = humanized.get("sqlRows")

            if isinstance(sql_rows, list) and sql_rows and isinstance(sql_rows[0], dict):
                columns = cls._infer_columns(sql_rows[0])

                return [row for row in sql_rows if isinstance(row, dict)], columns, title

        return None

    @staticmethod
    def _rows_and_columns(
        table: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]] | None:
        rows = table.get("rows")

        if not isinstance(rows, list) or not rows:
            return None

        dict_rows = [row for row in rows if isinstance(row, dict)]

        if not dict_rows:
            return None

        columns_raw = table.get("columns")
        columns: list[dict[str, str]] = []

        if isinstance(columns_raw, list):
            for column in columns_raw:
                if not isinstance(column, dict):
                    continue

                key = str(column.get("key") or "").strip()
                label = str(column.get("label") or key).strip()

                if key:
                    columns.append({"key": key, "label": label or key})

        if not columns:
            columns = ChatPresentationRowDetailAnswerService._infer_columns(dict_rows[0])

        return dict_rows, columns

    @staticmethod
    def _infer_columns(sample: dict[str, Any]) -> list[dict[str, str]]:
        return [
            {"key": key, "label": key.replace("_", " ").strip()}
            for key in sample.keys()
            if str(key).strip() and not str(key).startswith("_")
        ]

    @classmethod
    def _resolve_title(cls, tool_meta: dict[str, Any]) -> str:
        for key in ("presentation", "tablePresentation"):
            table = tool_meta.get(key)

            if isinstance(table, dict):
                title = str(table.get("title") or "").strip()

                if title:
                    return title

        humanized = tool_meta.get("humanizedSummary")

        if isinstance(humanized, dict):
            title = str(humanized.get("titulo") or "").strip()

            if title:
                return title

        return ChatAssistantContentService.get(
            _CONTENT_BUNDLE,
            "defaultTitle",
            default="Consulta anterior",
        )

    @classmethod
    def _match_row(
        cls,
        rows: list[dict[str, Any]],
        columns: list[dict[str, str]],
        fields: list[tuple[str, str]],
    ) -> tuple[dict[str, Any], int] | None:
        keyed_fields = cls._map_fields_to_keys(columns, fields)

        if not keyed_fields:
            return None

        best_index: int | None = None
        best_score = -1

        for index, row in enumerate(rows):
            score = sum(
                1
                for key, expected in keyed_fields.items()
                if cls._values_equal(row.get(key), expected)
            )

            if score > best_score:
                best_score = score
                best_index = index

        if best_index is None or best_score <= 0:
            return None

        required = cls._required_match_count(keyed_fields)

        if best_score < required:
            return None

        return rows[best_index], best_index

    @classmethod
    def _map_fields_to_keys(
        cls,
        columns: list[dict[str, str]],
        fields: list[tuple[str, str]],
    ) -> dict[str, str]:
        label_to_key = {
            cls._normalize_label(column.get("label") or ""): str(column.get("key") or "").strip()
            for column in columns
            if str(column.get("key") or "").strip()
        }
        key_to_key = {
            cls._normalize_label(column.get("key") or ""): str(column.get("key") or "").strip()
            for column in columns
            if str(column.get("key") or "").strip()
        }

        mapped: dict[str, str] = {}

        for label, value in fields:
            normalized_label = cls._normalize_label(label)
            key = label_to_key.get(normalized_label) or key_to_key.get(normalized_label)

            if key:
                mapped[key] = value

        return mapped

    @classmethod
    def _required_match_count(cls, keyed_fields: dict[str, str]) -> int:
        if not keyed_fields:
            return 0

        code_keys = [key for key in keyed_fields if _CODE_KEY_RE.match(str(key))]

        if code_keys:
            return 1

        return min(2, len(keyed_fields))

    @classmethod
    def _values_equal(cls, actual: Any, expected: str) -> bool:
        actual_text = cls._normalize_value(actual)
        expected_text = cls._normalize_value(expected)

        if not actual_text or not expected_text:
            return False

        if actual_text == expected_text:
            return True

        if cls._numeric_equal(actual_text, expected_text):
            return True

        return cls._normalize_label(actual_text) == cls._normalize_label(expected_text)

    @staticmethod
    def _normalize_value(value: Any) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _numeric_equal(left: str, right: str) -> bool:
        try:
            left_num = float(left.replace(",", "."))
            right_num = float(right.replace(",", "."))
        except ValueError:
            return False

        if abs(left_num - right_num) <= 0.0001:
            return True

        if left_num == 0 and abs(right_num) < 0.01:
            return True

        if right_num == 0 and abs(left_num) < 0.01:
            return True

        return False

    @staticmethod
    def _normalize_label(value: str) -> str:
        lowered = str(value or "").strip().lower()
        cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)

        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def _format_row_detail(
        cls,
        *,
        row: dict[str, Any],
        columns: list[dict[str, str]],
        title: str,
        index: int,
        total: int,
    ) -> str:
        heading = ChatAssistantContentService.format(
            _CONTENT_BUNDLE,
            "rowDetail",
            "heading",
            title=title,
        )
        parts = [heading, ""]

        rendered_keys: set[str] = set()

        for column in columns:
            key = str(column.get("key") or "").strip()
            label = str(column.get("label") or key).strip()

            if not key or key in rendered_keys:
                continue

            value = cls._format_cell(row.get(key), key=key)

            if not value:
                continue

            parts.append(
                ChatAssistantContentService.format(
                    _CONTENT_BUNDLE,
                    "rowDetail",
                    "fieldLine",
                    label=label,
                    value=value,
                )
            )
            rendered_keys.add(key)

        for key, raw in row.items():
            key_text = str(key or "").strip()

            if not key_text or key_text.startswith("_") or key_text in rendered_keys:
                continue

            value = cls._format_cell(raw, key=key_text)

            if not value:
                continue

            label = key_text.replace("_", " ").strip()
            parts.append(
                ChatAssistantContentService.format(
                    _CONTENT_BUNDLE,
                    "rowDetail",
                    "fieldLine",
                    label=label,
                    value=value,
                )
            )

        parts.append("")
        parts.append(
            ChatAssistantContentService.format(
                _CONTENT_BUNDLE,
                "rowDetail",
                "positionFooter",
                index=index + 1,
                total=total,
                title=title,
            )
        )

        return "\n".join(parts).strip()

    @classmethod
    def _format_cell(cls, value: Any, *, key: str = "") -> str:
        if value is None:
            return ""

        text = str(value).strip()

        if not text:
            return ""

        if cls._should_format_as_date(key, text):
            return f"{text[6:8]}/{text[4:6]}/{text[0:4]}"

        return text

    @classmethod
    def _should_format_as_date(cls, key: str, text: str) -> bool:
        if len(text) != 8 or not text.isdigit():
            return False

        key_norm = cls._normalize_label(key)

        if not any(token in key_norm for token in ("data", "date", "dt ", " dt")):
            return False

        year = int(text[0:4])

        return 1990 <= year <= 2100

    @staticmethod
    def _message_metadata(item: Any) -> dict[str, Any]:
        if isinstance(item, dict):
            metadata = item.get("metadata")

            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(item, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}
