"""Regras puras para enriquecer rótulos de coluna ausentes do vocabulário JSON."""

from __future__ import annotations

import json
import re
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService


class ChatPresentationColumnLabelEnrichmentService:
    _BUNDLE = "column_labels"

    @classmethod
    def discovery_config(cls) -> dict[str, Any]:
        bundle = ChatAssistantContentService.load_bundle(cls._BUNDLE) or {}

        return bundle.get("columnLabelDiscovery") if isinstance(bundle, dict) else {}

    @classmethod
    def is_catalog_resolved(
        cls,
        key: str,
        *,
        schema_labels: dict[str, str] | None = None,
        profile_label: str | None = None,
        fields: dict[str, str] | None = None,
        snake_key: str | None = None,
    ) -> bool:
        from app.domain.services.external_actions.external_action_column_label_service import (
            ExternalActionColumnLabelService,
        )

        return ExternalActionColumnLabelService.is_catalog_field_resolved(
            key,
            schema_labels=schema_labels,
            profile_label=profile_label,
            fields=fields,
            snake_key=snake_key,
        )

    @classmethod
    def build_web_search_query(cls, field_key: str) -> str:
        config = cls.discovery_config()
        template = str(config.get("webSearchQueryTemplate") or "{field} significado campo ERP").strip()
        humanized = field_key.replace("_", " ").strip()

        return (
            template.replace("{field}", humanized)
            .replace("{key}", field_key)
            .strip()
        )

    @classmethod
    def build_llm_messages(
        cls,
        fields: list[str],
        *,
        path: str = "",
        web_snippets: dict[str, str] | None = None,
    ) -> list[dict[str, str]]:
        config = cls.discovery_config()
        system = str(config.get("llmSystemPrompt") or "").strip()
        intro = str(config.get("llmUserIntro") or "Traduza estes campos técnicos:").strip()
        web_intro = str(config.get("llmWebContextIntro") or "Contexto da web:").strip()

        lines = [intro, ""]

        if path:
            lines.append(f"Rota/contexto: {path}")
            lines.append("")

        for field in fields:
            lines.append(f"- {field}")

            snippet = (web_snippets or {}).get(field)

            if snippet:
                lines.append(f"  {web_intro} {snippet[:400]}")

        lines.append("")
        lines.append(
            str(
                config.get("llmResponseHint")
                or 'Responda somente JSON: {"nome_campo": "Rótulo PT-BR"}'
            ).strip()
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": "\n".join(lines).strip()},
        ]

    @classmethod
    def parse_llm_labels(cls, raw: str, *, expected_keys: list[str] | None = None) -> dict[str, str]:
        text = str(raw or "").strip()

        if not text:
            return {}

        candidates = [text]

        match = re.search(r"\{[\s\S]*\}", text)

        if match:
            candidates.insert(0, match.group(0))

        parsed: dict[str, str] = {}

        for candidate in candidates:
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue

            if not isinstance(payload, dict):
                continue

            for key, value in payload.items():
                token = str(key or "").strip()
                label = str(value or "").strip()

                if token and label:
                    parsed[token] = label

            if parsed:
                break

        if not expected_keys:
            return parsed

        allowed = {str(key).strip() for key in expected_keys if str(key).strip()}

        return {
            key: label
            for key, label in parsed.items()
            if key in allowed and label
        }

    @classmethod
    def normalize_label(cls, label: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(label or "").strip())

        if len(cleaned) > 48:
            cleaned = cleaned[:45].rstrip() + "…"

        return cleaned
