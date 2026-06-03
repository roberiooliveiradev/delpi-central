"""Agregação admin de memória de sessão e assertividade — Playbook memória §77–78, Fase 9."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ChatSessionMemoryAdminMetricsService:
    MEMORY_FEEDBACK_REASON_IDS: frozenset[str] = frozenset(
        {
            "lost_context",
            "forgot_previous",
            "routing_lost_context",
            "routing_repeated_question",
            "memory_wrong_context",
            "memory_ignored_preference",
            "memory_forgot_product",
            "memory_forgot_period",
            "memory_wrong_canvas",
            "memory_wrong_attachment",
            "memory_repeated_question",
            "memory_stale_context",
            "wrong_product",
        }
    )

    LOSS_ASSERTIVENESS_FLAGS: frozenset[str] = frozenset(
        {
            "follow_up_without_entity_reuse",
            "unnecessary_code_request",
            "stale_product_context",
        }
    )

    @classmethod
    def snapshot_from_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        session_metrics = metadata.get("sessionMemoryMetrics")
        assertiveness = metadata.get("contextAssertiveness")

        if not isinstance(session_metrics, dict) and not isinstance(assertiveness, dict):
            return None

        snapshot: dict[str, Any] = {}

        if isinstance(session_metrics, dict):
            snapshot.update(
                {
                    "memoryUsed": bool(session_metrics.get("memoryUsed")),
                    "entityCount": int(session_metrics.get("entityCount") or 0),
                    "resolvedReferenceCount": int(
                        session_metrics.get("resolvedReferenceCount") or 0
                    ),
                    "preferenceCount": int(session_metrics.get("preferenceCount") or 0),
                    "followUpDetected": bool(session_metrics.get("followUpDetected")),
                    "followUpType": session_metrics.get("followUpType"),
                    "hasProductCode": bool(session_metrics.get("hasProductCode")),
                    "hasPeriod": bool(session_metrics.get("hasPeriod")),
                    "hasBranch": bool(session_metrics.get("hasBranch")),
                    "canvasActive": bool(session_metrics.get("canvasActive")),
                    "hasAmbiguity": bool(session_metrics.get("hasAmbiguity")),
                    "persistedMemoryCleared": bool(
                        session_metrics.get("persistedMemoryCleared")
                    ),
                    "selectiveMemoryCleared": bool(
                        bool(session_metrics.get("selectiveMemoryCleared"))
                    ),
                }
            )

        if isinstance(assertiveness, dict):
            flags = assertiveness.get("flags") if isinstance(assertiveness.get("flags"), list) else []
            snapshot["assertivenessScore"] = assertiveness.get("score")
            snapshot["assertivenessFlags"] = [str(item) for item in flags if item]
            snapshot["followUpResolved"] = bool(assertiveness.get("followUpResolved"))
            snapshot["contextLossRisk"] = cls._context_loss_risk(assertiveness)

        if not snapshot:
            return None

        return snapshot

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        assistant_metadata: dict[str, Any] | None = None,
    ) -> dict:
        snapshot = cls.snapshot_from_metadata(assistant_metadata)

        if snapshot:
            audit_metadata["sessionMemoryAdminMetrics"] = snapshot

        return audit_metadata

    @classmethod
    def aggregate_snapshots(
        cls,
        entries: list[dict[str, Any]],
        *,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        memory_turns = 0
        follow_up_turns = 0
        follow_up_resolved = 0
        context_loss_risk_turns = 0
        low_assertiveness_turns = 0
        ambiguity_turns = 0
        cleared_turns = 0
        entity_turns = 0
        by_flag: Counter[str] = Counter()
        recent: list[dict[str, Any]] = []

        for entry in entries:
            snapshot = entry.get("snapshot") if isinstance(entry.get("snapshot"), dict) else entry

            if not isinstance(snapshot, dict):
                continue

            memory_turns += 1

            if snapshot.get("memoryUsed") or int(snapshot.get("entityCount") or 0) > 0:
                entity_turns += 1

            if snapshot.get("followUpDetected"):
                follow_up_turns += 1

            if snapshot.get("followUpResolved"):
                follow_up_resolved += 1

            if snapshot.get("contextLossRisk"):
                context_loss_risk_turns += 1

            score = snapshot.get("assertivenessScore")

            if isinstance(score, (int, float)) and float(score) < 70:
                low_assertiveness_turns += 1

            if snapshot.get("hasAmbiguity"):
                ambiguity_turns += 1

            if snapshot.get("persistedMemoryCleared") or snapshot.get("selectiveMemoryCleared"):
                cleared_turns += 1

            for flag in snapshot.get("assertivenessFlags") or []:
                token = str(flag).strip()

                if token:
                    by_flag[token] += 1

        for entry in entries[:12]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "action": entry.get("action"),
                    "assertivenessScore": snapshot.get("assertivenessScore"),
                    "contextLossRisk": snapshot.get("contextLossRisk"),
                    "followUpDetected": snapshot.get("followUpDetected"),
                    "entityCount": snapshot.get("entityCount"),
                    "flags": (snapshot.get("assertivenessFlags") or [])[:4],
                }
            )

        follow_up_rate = (
            round(follow_up_resolved / follow_up_turns, 4) if follow_up_turns else None
        )

        return {
            "windowHours": hours,
            "since": since_iso,
            "memoryTurnsCount": memory_turns,
            "entityActiveTurns": entity_turns,
            "followUpTurns": follow_up_turns,
            "followUpResolvedTurns": follow_up_resolved,
            "followUpResolutionRate": follow_up_rate,
            "contextLossRiskTurns": context_loss_risk_turns,
            "lowAssertivenessTurns": low_assertiveness_turns,
            "ambiguityTurns": ambiguity_turns,
            "memoryClearedTurns": cleared_turns,
            "assertivenessFlags": cls._counter_rows(by_flag, limit=10),
            "recent": recent,
            "alerts": cls._usage_alerts(
                memory_turns=memory_turns,
                context_loss_risk_turns=context_loss_risk_turns,
                low_assertiveness_turns=low_assertiveness_turns,
                follow_up_turns=follow_up_turns,
                follow_up_resolved=follow_up_resolved,
            ),
        }

    @classmethod
    def aggregate_feedback_rows(cls, rows: list[dict[str, Any]]) -> dict[str, Any]:
        positive = 0
        negative = 0
        by_reason: Counter[str] = Counter()
        lost_context = 0
        recent: list[dict[str, Any]] = []

        for row in rows:
            if not cls._is_memory_feedback_row(row):
                continue

            rating = int(row.get("rating") or 0)

            if rating == 1:
                positive += 1
            elif rating == -1:
                negative += 1

            reason = str(row.get("reason") or "").strip()

            if reason:
                by_reason[reason] += 1

            if reason in cls.MEMORY_FEEDBACK_REASON_IDS or reason.startswith("memory_"):
                lost_context += 1

            if len(recent) < 12:
                context = (
                    row.get("contextMetadata")
                    if isinstance(row.get("contextMetadata"), dict)
                    else {}
                )
                recent.append(
                    {
                        "messageId": row.get("messageId"),
                        "rating": rating,
                        "reason": reason or None,
                        "usedMemory": context.get("usedMemory"),
                        "createdAt": row.get("createdAt"),
                    }
                )

        total = positive + negative

        return {
            "feedbackTotal": total,
            "feedbackPositive": positive,
            "feedbackNegative": negative,
            "memoryFeedbackCount": total,
            "lostContextFeedbackCount": lost_context,
            "feedbackByReason": dict(by_reason),
            "feedbackRecent": recent,
            "alerts": cls._feedback_alerts(
                negative=negative,
                total=total,
                lost_context=lost_context,
                by_reason=by_reason,
            ),
        }

    @classmethod
    def merge_usage_and_feedback(
        cls,
        usage: dict[str, Any],
        feedback: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(usage)
        merged["feedback"] = feedback
        feedback_alerts = feedback.get("alerts") if isinstance(feedback.get("alerts"), list) else []
        usage_alerts = usage.get("alerts") if isinstance(usage.get("alerts"), list) else []
        merged["alerts"] = (usage_alerts + feedback_alerts)[:8]
        return merged

    @classmethod
    def _context_loss_risk(cls, assertiveness: dict[str, Any]) -> bool:
        score = assertiveness.get("score")

        if isinstance(score, (int, float)) and float(score) < 65:
            return True

        flags = assertiveness.get("flags") if isinstance(assertiveness.get("flags"), list) else []

        return any(str(flag) in cls.LOSS_ASSERTIVENESS_FLAGS for flag in flags)

    @classmethod
    def _is_memory_feedback_row(cls, row: dict[str, Any]) -> bool:
        reason = str(row.get("reason") or "").strip()
        context = (
            row.get("contextMetadata")
            if isinstance(row.get("contextMetadata"), dict)
            else {}
        )

        if reason in cls.MEMORY_FEEDBACK_REASON_IDS or reason.startswith("memory_"):
            return True

        if context.get("usedMemory"):
            return True

        return reason in {"lost_context", "forgot_previous", "wrong_product"}

    @classmethod
    def _counter_rows(cls, counter: Counter[str], *, limit: int = 20) -> list[dict[str, Any]]:
        return [
            {"key": key, "count": count}
            for key, count in counter.most_common(limit)
        ]

    @classmethod
    def _usage_alerts(
        cls,
        *,
        memory_turns: int,
        context_loss_risk_turns: int,
        low_assertiveness_turns: int,
        follow_up_turns: int,
        follow_up_resolved: int,
    ) -> list[dict[str, str]]:
        alerts: list[dict[str, str]] = []

        if memory_turns >= 10 and context_loss_risk_turns >= 3:
            alerts.append(
                {
                    "code": "memory_context_loss_risk",
                    "message": (
                        "Vários turnos com risco de perda de contexto "
                        "(assertividade baixa ou follow-up sem reutilizar entidade)."
                    ),
                }
            )

        if follow_up_turns >= 5 and follow_up_resolved < max(1, follow_up_turns // 3):
            alerts.append(
                {
                    "code": "memory_follow_up_unresolved",
                    "message": "Follow-ups frequentes sem reutilizar entidade da memória.",
                }
            )

        if memory_turns >= 10 and low_assertiveness_turns / memory_turns >= 0.2:
            alerts.append(
                {
                    "code": "memory_low_assertiveness",
                    "message": "Mais de 20% dos turnos com memória têm assertividade abaixo de 70.",
                }
            )

        return alerts[:4]

    @classmethod
    def _feedback_alerts(
        cls,
        *,
        negative: int,
        total: int,
        lost_context: int,
        by_reason: Counter[str],
    ) -> list[dict[str, str]]:
        alerts: list[dict[str, str]] = []

        if lost_context >= 3:
            alerts.append(
                {
                    "code": "context_loss",
                    "message": "Perda de contexto reportada em feedback de memória.",
                }
            )

        for reason, count in by_reason.most_common(4):
            if count >= 3 and (
                reason.startswith("memory_") or reason in cls.MEMORY_FEEDBACK_REASON_IDS
            ):
                alerts.append(
                    {
                        "code": f"recurring_{reason}",
                        "message": f"Feedback recorrente de memória: {reason} ({count}x).",
                    }
                )

        if total >= 5 and negative / total >= 0.4:
            alerts.append(
                {
                    "code": "memory_negative_feedback",
                    "message": "Taxa elevada de feedback negativo em turnos com memória.",
                }
            )

        return alerts[:6]
