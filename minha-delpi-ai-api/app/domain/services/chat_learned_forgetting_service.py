"""Esquecimento controlado de contexto — Playbook §33 / Fase 7."""

from __future__ import annotations

from typing import Any


class ChatLearnedForgettingService:
    MAX_PRODUCT_HISTORY = 3
    MAX_EPISODES_AFTER_TOPIC_CHANGE = 2

    @classmethod
    def apply_to_snapshot(cls, snapshot: dict, *, message: str | None = None) -> dict:
        result = dict(snapshot)
        forgotten: list[str] = []
        state = dict(result.get("conversationState") or {})
        active_topic = str(state.get("activeTopic") or "").strip().lower()

        if result.get("preferencesTopicChanged"):
            codes = list((result.get("previousProductCodes") or []))

            if len(codes) > 1:
                result["previousProductCodes"] = codes[-1:]
                forgotten.append("previousProductCodes:topic_change")

            episodes = list(result.get("episodicMemory") or [])

            if episodes:
                result["episodicMemory"] = episodes[: cls.MAX_EPISODES_AFTER_TOPIC_CHANGE]
                forgotten.append("episodicMemory:trimmed")

            hints = dict(result.get("referenceHints") or {})

            if hints.pop("lastSqlSnippet", None):
                result["referenceHints"] = hints
                forgotten.append("referenceHints:sql_snippet")

        stack = list(state.get("taskStack") or [])
        pruned_stack: list[dict[str, Any]] = []

        for task in stack:
            if not isinstance(task, dict):
                continue

            if str(task.get("status") or "") == "completed":
                forgotten.append(f"taskStack:completed:{task.get('label') or task.get('type')}")
                continue

            pruned_stack.append(task)

        if len(pruned_stack) != len(stack):
            state["taskStack"] = pruned_stack[-5:]

        task = state.get("activeTask")

        if isinstance(task, dict) and str(task.get("status") or "") == "completed":
            state["activeTask"] = None
            forgotten.append("activeTask:completed")

        codes = list((result.get("previousProductCodes") or []))

        if len(codes) > cls.MAX_PRODUCT_HISTORY:
            result["previousProductCodes"] = codes[-cls.MAX_PRODUCT_HISTORY :]
            forgotten.append("previousProductCodes:limit")

        from app.domain.services.chat_snapshot_operational_focus import (
            ChatSnapshotOperationalFocus,
        )

        focus = ChatSnapshotOperationalFocus.get(result)

        if active_topic and "sql" not in active_topic:
            for key in ("warehouse",):
                if focus.pop(key, None):
                    forgotten.append(f"operationalFocus:{key}")

        result = ChatSnapshotOperationalFocus.set(result, focus)
        result["conversationState"] = state

        if forgotten:
            result["forgottenMemoryKeys"] = list(
                dict.fromkeys((result.get("forgottenMemoryKeys") or []) + forgotten)
            )[-16:]

        return result

    @classmethod
    def compact_for_admin_debug(cls, snapshot: dict | None) -> dict[str, Any]:
        keys = (snapshot or {}).get("forgottenMemoryKeys") or []

        return {
            "count": len(keys),
            "recent": keys[-4:],
        }
