"""Chips de refinamento pós-consulta operacional — Playbook 07 Fase 4."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from app.infrastructure.content.content_service import ContentService


@lru_cache(maxsize=1)
def _content() -> dict[str, Any]:
    return ContentService.load_json("assistant/interactivity")


class ChatOperationalRefinementInteractivityService:
    @classmethod
    def build_from_tool_calls(cls, tool_calls: list | None) -> list[dict[str, str]]:
        tool_meta = cls._last_successful_metadata(tool_calls)

        if not tool_meta:
            return []

        chip_keys = cls._resolve_chip_keys(tool_meta)
        queries = _content().get("refinementQueries") or {}
        suggestions: list[dict[str, str]] = []
        seen_labels: set[str] = set()

        for key in chip_keys:
            labels = (_content().get("refinementChips") or {}).get(key) or []

            if not isinstance(labels, list):
                continue

            for label in labels:
                label_text = str(label or "").strip()

                if not label_text or label_text in seen_labels:
                    continue

                query = str(queries.get(label_text) or label_text).strip()

                if not query:
                    continue

                seen_labels.add(label_text)
                suggestions.append({"label": label_text, "query": query})

                if len(suggestions) >= 5:
                    return suggestions

        return suggestions

    @classmethod
    def _last_successful_metadata(cls, tool_calls: list | None) -> dict[str, Any] | None:
        for call in reversed(tool_calls or []):
            if not isinstance(call, dict):
                continue

            if str(call.get("name") or "") != "execute_external_action":
                continue

            metadata = call.get("metadata")

            if isinstance(metadata, dict) and metadata.get("ok"):
                return metadata

        return None

    @classmethod
    def _resolve_chip_keys(cls, metadata: dict[str, Any]) -> list[str]:
        keys: list[str] = []
        path = str(metadata.get("path") or "").lower()
        coverage = metadata.get("dataCoverageNotice")

        if isinstance(coverage, dict):
            kind = str(coverage.get("kind") or "").strip().lower()
            details = coverage.get("details") or {}

            if kind == "pagination" or isinstance(details.get("pagination"), dict):
                keys.append("pagination")

            if isinstance(details.get("depth"), dict):
                keys.append("depth")

            if isinstance(details.get("stockPagination"), dict):
                keys.append("stock")

        consolidation = metadata.get("paginationConsolidation")

        if isinstance(consolidation, dict) and not consolidation.get("completed"):
            if "pagination" not in keys:
                keys.append("pagination")

        if "/stock" in path:
            if "stock" not in keys:
                keys.append("stock")

        if any(token in path for token in ("/sales", "/purchases", "/invoice")):
            keys.append("period")

        if any(token in path for token in ("/structure", "/parents", "/analyser")):
            if "depth" not in keys:
                keys.append("depth")

        return keys
