"""Resolve produto por descrição (drill-down na árvore, histórico de estrutura ou busca)."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)


class ChatProductDescriptionResolutionService:
    _DRILLDOWN_CODE_RE = re.compile(
        r"detalhe\s+do\s+item\s+(\d{4,})(?:\s*\(.+\))?\s*$",
        re.IGNORECASE,
    )
    _DESCRIPTION_QUERY_RES = (
        re.compile(
            r"^(?:mais\s+)?informa(?:ç|c)(?:õ|o)es\s+sobre\s+(.+)$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^detalhes?\s+(?:sobre\s+)?(.+)$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^detalhe\s+de\s+(.+)$",
            re.IGNORECASE,
        ),
    )

    @classmethod
    def extract_code_from_drilldown_message(cls, message: str | None) -> str | None:
        normalized = str(message or "").strip()

        if not normalized:
            return None

        match = cls._DRILLDOWN_CODE_RE.match(normalized)

        if not match:
            return None

        return match.group(1).strip()

    @classmethod
    def extract_description_query(cls, message: str | None) -> str | None:
        normalized = str(message or "").strip()

        if not normalized:
            return None

        if cls.extract_code_from_drilldown_message(normalized):
            return None

        for pattern in cls._DESCRIPTION_QUERY_RES:
            match = pattern.match(normalized)

            if match:
                query = match.group(1).strip(" .")

                if query:
                    return query

        return None

    @classmethod
    def resolve_code_from_history(
        cls,
        description_query: str,
        *,
        previous_messages: list[Any] | None,
    ) -> str | None:
        query_key = cls._normalize_match_key(description_query)

        if not query_key:
            return None

        best_code: str | None = None
        best_score = 0.0

        for item in reversed((previous_messages or [])[-14:]):
            for tool_call in reversed(cls._tool_calls(item)):
                metadata = tool_call.get("metadata") or {}

                if not metadata.get("ok"):
                    continue

                for code, description in cls._iter_catalog_entries(metadata):
                    score = cls._description_match_score(query_key, description)

                    if score > best_score:
                        best_score = score
                        best_code = code

        if best_score >= 0.55 and best_code:
            return best_code

        return None

    @classmethod
    def looks_like_description_lookup(cls, message: str | None) -> bool:
        return bool(
            cls.extract_code_from_drilldown_message(message)
            or cls.extract_description_query(message)
        )

    @classmethod
    def _tool_calls(cls, message: Any) -> list[dict]:
        if isinstance(message, dict):
            metadata = message.get("metadata") or {}
        else:
            metadata = getattr(message, "metadata", None) or {}

        if not isinstance(metadata, dict):
            return []

        tool_calls = metadata.get("toolCalls") or []

        return [call for call in tool_calls if isinstance(call, dict)]

    @classmethod
    def _iter_catalog_entries(cls, metadata: dict) -> list[tuple[str, str]]:
        entries: list[tuple[str, str]] = []
        seen: set[str] = set()

        def add(code: str | None, description: str | None) -> None:
            normalized_code = re.sub(r"\D", "", str(code or ""))

            if len(normalized_code) < 4:
                return

            desc = str(description or "").strip()

            if not desc:
                return

            key = f"{normalized_code}:{desc.lower()}"

            if key in seen:
                return

            seen.add(key)
            entries.append((normalized_code, desc))

        for presentation_key in (
            "presentation",
            "treePresentation",
            "tablePresentation",
            "chartPresentation",
        ):
            presentation = metadata.get(presentation_key)

            if not isinstance(presentation, dict):
                continue

            presentation_type = str(presentation.get("type") or "").lower()

            if presentation_type == "tree":
                root = presentation.get("root")

                if isinstance(root, dict):
                    cls._walk_tree_nodes(root, add)

            rows = presentation.get("rows")

            if isinstance(rows, list):
                columns = presentation.get("columns") or []
                code_key, desc_key = cls._table_keys(columns)

                for row in rows:
                    if not isinstance(row, dict):
                        continue

                    add(
                        str(row.get(code_key or "code") or row.get("codigo") or ""),
                        str(row.get(desc_key or "description") or row.get("descricao") or ""),
                    )

        return entries

    @classmethod
    def _walk_tree_nodes(cls, node: dict, add) -> None:
        code = str(node.get("label") or node.get("id") or "").strip()
        description = str(node.get("subtitle") or "").strip()
        add(code, description)

        children = node.get("children")

        if isinstance(children, list):
            for child in children:
                if isinstance(child, dict):
                    cls._walk_tree_nodes(child, add)

    @classmethod
    def _table_keys(cls, columns: list) -> tuple[str | None, str | None]:
        code_key = None
        desc_key = None

        for column in columns:
            if not isinstance(column, dict):
                continue

            key = str(column.get("key") or "")
            lowered = key.lower()

            if lowered in {"code", "codigo", "product_code", "productcode", "sku"}:
                code_key = key
            elif lowered in {"description", "descricao", "name", "nome"}:
                desc_key = key

        return code_key, desc_key

    @classmethod
    def _description_match_score(cls, query_key: str, description: str) -> float:
        desc_key = cls._normalize_match_key(description)

        if not desc_key:
            return 0.0

        if query_key == desc_key:
            return 1.0

        if query_key in desc_key or desc_key in query_key:
            shorter = min(len(query_key), len(desc_key))
            longer = max(len(query_key), len(desc_key))

            return 0.75 + (0.2 * shorter / max(longer, 1))

        query_tokens = set(query_key.split())
        desc_tokens = set(desc_key.split())
        overlap = query_tokens & desc_tokens

        if not overlap:
            return 0.0

        return len(overlap) / max(len(query_tokens), 1)

    @classmethod
    def _normalize_match_key(cls, value: str) -> str:
        normalized = ChatMessageNormalizationService.normalize_for_matching(value)
        normalized = unicodedata.normalize("NFKD", normalized)
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        return normalized
