"""Resolve placeholders em queries de chips — Playbook 07 Fase 2."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_product_query_intent_service import ChatProductQueryIntentService

_PLACEHOLDER_RE = re.compile(r"\{\{([a-zA-Z][a-zA-Z0-9]*)\}\}")


class ChatInteractivityQueryResolver:
    @classmethod
    def resolve(
        cls,
        query: str,
        *,
        metadata: dict | None = None,
        workspace_context: dict | None = None,
    ) -> str:
        text = str(query or "").strip()

        if not text or "{{" not in text:
            return text

        entities = cls._entity_map(metadata=metadata, workspace_context=workspace_context)

        def replace(match: re.Match[str]) -> str:
            key = match.group(1)
            value = entities.get(key)

            if value:
                return value

            return match.group(0)

        return _PLACEHOLDER_RE.sub(replace, text)

    @classmethod
    def _entity_map(
        cls,
        *,
        metadata: dict | None,
        workspace_context: dict | None,
    ) -> dict[str, str]:
        output: dict[str, str] = {}
        snapshot = (metadata or {}).get("contextSnapshot")

        if isinstance(snapshot, dict):
            last_entities = snapshot.get("operationalFocus") or {}

            if isinstance(last_entities, dict):
                cls._merge_entities(output, last_entities)

        working = (workspace_context or {}).get("workingMemory") or {}
        persisted = working.get("operationalFocus") or {}

        if isinstance(persisted, dict):
            cls._merge_entities(output, persisted)

        for chip in (metadata or {}).get("contextChips") or []:
            if not isinstance(chip, dict):
                continue

            kind = str(chip.get("kind") or "").strip().lower()
            value = str(chip.get("value") or "").strip()

            if not value:
                continue

            if kind == "product":
                normalized = ChatProductQueryIntentService.normalize_product_code(value)

                if ChatProductQueryIntentService.is_plausible_product_code(normalized):
                    output.setdefault("productCode", normalized)

            if kind == "branch":
                output.setdefault("branch", value)

            if kind == "period":
                output.setdefault("period", value)

            if kind in {"warehouse", "armazem"}:
                output.setdefault("warehouse", value)

        research = (metadata or {}).get("webSearchResearch")

        if isinstance(research, dict):
            search_query = str(research.get("query") or "").strip()

            if search_query:
                output.setdefault("searchQuery", search_query)

            attempted = research.get("attemptedQueries") or []

            if not output.get("searchQuery") and isinstance(attempted, list):
                for item in attempted:
                    token = str(item or "").strip()

                    if token:
                        output.setdefault("searchQuery", token)
                        break

        return output

    @staticmethod
    def _merge_entities(target: dict[str, str], source: dict) -> None:
        mapping = {
            "productCode": "productCode",
            "branch": "branch",
            "period": "period",
            "warehouse": "warehouse",
        }

        for key, alias in mapping.items():
            raw = source.get(key)

            if raw in (None, ""):
                continue

            token = str(raw).strip()

            if key == "productCode":
                normalized = ChatProductQueryIntentService.normalize_product_code(token)

                if ChatProductQueryIntentService.is_plausible_product_code(normalized):
                    target.setdefault(alias, normalized)

                continue

            if token:
                target.setdefault(alias, token)
