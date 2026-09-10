"""Valida recommendations estruturadas contra allowedActions."""

from __future__ import annotations

from typing import Any


class RecommendationActionValidator:
    """Garante que actionId sugerido ∈ allowlist; sem actionId mantém só textual."""

    @classmethod
    def filter_items(
        cls,
        items: list[Any] | None,
        allowed_action_ids: list[str] | set[str] | None,
    ) -> list[dict[str, str]]:
        allowed = {
            str(token).strip()
            for token in (allowed_action_ids or [])
            if str(token).strip()
        }
        enforce = bool(allowed)
        output: list[dict[str, str]] = []

        for item in items or []:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    output.append({"text": text})
                continue

            if not isinstance(item, dict):
                continue

            action_id = str(item.get("actionId") or item.get("action_id") or "").strip()
            if action_id and enforce and action_id not in allowed:
                continue

            label = str(item.get("label") or item.get("text") or "").strip()
            query = str(item.get("query") or item.get("intent") or label).strip()
            reason = str(item.get("reason") or "").strip()
            text = str(item.get("text") or label).strip()

            if not (label or text):
                continue

            entry: dict[str, str] = {}
            if text:
                entry["text"] = text
            if label:
                entry["label"] = label
            if query:
                entry["query"] = query
            if reason:
                entry["reason"] = reason
            if action_id and (not enforce or action_id in allowed):
                entry["actionId"] = action_id

            output.append(entry)

        return output
