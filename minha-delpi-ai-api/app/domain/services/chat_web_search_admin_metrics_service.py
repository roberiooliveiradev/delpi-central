"""Métricas admin de pesquisa web — Playbook 08 Fase 5."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_OFFICIAL_SOURCE_TYPES = frozenset(
    {
        "official",
        "official_manufacturer",
        "government",
        "official_pdf",
        "manufacturer",
    }
)

_WEB_FEEDBACK_REASON_IDS = frozenset(
    {
        "web_bad_source",
        "web_outdated_source",
        "web_missing_official",
        "web_superficial",
        "web_should_english",
        "web_mixed_internal",
        "web_no_sources_shown",
        "web_divergence_unexplained",
        "routing_should_web",
        "routing_unneeded_web",
        "missing_source",
    }
)


@lru_cache(maxsize=1)
def _web_follow_up_labels() -> frozenset[str]:
    playbook = ChatAssistantContentService.load_personality_playbook()
    labels: set[str] = set()

    for key in ("webSearchFollowUpChips", "webSearchFollowUpChipsNoResults"):
        block = playbook.get(key) or {}

        if isinstance(block, dict):
            labels.update(str(label).strip() for label in block.keys() if str(label).strip())

    return frozenset(labels)


class ChatWebSearchAdminMetricsService:
    @classmethod
    def web_follow_up_labels(cls) -> frozenset[str]:
        return _web_follow_up_labels()

    @classmethod
    def is_web_feedback_reason(cls, reason: str | None) -> bool:
        normalized = str(reason or "").strip()

        return bool(normalized) and normalized in _WEB_FEEDBACK_REASON_IDS

    @classmethod
    def snapshot_from_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        research = metadata.get("webSearchResearch")

        if not isinstance(research, dict):
            return None

        sites = research.get("sites") or []
        official_sources = 0

        if isinstance(sites, list):
            for site in sites:
                if not isinstance(site, dict):
                    continue

                source_type = str(site.get("sourceType") or "").strip()
                quality = site.get("sourceQuality")

                if isinstance(quality, dict):
                    source_type = str(quality.get("type") or source_type).strip()

                if site.get("isOfficial") or source_type in _OFFICIAL_SOURCE_TYPES:
                    official_sources += 1

        query_security = research.get("querySecurity")
        redacted = False

        if isinstance(query_security, dict):
            redacted = bool(query_security.get("redacted"))

        search_status = str(research.get("searchStatus") or "").strip()

        return {
            "searchStatus": search_status or None,
            "sourceCount": int(research.get("sourceCount") or 0),
            "confidence": research.get("confidence"),
            "preferOfficial": bool(research.get("preferOfficial")),
            "searchMode": research.get("searchMode"),
            "synthesized": bool(research.get("synthesized")),
            "hasOfficialSource": official_sources > 0,
            "officialSourceCount": official_sources,
            "queryRedacted": redacted,
            "durationMs": research.get("durationMs"),
            "searchIntent": research.get("searchIntent"),
        }

    @classmethod
    def build_admin_debug_web_search(
        cls,
        *,
        tool_context: dict[str, Any] | None,
        assistant_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        payload = None

        if isinstance(tool_context, dict):
            payload = tool_context.get("webSearchPayload")

        research = None

        if isinstance(assistant_metadata, dict):
            research = assistant_metadata.get("webSearchResearch")

        if not isinstance(payload, dict) and not isinstance(research, dict):
            return None

        source = research if isinstance(research, dict) else payload
        evaluation = (payload or {}).get("sourceEvaluation") if isinstance(payload, dict) else {}
        query_security = (payload or {}).get("querySecurity") if isinstance(payload, dict) else {}

        if not query_security and isinstance(research, dict):
            query_security = research.get("querySecurity") or {}

        attempted = source.get("attemptedQueries") if isinstance(source, dict) else None

        return {
            "enabled": True,
            "reason": "user_requested_web_search",
            "queries": attempted if isinstance(attempted, list) else [],
            "provider": (payload or source or {}).get("provider"),
            "sourceCount": (source or {}).get("sourceCount"),
            "searchStatus": (source or {}).get("searchStatus"),
            "searchMode": (source or {}).get("searchMode"),
            "preferOfficial": (source or {}).get("preferOfficial"),
            "durationMs": (source or {}).get("durationMs"),
            "confidence": (
                (evaluation or {}).get("confidence")
                if isinstance(evaluation, dict)
                else (source or {}).get("confidence")
            ),
            "warnings": (
                (evaluation or {}).get("warnings")
                if isinstance(evaluation, dict)
                else (source or {}).get("warnings")
            )
            or [],
            "querySecurity": query_security if isinstance(query_security, dict) else None,
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
            audit_metadata["webSearchMetrics"] = snapshot

        return audit_metadata

    @classmethod
    def log_security_events_if_needed(
        cls,
        audit_repository: Any,
        *,
        user_id: Any,
        message: str,
    ) -> None:
        from app.domain.services.chat_web_search_intent_service import (
            ChatWebSearchIntentService,
        )
        from app.domain.services.chat_web_search_query_security_service import (
            ChatWebSearchQuerySecurityService,
        )

        if not ChatWebSearchIntentService.matches(message):
            return

        security = ChatWebSearchQuerySecurityService.sanitize(
            message,
            extracted_query=ChatWebSearchIntentService.extract_query(message),
        )
        metadata = cls.security_audit_metadata(message=message, security_result=security)

        if security.blocked:
            audit_repository.log(
                user_id=user_id,
                action="chat.web_search.blocked",
                metadata=metadata,
            )
            return

        if security.redacted:
            audit_repository.log(
                user_id=user_id,
                action="chat.web_search.query_redacted",
                metadata=metadata,
            )

    @classmethod
    def security_audit_metadata(
        cls,
        *,
        message: str,
        security_result: Any,
    ) -> dict[str, Any]:
        return {
            "messagePreview": str(message or "")[:240],
            "blocked": bool(getattr(security_result, "blocked", False)),
            "redacted": bool(getattr(security_result, "redacted", False)),
            "warnings": list(getattr(security_result, "warnings", ()) or ()),
        }

    @classmethod
    def feedback_audit_metadata(
        cls,
        *,
        message_id: str,
        reason: str,
        rating: int,
    ) -> dict[str, Any]:
        return {
            "messageId": message_id,
            "reason": reason,
            "rating": rating,
            "domain": "web_search",
        }

    @classmethod
    def aggregate(
        cls,
        *,
        entries: list[dict[str, Any]],
        blocked_events: list[dict[str, Any]] | None = None,
        redacted_events: list[dict[str, Any]] | None = None,
        feedback_events: list[dict[str, Any]] | None = None,
        follow_up_clicks: list[dict[str, Any]] | None = None,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        total = 0
        with_official = 0
        low_confidence = 0
        no_result = 0
        redacted_queries = 0
        synthesized = 0
        prefer_official = 0
        duration_total = 0
        duration_count = 0
        by_status: Counter[str] = Counter()
        by_mode: Counter[str] = Counter()
        by_confidence: Counter[str] = Counter()
        recent: list[dict[str, Any]] = []

        for entry in entries:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            total += 1
            status = str(snapshot.get("searchStatus") or "unknown")
            by_status[status] += 1

            if snapshot.get("hasOfficialSource"):
                with_official += 1

            confidence = str(snapshot.get("confidence") or "").strip()

            if confidence:
                by_confidence[confidence] += 1

            if confidence == "low":
                low_confidence += 1

            if status in {"no_results", "no_reliable_source", "empty"}:
                no_result += 1

            if snapshot.get("queryRedacted"):
                redacted_queries += 1

            if snapshot.get("synthesized"):
                synthesized += 1

            if snapshot.get("preferOfficial"):
                prefer_official += 1

            mode = str(snapshot.get("searchMode") or "").strip()

            if mode:
                by_mode[mode] += 1

            duration = snapshot.get("durationMs")

            if isinstance(duration, (int, float)) and duration > 0:
                duration_total += int(duration)
                duration_count += 1

            if len(recent) < 12:
                recent.append(
                    {
                        "loggedAt": entry.get("loggedAt"),
                        "searchStatus": status,
                        "sourceCount": snapshot.get("sourceCount"),
                        "confidence": snapshot.get("confidence"),
                        "hasOfficialSource": snapshot.get("hasOfficialSource"),
                    }
                )

        feedback_by_reason: Counter[str] = Counter()

        for item in feedback_events or []:
            snapshot = item.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            reason = str(snapshot.get("reason") or "unknown")
            feedback_by_reason[reason] += 1

        follow_up_labels: Counter[str] = Counter()
        allowed_labels = _web_follow_up_labels()

        for item in follow_up_clicks or []:
            snapshot = item.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            label = str(snapshot.get("label") or "").strip()

            if label and (label in allowed_labels or str(snapshot.get("group") or "") == "web_search"):
                follow_up_labels[label] += 1

        return {
            "windowHours": hours,
            "since": since_iso,
            "totalSearches": total,
            "officialSourceRate": (with_official / total) if total else 0.0,
            "withOfficialSourceCount": with_official,
            "lowConfidenceCount": low_confidence,
            "noResultCount": no_result,
            "redactedQueryCount": redacted_queries,
            "synthesizedCount": synthesized,
            "preferOfficialCount": prefer_official,
            "blockedBySecurityCount": len(blocked_events or []),
            "queryRedactedAuditCount": len(redacted_events or []),
            "averageDurationMs": (
                int(duration_total / duration_count) if duration_count else None
            ),
            "followUpClicksCount": sum(follow_up_labels.values()),
            "negativeFeedbackCount": sum(feedback_by_reason.values()),
            "byStatus": [
                {"status": key, "count": value}
                for key, value in by_status.most_common(8)
            ],
            "byMode": [{"mode": key, "count": value} for key, value in by_mode.most_common(4)],
            "byConfidence": [
                {"confidence": key, "count": value}
                for key, value in by_confidence.most_common(4)
            ],
            "feedbackByReason": [
                {"reason": key, "count": value}
                for key, value in feedback_by_reason.most_common(12)
            ],
            "followUpByLabel": [
                {"label": key, "count": value}
                for key, value in follow_up_labels.most_common(12)
            ],
            "recent": recent,
            "alerts": cls._build_alerts(
                total=total,
                no_result=no_result,
                low_confidence=low_confidence,
                with_official=with_official,
                blocked=len(blocked_events or []),
                negative_feedback=sum(feedback_by_reason.values()),
            ),
        }

    @classmethod
    def _build_alerts(
        cls,
        *,
        total: int,
        no_result: int,
        low_confidence: int,
        with_official: int,
        blocked: int,
        negative_feedback: int,
    ) -> list[str]:
        alerts: list[str] = []

        if total >= 5:
            if no_result / total >= 0.4:
                alerts.append(
                    "Muitas pesquisas sem resultado confiável na janela — revisar planejamento e provedor."
                )

            if with_official / total < 0.25:
                alerts.append(
                    "Taxa baixa de fonte oficial — priorizar site: do fabricante e chips «Só fontes oficiais»."
                )

            if low_confidence / total >= 0.35:
                alerts.append(
                    "Confiança baixa frequente — avaliar síntese e descarte de fontes fracas."
                )

        if blocked >= 3:
            alerts.append(
                "Várias consultas bloqueadas por dados sensíveis — revisar treinamento do usuário."
            )

        if negative_feedback >= 3:
            alerts.append(
                "Feedback negativo recorrente sobre pesquisa web — analisar motivos mais comuns."
            )

        return alerts
