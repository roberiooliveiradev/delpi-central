"""Foco operacional derivado no ``contextSnapshot`` — cache, não fonte editável."""

from __future__ import annotations

from typing import Any

OPERATIONAL_FOCUS_KEY = "operationalFocus"
LEGACY_LAST_ENTITIES_KEY = "lastEntities"
LEGACY_ACTIVE_ENTITIES_KEY = "activeEntities"


class ChatSnapshotOperationalFocus:
    @classmethod
    def get(cls, snapshot: dict[str, Any] | None) -> dict[str, str]:
        """Lê foco operacional; aceita snapshots antigos com ``lastEntities``."""
        snap = snapshot or {}

        for key in (OPERATIONAL_FOCUS_KEY, LEGACY_LAST_ENTITIES_KEY, LEGACY_ACTIVE_ENTITIES_KEY):
            block = snap.get(key)

            if not isinstance(block, dict) or not block:
                continue

            return {
                str(name).strip(): str(value).strip()
                for name, value in block.items()
                if value is not None and str(value).strip()
            }

        return {}

    @classmethod
    def set(cls, snapshot: dict[str, Any], focus: dict[str, str] | None) -> dict[str, Any]:
        """Grava só ``operationalFocus`` e remove chaves legadas do snapshot."""
        result = dict(snapshot)
        merged = {
            str(name).strip(): str(value).strip()
            for name, value in (focus or {}).items()
            if value is not None and str(value).strip()
        }
        result[OPERATIONAL_FOCUS_KEY] = merged
        result.pop(LEGACY_LAST_ENTITIES_KEY, None)
        result.pop(LEGACY_ACTIVE_ENTITIES_KEY, None)
        return result

    @classmethod
    def normalize(cls, snapshot: dict[str, Any] | None) -> dict[str, Any]:
        """Migra chaves legadas para ``operationalFocus`` antes de processar o turno."""
        if not snapshot:
            return {}

        focus = cls.get(snapshot)

        if not focus:
            return dict(snapshot)

        return cls.set(dict(snapshot), focus)

    @classmethod
    def overlay_get(cls, overlay: dict[str, Any] | None) -> dict[str, str]:
        return cls.get(overlay)

    @classmethod
    def overlay_with_focus(
        cls,
        overlay: dict[str, Any],
        focus: dict[str, str],
        *,
        behavior_instructions: dict[str, str] | None = None,
        user_context_items: list | None = None,
    ) -> dict[str, Any]:
        result = cls.set(overlay, focus)

        if behavior_instructions is not None:
            result["behaviorInstructions"] = behavior_instructions

        if user_context_items is not None:
            result["userContextItems"] = user_context_items

        return result
