"""Agregação de métricas textuais para admin — Playbook 03 §29."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ChatTextTaskAdminMetricsService:
    @classmethod
    def snapshot_from_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        metrics = metadata.get("textTaskMetrics")

        if not isinstance(metrics, dict):
            return None

        mixed = metadata.get("textTaskMixed")
        quality = metadata.get("textTaskQuality")
        versions = metadata.get("textCanvasVersions")

        snapshot = {
            "type": metrics.get("type"),
            "subtype": metrics.get("subtype"),
            "tone": metrics.get("tone"),
            "deliverFinalOnly": bool(metrics.get("deliverFinalOnly")),
            "source": metrics.get("source"),
        }

        if isinstance(mixed, dict):
            snapshot["mixed"] = True
            snapshot["mixedCategory"] = mixed.get("textCategory")
            snapshot["mixedDraft"] = bool(mixed.get("draftAttached"))

        if isinstance(quality, dict):
            snapshot["qualityPassed"] = bool(quality.get("passed"))
            snapshot["qualityIssues"] = len(quality.get("checks") or [])

        if isinstance(versions, list):
            snapshot["canvasVersionCount"] = len(versions)

        return snapshot

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        assistant_metadata: dict[str, Any] | None = None,
    ) -> dict:
        snapshot = cls.snapshot_from_metadata(assistant_metadata)

        if snapshot and snapshot.get("subtype"):
            audit_metadata["textTaskMetrics"] = snapshot

        return audit_metadata

    @classmethod
    def aggregate_snapshots(
        cls,
        entries: list[dict[str, Any]],
        *,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        by_subtype: Counter[str] = Counter()
        by_type: Counter[str] = Counter()
        mixed_count = 0
        quality_failed = 0
        canvas_updates = 0
        recent: list[dict[str, Any]] = []

        for entry in entries:
            snapshot = entry.get("snapshot") if isinstance(entry.get("snapshot"), dict) else entry

            if not isinstance(snapshot, dict):
                continue

            subtype = str(snapshot.get("subtype") or "unknown")
            by_subtype[subtype] += 1
            task_type = str(snapshot.get("type") or "unknown")
            by_type[task_type] += 1

            if snapshot.get("mixed"):
                mixed_count += 1

            if snapshot.get("qualityPassed") is False:
                quality_failed += 1

            if int(snapshot.get("canvasVersionCount") or 0) > 1:
                canvas_updates += 1

        for entry in entries[:12]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "action": entry.get("action"),
                    "subtype": snapshot.get("subtype"),
                    "type": snapshot.get("type"),
                    "mixed": snapshot.get("mixed"),
                    "qualityPassed": snapshot.get("qualityPassed"),
                }
            )

        return {
            "windowHours": hours,
            "since": since_iso,
            "textTasksCount": len(entries),
            "mixedTurnCount": mixed_count,
            "qualityFailedCount": quality_failed,
            "canvasVersionedCount": canvas_updates,
            "bySubtype": dict(by_subtype),
            "byType": dict(by_type),
            "recent": recent,
        }
