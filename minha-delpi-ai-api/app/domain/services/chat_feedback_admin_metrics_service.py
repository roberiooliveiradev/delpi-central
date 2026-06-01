"""Agregação admin de feedback do usuário — Playbook 10."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ChatFeedbackAdminMetricsService:
    @classmethod
    def feedback_audit_metadata(
        cls,
        *,
        message_id: str,
        session_id: str | None,
        rating: int,
        reason: str | None,
        comment: str | None,
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "messageId": message_id,
            "sessionId": session_id,
            "rating": rating,
        }

        if reason:
            payload["reason"] = reason

        if comment:
            payload["comment"] = comment

        if isinstance(context, dict):
            payload["context"] = {
                key: context.get(key)
                for key in (
                    "intent",
                    "subIntent",
                    "confidence",
                    "agentId",
                    "agent",
                    "usedTool",
                    "toolPath",
                    "usedRag",
                    "usedWeb",
                    "usedMemory",
                    "presentationType",
                    "durationMs",
                    "error",
                )
                if context.get(key) is not None
            }

        return payload

    @classmethod
    def aggregate_rows(
        cls,
        rows: list[dict[str, Any]],
        *,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        positive = 0
        negative = 0
        by_reason: Counter[str] = Counter()
        by_intent: Counter[str] = Counter()
        by_agent: Counter[str] = Counter()
        by_tool: Counter[str] = Counter()
        by_presentation: Counter[str] = Counter()
        lost_context = 0
        recent: list[dict[str, Any]] = []

        for row in rows:
            rating = int(row.get("rating") or 0)

            if rating == 1:
                positive += 1
            elif rating == -1:
                negative += 1

            reason = str(row.get("reason") or "").strip()

            if reason:
                by_reason[reason] += 1

            context = row.get("contextMetadata") if isinstance(row.get("contextMetadata"), dict) else {}
            intent = str(context.get("intent") or "unknown")
            by_intent[intent] += 1

            agent = str(context.get("agent") or context.get("agentId") or "unknown")
            by_agent[agent] += 1

            tool_path = str(context.get("toolPath") or "").strip()

            if tool_path:
                by_tool[tool_path] += 1

            presentation = str(context.get("presentationType") or "").strip()

            if presentation:
                by_presentation[presentation] += 1

            if reason in {"lost_context", "routing_lost_context", "forgot_previous", "routing_repeated_question"}:
                lost_context += 1

            if len(recent) < 20:
                recent.append(
                    {
                        "messageId": row.get("messageId"),
                        "rating": rating,
                        "reason": reason or None,
                        "intent": context.get("intent"),
                        "agent": context.get("agent"),
                        "toolPath": context.get("toolPath"),
                        "createdAt": row.get("createdAt"),
                    }
                )

        total = positive + negative
        csat = round(positive / total, 4) if total else None

        return {
            "windowHours": hours,
            "since": since_iso,
            "totalFeedback": total,
            "positiveCount": positive,
            "negativeCount": negative,
            "csat": csat,
            "lostContextCount": lost_context,
            "feedbackByReason": cls._counter_rows(by_reason),
            "feedbackByIntent": cls._counter_rows(by_intent, limit=12),
            "feedbackByAgent": cls._counter_rows(by_agent, limit=12),
            "feedbackByToolPath": cls._counter_rows(by_tool, limit=12),
            "feedbackByPresentation": cls._counter_rows(by_presentation, limit=8),
            "recentFeedback": recent,
            "alerts": cls._build_alerts(
                negative=negative,
                total=total,
                lost_context=lost_context,
                by_reason=by_reason,
            ),
        }

    @classmethod
    def _counter_rows(cls, counter: Counter[str], *, limit: int = 20) -> list[dict[str, Any]]:
        return [
            {"key": key, "count": count}
            for key, count in counter.most_common(limit)
        ]

    @classmethod
    def _build_alerts(
        cls,
        *,
        negative: int,
        total: int,
        lost_context: int,
        by_reason: Counter[str],
    ) -> list[dict[str, str]]:
        alerts: list[dict[str, str]] = []

        if total >= 5 and negative / total >= 0.35:
            alerts.append(
                {
                    "code": "high_negative_rate",
                    "message": "Taxa de feedback negativo acima de 35% na janela.",
                }
            )

        if lost_context >= 3:
            alerts.append(
                {
                    "code": "context_loss",
                    "message": "Perda de contexto reportada em múltiplos feedbacks.",
                }
            )

        for reason, count in by_reason.most_common(3):
            if count >= 5 and reason.startswith(("wrong_", "routing_", "text_", "error_")):
                alerts.append(
                    {
                        "code": f"recurring_{reason}",
                        "message": f"Motivo recorrente: {reason} ({count}x).",
                    }
                )

        return alerts[:6]
