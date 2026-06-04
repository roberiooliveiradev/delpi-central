"""Foco operacional derivado no ``contextSnapshot`` — cache, não fonte editável."""

from __future__ import annotations

from typing import Any

OPERATIONAL_FOCUS_KEY = "operationalFocus"

# Chaves removidas do contrato (pré-produção); ignoradas se ainda aparecerem em JSON antigo local.
_REMOVED_SNAPSHOT_KEYS = frozenset({"lastEntities", "activeEntities"})


class ChatSnapshotOperationalFocus:
    @classmethod
    def get(cls, snapshot: dict[str, Any] | None) -> dict[str, str]:
        block = (snapshot or {}).get(OPERATIONAL_FOCUS_KEY)

        if not isinstance(block, dict) or not block:
            return {}

        return {
            str(name).strip(): str(value).strip()
            for name, value in block.items()
            if value is not None and str(value).strip()
        }

    @classmethod
    def set(cls, snapshot: dict[str, Any], focus: dict[str, str] | None) -> dict[str, Any]:
        """Grava só ``operationalFocus`` e remove chaves obsoletas do snapshot."""
        result = cls.strip_removed_keys(dict(snapshot))

        result[OPERATIONAL_FOCUS_KEY] = {
            str(name).strip(): str(value).strip()
            for name, value in (focus or {}).items()
            if value is not None and str(value).strip()
        }

        return result

    @classmethod
    def strip_removed_keys(cls, snapshot: dict[str, Any] | None) -> dict[str, Any]:
        result = dict(snapshot or {})

        for key in _REMOVED_SNAPSHOT_KEYS:
            result.pop(key, None)

        return result

    @classmethod
    def normalize(cls, snapshot: dict[str, Any] | None) -> dict[str, Any]:
        """Garante snapshot sem chaves obsoletas antes do pré-turno."""
        result = cls.strip_removed_keys(snapshot)

        if OPERATIONAL_FOCUS_KEY not in result:
            result[OPERATIONAL_FOCUS_KEY] = cls.get(result)

        return result

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
