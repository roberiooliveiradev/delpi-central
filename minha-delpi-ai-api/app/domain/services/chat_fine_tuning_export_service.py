"""Exportação JSONL de amostras aprovadas — playbook Fase 7."""

from __future__ import annotations

import json
from typing import Any


class ChatFineTuningExportService:
    @staticmethod
    def build_jsonl(samples: list[dict]) -> str:
        lines: list[str] = []

        for sample in samples or []:
            if str(sample.get("status")) != "approved":
                continue

            messages = sample.get("messages") or sample.get("messagesJson") or []

            if not isinstance(messages, list) or not messages:
                continue

            payload: dict[str, Any] = {"messages": messages}

            intent = sample.get("intentLabel") or sample.get("intent_label")

            if intent:
                payload["intent"] = str(intent)

            category = sample.get("category")

            if category:
                payload["category"] = str(category)

            lines.append(json.dumps(payload, ensure_ascii=False))

        return "\n".join(lines)

    @staticmethod
    def export_stats(samples: list[dict], *, jsonl: str) -> dict:
        approved = [s for s in samples if str(s.get("status")) == "approved"]
        by_category: dict[str, int] = {}

        for sample in approved:
            key = str(sample.get("category") or "other")
            by_category[key] = by_category.get(key, 0) + 1

        return {
            "sampleCount": len(approved),
            "lineCount": len([line for line in jsonl.splitlines() if line.strip()]),
            "bytes": len(jsonl.encode("utf-8")),
            "byCategory": by_category,
        }
