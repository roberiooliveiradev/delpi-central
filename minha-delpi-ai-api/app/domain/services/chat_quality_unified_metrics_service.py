"""Visão unificada de qualidade — Playbook 10."""

from __future__ import annotations

from typing import Any


class ChatQualityUnifiedMetricsService:
    @classmethod
    def build(
        cls,
        *,
        feedback: dict[str, Any] | None,
        metrics: dict[str, Any] | None,
        security: dict[str, Any] | None,
        adoption: dict[str, Any] | None,
        presentation: dict[str, Any] | None = None,
        presentation_coverage: dict[str, Any] | None = None,
        session_memory: dict[str, Any] | None = None,
        rag_settings: dict[str, Any] | None = None,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        feedback = feedback if isinstance(feedback, dict) else {}
        metrics = metrics if isinstance(metrics, dict) else {}
        security = security if isinstance(security, dict) else {}
        adoption = adoption if isinstance(adoption, dict) else {}
        presentation = presentation if isinstance(presentation, dict) else {}
        presentation_coverage = (
            presentation_coverage if isinstance(presentation_coverage, dict) else {}
        )
        session_memory = session_memory if isinstance(session_memory, dict) else {}
        rag_settings = rag_settings if isinstance(rag_settings, dict) else {}
        advanced = metrics.get("advanced") if isinstance(metrics.get("advanced"), dict) else {}
        coverage_summary = (
            presentation_coverage.get("summary")
            if isinstance(presentation_coverage.get("summary"), dict)
            else {}
        )
        coverage_metrics = (
            coverage_summary.get("metrics")
            if isinstance(coverage_summary.get("metrics"), dict)
            else {}
        )

        return {
            "windowHours": hours,
            "since": since_iso,
            "health": {
                "csat": feedback.get("csat"),
                "errorRate": metrics.get("errorRate24h"),
                "toolUsageRate": metrics.get("toolUsageRate24h"),
                "latencyAvgMs": advanced.get("latencyAvgMs"),
                "assertivenessRate": advanced.get("assertivenessRate"),
                "lostContextCount": feedback.get("lostContextCount"),
            },
            "feedback": {
                "total": feedback.get("totalFeedback"),
                "positive": feedback.get("positiveCount"),
                "negative": feedback.get("negativeCount"),
                "topReasons": (feedback.get("feedbackByReason") or [])[:5],
                "topIntents": (feedback.get("feedbackByIntent") or [])[:5],
                "alerts": feedback.get("alerts") or [],
            },
            "adoption": adoption,
            "efficiency": {
                "instrumentedMessages": advanced.get("instrumentedMessages"),
                "tokensUsed": advanced.get("tokensUsed"),
                "estimatedCost": advanced.get("estimatedCost"),
                "latencyAvgMs": advanced.get("latencyAvgMs"),
                "simpleTurnLatencyAvgMs": advanced.get("simpleTurnLatencyAvgMs"),
                "simpleTurnCount": advanced.get("simpleTurnCount"),
                "messagesPerSession": cls._messages_per_session(adoption),
            },
            "security": {
                "blockedCount": security.get("blockedCount"),
                "flaggedCount": security.get("flaggedCount"),
                "scannedCount": security.get("scannedCount"),
                "totalEvents": security.get("totalEvents"),
                "flagDistribution": security.get("flagDistribution") or [],
            },
            "operations": {
                "sessionsTotal": metrics.get("sessions"),
                "messagesTotal": metrics.get("messages"),
                "recentToolCalls": metrics.get("recentToolCalls24h"),
                "recentErrors": metrics.get("recentErrors24h"),
            },
            "presentation": {
                "sessionFormatRespectedRatio": presentation.get("sessionFormatRespectedRatio"),
                "explicitPreferenceTurns": presentation.get("explicitPreferenceTurns"),
                "formatRespectedTurns": presentation.get("formatRespectedTurns"),
                "responsesWithRichPresentation": presentation.get("responsesWithRichPresentation"),
                "viewSwitchRate": presentation.get("viewSwitchRate"),
                "tierBPlusRatio": coverage_metrics.get("tierBPlusRatio"),
                "profileCoverageRatio": coverage_summary.get("profileCoverageRatio"),
                "operationCount": coverage_summary.get("operationCount"),
            },
            "sessionMemory": {
                "memoryTurnsCount": session_memory.get("memoryTurnsCount"),
                "lowAssertivenessTurns": session_memory.get("lowAssertivenessTurns"),
                "contextLossRiskTurns": session_memory.get("contextLossRiskTurns"),
                "followUpResolutionRate": session_memory.get("followUpResolutionRate"),
                "lostContextFeedbackCount": (
                    (session_memory.get("feedback") or {}).get("lostContextFeedbackCount")
                    if isinstance(session_memory.get("feedback"), dict)
                    else None
                ),
            },
            "rag": {
                "ragContextMinScore": rag_settings.get("ragContextMinScore"),
                "ragHybridEnabled": rag_settings.get("ragHybridEnabled"),
                "ragFtsEnabled": rag_settings.get("ragFtsEnabled"),
                "defaults": rag_settings.get("defaults") or {},
            },
        }

    @classmethod
    def _messages_per_session(cls, adoption: dict[str, Any]) -> float | None:
        messages = int(adoption.get("messagesSent") or 0)
        sessions = int(adoption.get("activeSessions") or 0)

        if sessions <= 0:
            return None

        return round(messages / sessions, 2)
