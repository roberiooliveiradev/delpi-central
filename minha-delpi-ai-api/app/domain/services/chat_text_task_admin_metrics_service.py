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
            "intent": metrics.get("intent"),
            "tone": metrics.get("tone"),
            "audience": metrics.get("audience"),
            "deliverFinalOnly": bool(metrics.get("deliverFinalOnly")),
            "source": metrics.get("source"),
            "containsTechnicalTerms": bool(metrics.get("containsTechnicalTerms")),
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
        by_intent: Counter[str] = Counter()
        by_audience: Counter[str] = Counter()
        by_family: Counter[str] = Counter()
        mixed_count = 0
        quality_failed = 0
        canvas_updates = 0
        deliver_final_only_count = 0
        technical_term_count = 0
        attachment_source_count = 0
        recent: list[dict[str, Any]] = []

        for entry in entries:
            snapshot = entry.get("snapshot") if isinstance(entry.get("snapshot"), dict) else entry

            if not isinstance(snapshot, dict):
                continue

            subtype = str(snapshot.get("subtype") or "unknown")
            by_subtype[subtype] += 1
            task_type = str(snapshot.get("type") or "unknown")
            by_type[task_type] += 1
            intent = str(snapshot.get("intent") or "unknown")
            by_intent[intent] += 1
            by_family[cls._family_from_intent(intent)] += 1
            audience = snapshot.get("audience")

            if audience:
                by_audience[str(audience)] += 1

            tone = str(snapshot.get("tone") or "")

            if tone == "formal":
                by_family["tone_formal"] += 1

            if snapshot.get("deliverFinalOnly"):
                by_family["deliver_final_only"] += 1

            if int(snapshot.get("canvasVersionCount") or 0) > 0:
                by_family["canvas_used"] += 1

            if snapshot.get("deliverFinalOnly"):
                deliver_final_only_count += 1

            if snapshot.get("containsTechnicalTerms"):
                technical_term_count += 1

            if str(snapshot.get("source") or "") == "attachment":
                attachment_source_count += 1

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
                    "intent": snapshot.get("intent"),
                    "audience": snapshot.get("audience"),
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
            "deliverFinalOnlyCount": deliver_final_only_count,
            "technicalTermCount": technical_term_count,
            "attachmentSourceCount": attachment_source_count,
            "bySubtype": dict(by_subtype),
            "byType": dict(by_type),
            "byIntent": dict(by_intent),
            "byAudience": dict(by_audience),
            "byFamily": dict(by_family),
            "recent": recent,
        }

    @staticmethod
    def _family_from_intent(intent: str) -> str:
        token = (intent or "").strip().lower()

        if token.startswith("text.email"):
            return "emails"

        if token.startswith("text.letter"):
            return "letters"

        if "minutes" in token or token == "text.conversation.transform":
            return "minutes"

        if "announcement" in token or "memorandum" in token:
            return "announcements"

        if "report" in token:
            return "reports"

        if "documentation" in token:
            return "documentation"

        if token.startswith("text.translate"):
            return "translations"

        if token.startswith("text.summarize"):
            return "summaries"

        if token == "text.eli5":
            return "eli5"

        if token.startswith("text.correct") or token.startswith("text.review"):
            return "corrections"

        if token.startswith("text.rewrite") or token.startswith("text.formalize"):
            return "rewrites"

        if "checklist" in token or "table" in token:
            return "structured"

        return "other"
