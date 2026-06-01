"""Métricas do Especialista SQL Avançado — Playbook §53."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ChatAdvancedSqlMetricsService:
    @classmethod
    def snapshot_from_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        advanced = metadata.get("sqlAdvanced")

        if not isinstance(advanced, dict):
            return None

        mode = str(advanced.get("mode") or "none")
        performance = advanced.get("performance") if isinstance(advanced.get("performance"), dict) else {}
        features = performance.get("features") if isinstance(performance.get("features"), dict) else {}
        review = advanced.get("review") if isinstance(advanced.get("review"), dict) else {}
        workspace = advanced.get("workspace") if isinstance(advanced.get("workspace"), dict) else {}

        return {
            "mode": mode,
            "dialect": (advanced.get("dialect") or {}).get("dialect"),
            "blocked": bool(advanced.get("blocked")),
            "schemaPrefetchRecommended": bool(advanced.get("schemaPrefetchRecommended")),
            "usesCte": bool(features.get("usesCte")),
            "usesWindowFunction": bool(features.get("usesWindowFunction")),
            "performanceIssueCount": len(performance.get("issues") or []),
            "reviewRiskLevel": review.get("riskLevel"),
            "hasActiveQuery": bool(workspace.get("hasActiveQuery")),
            "incrementalEditReady": bool(workspace.get("incrementalEditReady")),
        }

    @classmethod
    def attach_to_assistant_metadata(
        cls,
        metadata: dict,
        *,
        tool_context: dict | None = None,
    ) -> None:
        advanced = None

        if isinstance(tool_context, dict):
            advanced = tool_context.get("sqlAdvanced")

        if advanced is None:
            advanced = metadata.get("sqlAdvanced")

        if not isinstance(advanced, dict):
            return

        metadata["sqlAdvancedMetrics"] = cls.build_snapshot(advanced)

    @classmethod
    def build_snapshot(cls, advanced: dict[str, Any]) -> dict[str, Any]:
        performance = advanced.get("performance") if isinstance(advanced.get("performance"), dict) else {}
        features = performance.get("features") if isinstance(performance.get("features"), dict) else {}
        review = advanced.get("review") if isinstance(advanced.get("review"), dict) else {}
        workspace = advanced.get("workspace") if isinstance(advanced.get("workspace"), dict) else {}
        dialect = advanced.get("dialect") if isinstance(advanced.get("dialect"), dict) else {}

        return {
            "mode": advanced.get("mode"),
            "dialect": dialect.get("dialect"),
            "blocked": bool(advanced.get("blocked")),
            "schemaPrefetchRecommended": bool(advanced.get("schemaPrefetchRecommended")),
            "usesCte": bool(features.get("usesCte")),
            "usesWindowFunction": bool(features.get("usesWindowFunction")),
            "performanceIssueCount": len(performance.get("issues") or []),
            "performanceScore": performance.get("score"),
            "reviewRiskLevel": review.get("riskLevel"),
            "hasActiveQuery": bool(workspace.get("hasActiveQuery")),
            "incrementalEditReady": bool(workspace.get("incrementalEditReady")),
        }

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        assistant_metadata: dict[str, Any] | None = None,
        tool_context: dict | None = None,
    ) -> dict:
        snapshot = None

        if isinstance(assistant_metadata, dict):
            metrics = assistant_metadata.get("sqlAdvancedMetrics")

            if isinstance(metrics, dict):
                snapshot = metrics

        if snapshot is None and isinstance(tool_context, dict):
            advanced = tool_context.get("sqlAdvanced")

            if isinstance(advanced, dict):
                snapshot = cls.build_snapshot(advanced)

        if snapshot:
            audit_metadata["sqlAdvancedMetrics"] = snapshot

        return audit_metadata

    @classmethod
    def aggregate_snapshots(
        cls,
        entries: list[dict[str, Any]],
        *,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        by_mode: Counter[str] = Counter()
        by_dialect: Counter[str] = Counter()
        blocked = 0
        cte_count = 0
        window_count = 0
        incremental = 0
        schema_prefetch = 0
        recent: list[dict[str, Any]] = []

        for entry in entries:
            snapshot = entry.get("snapshot") if isinstance(entry.get("snapshot"), dict) else entry

            if not isinstance(snapshot, dict):
                continue

            by_mode[str(snapshot.get("mode") or "unknown")] += 1
            by_dialect[str(snapshot.get("dialect") or "unknown")] += 1

            if snapshot.get("blocked"):
                blocked += 1

            if snapshot.get("usesCte"):
                cte_count += 1

            if snapshot.get("usesWindowFunction"):
                window_count += 1

            if snapshot.get("incrementalEditReady"):
                incremental += 1

            if snapshot.get("schemaPrefetchRecommended"):
                schema_prefetch += 1

        for entry in entries[:12]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "action": entry.get("action"),
                    "mode": snapshot.get("mode"),
                    "dialect": snapshot.get("dialect"),
                    "blocked": snapshot.get("blocked"),
                }
            )

        runs = sum(by_mode.values())

        return {
            "windowHours": hours,
            "since": since_iso,
            "runsCount": runs,
            "blockedCount": blocked,
            "cteUsageCount": cte_count,
            "windowFunctionUsageCount": window_count,
            "incrementalEditCount": incremental,
            "schemaPrefetchCount": schema_prefetch,
            "byMode": dict(by_mode),
            "byDialect": dict(by_dialect),
            "recent": recent,
        }
