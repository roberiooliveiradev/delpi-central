"""Conjuntos de resultado da sessão e resolução de referências ordinais (E2.S2).

``resultSets`` guarda, por turno, a lista ordenada de itens (código + rótulo)
que o usuário acabou de ver — base para «o segundo», «os três primeiros»,
«o último». Sem reintroduzir ``lastEntities``: o foco operacional continua em
``operationalFocus`` / ``userContextItems``.
"""

from __future__ import annotations

import json
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_result_set_reference_content_service import (
    ChatResultSetReferenceContentService,
)

_CONTENT = ChatResultSetReferenceContentService


class ChatResultSetReferenceService:
    """Monta ``snapshot['resultSets']`` e resolve ordinais para códigos."""

    # ------------------------------------------------------------------ build

    @classmethod
    def build_result_sets(
        cls,
        *,
        tool_calls: list[Any] | None,
        excerpt: dict[str, Any] | None = None,
        message_id: str | None = None,
        previous_result_sets: list[Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Conjuntos do turno atual; mantém os anteriores quando o turno não lista nada."""
        current = cls._build_from_tool_calls(tool_calls, message_id=message_id)

        if not current:
            current = cls._build_from_excerpt(excerpt, message_id=message_id)

        if current:
            return current

        return cls._sanitize_sets(previous_result_sets)

    @classmethod
    def _build_from_tool_calls(
        cls,
        tool_calls: list[Any] | None,
        *,
        message_id: str | None,
    ) -> list[dict[str, Any]]:
        max_sets = max(1, _CONTENT.limit_int("maxSets", 3))
        sets: list[dict[str, Any]] = []

        for tool_call in tool_calls or []:
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            metadata = tool_call.get("metadata")

            if not isinstance(metadata, dict) or not metadata.get("ok"):
                continue

            rows = cls._rows_from_metadata(metadata)
            items = cls._items_from_rows(rows)

            if not items:
                continue

            sets.append(
                cls._make_set(
                    items=items,
                    total_count=len(rows),
                    metadata=metadata,
                    message_id=message_id,
                    index=len(sets) + 1,
                )
            )

            if len(sets) >= max_sets:
                break

        return sets

    @classmethod
    def _build_from_excerpt(
        cls,
        excerpt: dict[str, Any] | None,
        *,
        message_id: str | None,
    ) -> list[dict[str, Any]]:
        if not isinstance(excerpt, dict):
            return []

        top_keys = excerpt.get("topKeys")

        if not isinstance(top_keys, list) or not top_keys:
            return []

        rows = [{"code": str(item).strip()} for item in top_keys if str(item).strip()]
        items = cls._items_from_rows(rows)

        if not items:
            return []

        row_count = excerpt.get("rowCount")
        total = row_count if isinstance(row_count, int) and row_count > 0 else len(rows)

        return [
            cls._make_set(
                items=items,
                total_count=total,
                metadata={
                    "operationId": excerpt.get("operationId"),
                    "path": excerpt.get("path"),
                    "title": excerpt.get("title"),
                },
                message_id=message_id or excerpt.get("messageId"),
                index=1,
            )
        ]

    @classmethod
    def _make_set(
        cls,
        *,
        items: list[dict[str, Any]],
        total_count: int,
        metadata: dict[str, Any],
        message_id: str | None,
        index: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": f"rs-{index}",
            "kind": cls._resolve_kind(items),
            "items": items,
            "totalCount": max(total_count, len(items)),
            "truncated": total_count > len(items),
        }

        operation_id = str(metadata.get("operationId") or "").strip()

        if operation_id:
            payload["operationId"] = operation_id

        path = str(metadata.get("path") or "").strip()

        if path:
            payload["path"] = path

        title = cls._resolve_title(metadata)

        if title:
            payload["title"] = title

        if message_id:
            payload["messageId"] = str(message_id)

        return payload

    @classmethod
    def _resolve_kind(cls, items: list[dict[str, Any]]) -> str:
        if not items:
            return _CONTENT.kind("generic")

        product_like = 0

        for item in items:
            code = str(item.get("code") or "").strip()

            if code and ChatProductQueryIntentService.is_plausible_product_code(code):
                product_like += 1

        ratio = product_like / len(items)

        if ratio >= _CONTENT.limit_float("minProductRatio", 0.6):
            return _CONTENT.kind("product")

        return _CONTENT.kind("generic")

    @classmethod
    def _resolve_title(cls, metadata: dict[str, Any]) -> str:
        direct = str(metadata.get("title") or "").strip()

        if direct:
            return direct

        for key in (
            "presentation",
            "tablePresentation",
            "textPresentation",
            "treePresentation",
        ):
            block = metadata.get(key)

            if isinstance(block, dict):
                title = str(block.get("title") or "").strip()

                if title:
                    return title

        tables = metadata.get("tablePresentations")

        if isinstance(tables, list):
            for table in tables:
                if isinstance(table, dict):
                    title = str(table.get("title") or "").strip()

                    if title:
                        return title

        return ""

    @classmethod
    def _rows_from_metadata(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for table in metadata.get("tablePresentations") or []:
            if not isinstance(table, dict):
                continue

            for row in table.get("rows") or []:
                if isinstance(row, dict):
                    rows.append(row)

            if rows:
                return rows

        table = metadata.get("tablePresentation")

        if isinstance(table, dict):
            for row in table.get("rows") or []:
                if isinstance(row, dict):
                    rows.append(row)

            if rows:
                return rows

        payload = cls._load_response_preview(metadata)

        if isinstance(payload, dict):
            for holder in (payload, payload.get("data")):
                if not isinstance(holder, dict):
                    continue

                for key in ("items", "rows", "results"):
                    collection = holder.get(key)

                    if isinstance(collection, list) and collection:
                        return [item for item in collection if isinstance(item, dict)]

        return rows

    @classmethod
    def _items_from_rows(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        max_items = max(1, _CONTENT.limit_int("maxItemsPerSet", 20))
        max_label = max(8, _CONTENT.limit_int("maxLabelChars", 90))
        code_fields = _CONTENT.field_names("code")
        label_fields = _CONTENT.field_names("label")

        items: list[dict[str, Any]] = []
        seen: set[str] = set()

        for row in rows:
            code = cls._first_field(row, code_fields)

            if not code:
                continue

            if code in seen:
                continue

            seen.add(code)
            item: dict[str, Any] = {"ordinal": len(items) + 1, "code": code}
            label = cls._first_field(row, label_fields)

            if label:
                item["label"] = label[:max_label]

            items.append(item)

            if len(items) >= max_items:
                break

        return items

    @staticmethod
    def _first_field(row: dict[str, Any], field_names: tuple[str, ...]) -> str:
        lowered = {
            str(key).strip().lower(): value
            for key, value in row.items()
            if value not in (None, "")
        }

        for field in field_names:
            value = lowered.get(field)

            if value not in (None, ""):
                return str(value).strip()

        return ""

    @classmethod
    def _sanitize_sets(cls, result_sets: list[Any] | None) -> list[dict[str, Any]]:
        sanitized: list[dict[str, Any]] = []

        for item in result_sets or []:
            if not isinstance(item, dict):
                continue

            items = item.get("items")

            if not isinstance(items, list) or not items:
                continue

            sanitized.append(item)

        return sanitized

    @staticmethod
    def _load_response_preview(metadata: dict[str, Any]) -> Any:
        raw = str(metadata.get("responsePreview") or "").strip()

        if not raw or not raw.startswith(("{", "[")):
            return None

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    # --------------------------------------------------------------- resolve

    @classmethod
    def primary_set(cls, snapshot: dict[str, Any] | None) -> dict[str, Any] | None:
        for candidate in cls._sanitize_sets((snapshot or {}).get("resultSets")):
            return candidate

        return None

    @classmethod
    def resolve(
        cls,
        message: str,
        snapshot: dict[str, Any] | None,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Entradas ``resolvedReferences`` para ordinais apoiados em ``resultSets``."""
        result_set = cls.primary_set(snapshot)

        if not result_set:
            return [], []

        items = [item for item in result_set.get("items") or [] if isinstance(item, dict)]

        if not items:
            return [], []

        normalized = ChatMessageNormalizationService.normalize_for_matching(message) or ""

        if not normalized:
            return [], []

        selection = cls._resolve_selection(normalized, items)

        if not selection:
            return [], []

        picked, text = selection
        confidence = _CONTENT.resolution_confidence()
        source = _CONTENT.resolution_text(
            "sourceTemplate",
            setId=str(result_set.get("id") or "rs-1"),
        )

        if len(picked) == 1:
            item = picked[0]
            value = str(item.get("code") or "").strip()

            if not value:
                return [], []

            entry = {
                "text": text,
                "resolvedTo": _CONTENT.resolution_value(
                    "resolvedToSingle",
                    default="resultSetItem",
                ),
                "value": value,
                "source": source,
                "confidence": confidence,
            }
            label = str(item.get("label") or "").strip()

            if label:
                entry["label"] = label

            return [entry], ["resultSets"]

        codes = [
            str(item.get("code") or "").strip()
            for item in picked
            if str(item.get("code") or "").strip()
        ]

        if not codes:
            return [], []

        return (
            [
                {
                    "text": text,
                    "resolvedTo": _CONTENT.resolution_value(
                        "resolvedToRange",
                        default="resultSetItems",
                    ),
                    "value": ", ".join(codes),
                    "values": codes,
                    "source": source,
                    "confidence": confidence,
                }
            ],
            ["resultSets"],
        )

    @classmethod
    def resolve_codes(
        cls,
        message: str,
        snapshot: dict[str, Any] | None,
    ) -> list[str]:
        """Códigos apontados pelo ordinal — consumo por tools/parâmetros."""
        entries, _ = cls.resolve(message, snapshot)

        codes: list[str] = []

        for entry in entries:
            values = entry.get("values")

            if isinstance(values, list):
                codes.extend(str(item).strip() for item in values if str(item).strip())
                continue

            value = str(entry.get("value") or "").strip()

            if value:
                codes.append(value)

        return codes

    @classmethod
    def _resolve_selection(
        cls,
        normalized: str,
        items: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], str] | None:
        max_range = max(1, _CONTENT.limit_int("maxRangeSize", 10))

        count = cls._match_first_n(normalized)

        if count:
            picked = items[: min(count, max_range)]

            if picked:
                return picked, _CONTENT.resolution_text(
                    "rangeReferenceText",
                    count=len(picked),
                )

        if _CONTENT.compile_pattern("lastItem").search(normalized):
            return [items[-1]], _CONTENT.resolution_text("lastReferenceText")

        ordinal = cls._match_single_ordinal(normalized)

        if ordinal and 1 <= ordinal <= len(items):
            return [items[ordinal - 1]], _CONTENT.resolution_text(
                "singleReferenceText",
                ordinalWord=_CONTENT.ordinal_label(ordinal),
            )

        return None

    @classmethod
    def _match_first_n(cls, normalized: str) -> int | None:
        numeric = _CONTENT.compile_pattern("firstNNumeric").search(normalized)

        if numeric:
            try:
                value = int(numeric.group(1))
            except (TypeError, ValueError):
                value = 0

            if value > 0:
                return value

        worded = _CONTENT.compile_pattern("firstNWord").search(normalized)

        if worded:
            return _CONTENT.cardinal_words().get(worded.group(1).lower())

        return None

    @classmethod
    def _match_single_ordinal(cls, normalized: str) -> int | None:
        item_number = _CONTENT.compile_pattern("itemNumber").search(normalized)

        if item_number:
            try:
                value = int(item_number.group(1))
            except (TypeError, ValueError):
                value = 0

            if value > 0:
                return value

        match = _CONTENT.compile_pattern("singleOrdinalWord").search(normalized)

        if not match:
            return None

        return _CONTENT.ordinal_words().get(match.group(1).lower())
