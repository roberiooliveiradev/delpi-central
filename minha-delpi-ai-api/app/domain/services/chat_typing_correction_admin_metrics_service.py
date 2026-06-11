"""Agregação de métricas do corretor de digitação — Playbook 14 Fase 4."""

from __future__ import annotations

from collections import Counter
from typing import Any

_TYPING_CORRECTION_EVENTS = frozenset(
    {
        "typing_correction_offered",
        "typing_correction_accepted",
        "typing_correction_dismissed",
    }
)


class ChatTypingCorrectionAdminMetricsService:
    @classmethod
    def snapshot_from_request(
        cls,
        typing_correction: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(typing_correction, dict):
            return None

        if not typing_correction.get("accepted"):
            return None

        original = str(typing_correction.get("original") or "").strip()
        corrected = str(typing_correction.get("corrected") or "").strip()

        if not original or not corrected:
            return None

        changes = typing_correction.get("changes") or []

        return {
            "accepted": True,
            "original": original,
            "corrected": corrected,
            "changeCount": len(changes) if isinstance(changes, list) else 0,
            "source": typing_correction.get("source"),
        }

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        typing_correction: dict[str, Any] | None = None,
    ) -> dict:
        snapshot = cls.snapshot_from_request(typing_correction)

        if snapshot:
            audit_metadata["typingCorrectionMetrics"] = snapshot

        return audit_metadata

    @classmethod
    def snapshot_from_event(
        cls,
        *,
        event: str,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        token = str(event or "").strip()

        if token not in _TYPING_CORRECTION_EVENTS:
            return None

        safe_meta = metadata if isinstance(metadata, dict) else {}
        original = str(safe_meta.get("original") or "").strip()
        corrected = str(safe_meta.get("corrected") or "").strip()
        change_count = safe_meta.get("changeCount")

        return {
            "event": token,
            "original": original or None,
            "corrected": corrected or None,
            "changeCount": int(change_count) if isinstance(change_count, (int, float)) else None,
        }

    @classmethod
    def _correction_label(cls, snapshot: dict[str, Any]) -> str | None:
        original = str(snapshot.get("original") or "").strip()
        corrected = str(snapshot.get("corrected") or "").strip()

        if not original or not corrected:
            return None

        if original == corrected:
            return original

        return f"{original} → {corrected}"

    @classmethod
    def aggregate(
        cls,
        *,
        acceptance_entries: list[dict[str, Any]],
        event_entries: list[dict[str, Any]],
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        by_event: Counter[str] = Counter()
        by_correction: Counter[str] = Counter()
        recent_events: list[dict[str, Any]] = []
        recent_acceptances: list[dict[str, Any]] = []

        offered_count = 0
        accepted_event_count = 0
        dismissed_count = 0

        for entry in event_entries:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            event = str(snapshot.get("event") or "unknown")
            by_event[event] += 1

            if event == "typing_correction_offered":
                offered_count += 1
            elif event == "typing_correction_accepted":
                accepted_event_count += 1
            elif event == "typing_correction_dismissed":
                dismissed_count += 1

            label = cls._correction_label(snapshot)

            if label and event in {
                "typing_correction_offered",
                "typing_correction_accepted",
            }:
                by_correction[label] += 1

        for entry in event_entries[:12]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent_events.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "event": snapshot.get("event"),
                    "original": snapshot.get("original"),
                    "corrected": snapshot.get("corrected"),
                    "changeCount": snapshot.get("changeCount"),
                }
            )

        accepted_turns = 0
        changes_total = 0

        for entry in acceptance_entries:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            accepted_turns += 1
            changes_total += int(snapshot.get("changeCount") or 0)

            label = cls._correction_label(snapshot)

            if label:
                by_correction[label] += 1

        for entry in acceptance_entries[:10]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent_acceptances.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "original": snapshot.get("original"),
                    "corrected": snapshot.get("corrected"),
                    "changeCount": snapshot.get("changeCount"),
                    "source": snapshot.get("source"),
                }
            )

        acceptance_rate = round(accepted_event_count / offered_count, 4) if offered_count > 0 else 0.0
        dismiss_rate = round(dismissed_count / offered_count, 4) if offered_count > 0 else 0.0
        avg_changes = round(changes_total / accepted_turns, 2) if accepted_turns > 0 else 0.0

        top_corrections = [
            {"label": label, "count": count}
            for label, count in by_correction.most_common(12)
        ]

        alerts: list[str] = []

        if offered_count >= 20 and acceptance_rate < 0.15:
            alerts.append(
                "Taxa de aceite do corretor abaixo de 15% — revisar regras ou UX do chip."
            )

        if offered_count >= 20 and dismiss_rate > 0.6:
            alerts.append(
                "Mais de 60% das sugestões são dispensadas — possível ruído no catálogo."
            )

        if accepted_event_count > 0 and accepted_turns == 0:
            alerts.append(
                "Eventos de aceite sem typingCorrectionMetrics em turnos — verificar metadata no envio."
            )

        return {
            "windowHours": hours,
            "since": since_iso,
            "offeredCount": offered_count,
            "acceptedCount": accepted_event_count,
            "dismissedCount": dismissed_count,
            "acceptedTurnsCount": accepted_turns,
            "acceptanceRate": acceptance_rate,
            "dismissRate": dismiss_rate,
            "avgChangesPerAcceptance": avg_changes,
            "byEvent": dict(by_event),
            "topCorrections": top_corrections,
            "recentEvents": recent_events,
            "recentAcceptances": recent_acceptances,
            "alerts": alerts,
        }
