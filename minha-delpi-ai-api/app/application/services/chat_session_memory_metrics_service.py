"""Métricas leves de memória de sessão (metadata / adminDebug)."""

from __future__ import annotations

from typing import Any


class ChatSessionMemoryMetricsService:
    @classmethod
    def build_snapshot(cls, snapshot: dict | None) -> dict[str, Any] | None:
        if not isinstance(snapshot, dict):
            return None

        entities = snapshot.get("lastEntities") or {}
        resolved = snapshot.get("resolvedReferences") or []
        preferences = snapshot.get("preferencesApplied") or []
        last_action = snapshot.get("lastAction") or {}
        canvas = snapshot.get("canvas") or {}

        if not (
            snapshot.get("memoryUsed")
            or entities
            or resolved
            or preferences
            or last_action
            or (isinstance(canvas, dict) and canvas.get("active"))
        ):
            return None

        return {
            "memoryUsed": bool(snapshot.get("memoryUsed")),
            "entityCount": len([v for v in entities.values() if v not in (None, "", [])]),
            "resolvedReferenceCount": len(resolved),
            "preferenceCount": len(preferences),
            "followUpDetected": bool(snapshot.get("followUpDetected")),
            "followUpType": snapshot.get("followUpType"),
            "hasProductCode": bool(entities.get("productCode")),
            "hasPeriod": bool(entities.get("period")),
            "hasBranch": bool(entities.get("branch")),
            "lastActionName": (
                last_action.get("name") if isinstance(last_action, dict) else None
            ),
            "canvasActive": (
                bool(canvas.get("active")) if isinstance(canvas, dict) else False
            ),
            "persistedMemoryApplied": bool(snapshot.get("persistedMemoryApplied")),
            "persistedMemoryCleared": bool(snapshot.get("persistedMemoryCleared")),
            "selectiveMemoryCleared": snapshot.get("selectiveMemoryCleared") or [],
            "agentContextReset": bool(snapshot.get("agentContextReset")),
            "hasAmbiguity": bool(snapshot.get("memoryAmbiguity")),
        }

    @classmethod
    def attach_to_assistant_metadata(cls, metadata: dict, *, snapshot: dict | None) -> None:
        metrics = cls.build_snapshot(snapshot)

        if metrics:
            metadata["sessionMemoryMetrics"] = metrics
