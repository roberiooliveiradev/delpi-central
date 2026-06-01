"""Agregação de métricas de erro/vazio para admin — Playbook 06 Fase 5."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ChatErrorHandlingAdminMetricsService:
    @classmethod
    def snapshot_from_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        error_handling = metadata.get("errorHandling")

        if not isinstance(error_handling, dict):
            return None

        error_type = str(error_handling.get("type") or "").strip()

        if not error_type:
            return None

        suggestions = error_handling.get("suggestions") or []

        auto_recovery = error_handling.get("autoRecovery")

        return {
            "type": error_type,
            "severity": error_handling.get("severity"),
            "recoverable": bool(error_handling.get("recoverable")),
            "apiFailed": bool(error_handling.get("apiFailed")),
            "suggestionCount": len(suggestions) if isinstance(suggestions, list) else 0,
            "hasAutoRecovery": isinstance(auto_recovery, dict),
        }

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        assistant_metadata: dict[str, Any] | None = None,
    ) -> dict:
        snapshot = cls.snapshot_from_metadata(assistant_metadata)

        if snapshot:
            audit_metadata["errorHandlingMetrics"] = snapshot

        return audit_metadata

    @classmethod
    def aggregate(
        cls,
        *,
        entries: list[dict[str, Any]],
        recovery_clicks: list[dict[str, Any]] | None = None,
        recovery_attempts: list[dict[str, Any]] | None = None,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        by_type: Counter[str] = Counter()
        recoverable = 0
        api_failed = 0
        auto_recovery_plans = 0
        recent: list[dict[str, Any]] = []

        for entry in entries:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            error_type = str(snapshot.get("type") or "unknown")
            by_type[error_type] += 1

            if snapshot.get("recoverable"):
                recoverable += 1

            if snapshot.get("apiFailed"):
                api_failed += 1

            if snapshot.get("hasAutoRecovery"):
                auto_recovery_plans += 1

            if len(recent) < 12:
                recent.append(
                    {
                        "loggedAt": entry.get("loggedAt"),
                        "type": error_type,
                        "severity": snapshot.get("severity"),
                        "recoverable": snapshot.get("recoverable"),
                    }
                )

        total = sum(by_type.values())
        clicks = recovery_clicks or []
        attempts = recovery_attempts or []
        successful_attempts = sum(
            1
            for entry in attempts
            if isinstance(entry.get("snapshot"), dict)
            and entry["snapshot"].get("ok")
        )

        return {
            "windowHours": hours,
            "since": since_iso,
            "totalEvents": total,
            "recoverableCount": recoverable,
            "apiFailedCount": api_failed,
            "autoRecoveryPlans": auto_recovery_plans,
            "recoveryClicksCount": len(clicks),
            "recoveryAttemptsCount": len(attempts),
            "recoverySuccessCount": successful_attempts,
            "recoverySuccessRate": (
                successful_attempts / len(attempts) if attempts else 0.0
            ),
            "byType": [
                {"type": error_type, "count": count}
                for error_type, count in by_type.most_common(12)
            ],
            "recent": recent,
        }
