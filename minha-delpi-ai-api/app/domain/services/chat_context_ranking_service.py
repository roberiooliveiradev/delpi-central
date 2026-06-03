"""Ranking de memórias para o prompt — Playbook memória e contexto (Fase 5, §22)."""

from __future__ import annotations

from typing import Any


class ChatContextRankingService:
    WEIGHT_SEMANTIC = 0.35
    WEIGHT_RECENCY = 0.20
    WEIGHT_TASK = 0.15
    WEIGHT_SOURCE = 0.10
    WEIGHT_PREFERENCE = 0.10
    WEIGHT_CONFIDENCE = 0.10

    @classmethod
    def rank_hits(
        cls,
        hits: list[dict[str, Any]],
        *,
        message: str | None = None,
        snapshot: dict | None = None,
        limit: int = 6,
    ) -> list[dict[str, Any]]:
        if not hits:
            return []

        snap = snapshot or {}
        task_type = cls._active_task_type(snap)
        preference_labels = {
            str(item).lower()
            for item in (snap.get("preferencesApplied") or [])
        }

        scored: list[tuple[float, dict[str, Any]]] = []

        for hit in hits:
            ranked = dict(hit)
            ranked["rankScore"] = cls._score_hit(
                hit,
                message=message,
                task_type=task_type,
                preference_labels=preference_labels,
            )
            scored.append((float(ranked["rankScore"]), ranked))

        scored.sort(key=lambda item: item[0], reverse=True)

        return [item[1] for item in scored[: max(1, limit)]]

    @classmethod
    def _score_hit(
        cls,
        hit: dict[str, Any],
        *,
        message: str | None,
        task_type: str | None,
        preference_labels: set[str],
    ) -> float:
        semantic = min(1.0, max(0.0, float(hit.get("score") or hit.get("semanticScore") or 0)))
        recency = min(1.0, max(0.0, float(hit.get("recencyScore") or 0.5)))
        task_match = 1.0 if hit.get("taskMatch") else 0.0

        if not task_match and task_type:
            hint = str(hit.get("taskHint") or hit.get("kind") or "").lower()

            if task_type in hint or hint in task_type:
                task_match = 0.85

        source_authority = min(1.0, max(0.0, float(hit.get("sourceAuthority") or 0.6)))
        preference_match = 0.0

        for label in preference_labels:
            title = str(hit.get("title") or "").lower()

            if label and label.split("=")[0] in title:
                preference_match = 1.0
                break

        confidence = min(1.0, max(0.0, float(hit.get("confidence") or semantic)))

        return (
            cls.WEIGHT_SEMANTIC * semantic
            + cls.WEIGHT_RECENCY * recency
            + cls.WEIGHT_TASK * task_match
            + cls.WEIGHT_SOURCE * source_authority
            + cls.WEIGHT_PREFERENCE * preference_match
            + cls.WEIGHT_CONFIDENCE * confidence
        )

    @staticmethod
    def _active_task_type(snapshot: dict) -> str | None:
        task = (snapshot.get("conversationState") or {}).get("activeTask")

        if isinstance(task, dict):
            return str(task.get("type") or "") or None

        return None
