"""Agregação de métricas de interatividade para admin — Playbook 07 Fase 5."""

from __future__ import annotations

from collections import Counter
from typing import Any


class ChatInteractivityAdminMetricsService:
    @classmethod
    def snapshot_from_metadata(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        interactivity = metadata.get("interactivity")

        if not isinstance(interactivity, dict) or not interactivity.get("consolidated"):
            return None

        primary = interactivity.get("suggestions") or []
        more = interactivity.get("moreSuggestions") or {}
        shown = interactivity.get("suggestionsShown") or []

        overflow_count = sum(
            len(items) for items in more.values() if isinstance(items, list)
        )

        return {
            "primaryCount": len(primary) if isinstance(primary, list) else 0,
            "overflowCount": overflow_count,
            "shownCount": len(shown) if isinstance(shown, list) else 0,
            "hasMoreOptions": overflow_count > 0,
            "sourceIntent": interactivity.get("sourceIntent"),
            "primaryLabels": [
                str(item.get("label") or "").strip()
                for item in primary
                if isinstance(item, dict) and item.get("label")
            ],
            "shownLabels": [str(label).strip() for label in shown if str(label).strip()],
        }

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        assistant_metadata: dict[str, Any] | None = None,
    ) -> dict:
        snapshot = cls.snapshot_from_metadata(assistant_metadata)

        if snapshot and snapshot.get("shownCount", 0) > 0:
            audit_metadata["interactivityMetrics"] = snapshot

        return audit_metadata

    @classmethod
    def snapshot_from_click(cls, metadata: dict[str, Any] | None) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        label = str(metadata.get("label") or "").strip()

        if not label:
            return None

        return {
            "label": label,
            "group": metadata.get("group"),
            "sessionId": metadata.get("sessionId") or metadata.get("session_id"),
        }

    @classmethod
    def aggregate(
        cls,
        *,
        impression_entries: list[dict[str, Any]],
        click_entries: list[dict[str, Any]],
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        responses_with_chips = 0
        more_options_count = 0
        shown_total = 0
        by_label_shown: Counter[str] = Counter()
        by_intent: Counter[str] = Counter()
        by_group_clicked: Counter[str] = Counter()
        by_label_clicked: Counter[str] = Counter()
        recent_impressions: list[dict[str, Any]] = []
        recent_clicks: list[dict[str, Any]] = []

        for entry in impression_entries:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            responses_with_chips += 1
            shown_total += int(snapshot.get("shownCount") or 0)

            if snapshot.get("hasMoreOptions"):
                more_options_count += 1

            intent = str(snapshot.get("sourceIntent") or "unknown")
            by_intent[intent] += 1

            for label in snapshot.get("shownLabels") or []:
                token = str(label).strip()

                if token:
                    by_label_shown[token] += 1

        for entry in impression_entries[:10]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent_impressions.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "action": entry.get("action"),
                    "primaryCount": snapshot.get("primaryCount"),
                    "overflowCount": snapshot.get("overflowCount"),
                    "sourceIntent": snapshot.get("sourceIntent"),
                    "primaryLabels": snapshot.get("primaryLabels"),
                }
            )

        click_count = 0

        for entry in click_entries:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            click_count += 1
            label = str(snapshot.get("label") or "unknown")
            by_label_clicked[label] += 1
            group = str(snapshot.get("group") or "unknown")
            by_group_clicked[group] += 1

        for entry in click_entries[:12]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent_clicks.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "label": snapshot.get("label"),
                    "group": snapshot.get("group"),
                }
            )

        ctr_by_label: dict[str, float] = {}

        for label, shown in by_label_shown.items():
            clicks = by_label_clicked.get(label, 0)

            if shown > 0:
                ctr_by_label[label] = round(clicks / shown, 4)

        overall_ctr = round(click_count / shown_total, 4) if shown_total > 0 else 0.0

        top_clicked = [
            {"label": label, "count": count}
            for label, count in by_label_clicked.most_common(12)
        ]

        top_shown = [
            {"label": label, "count": count}
            for label, count in by_label_shown.most_common(12)
        ]

        return {
            "windowHours": hours,
            "since": since_iso,
            "responsesWithChips": responses_with_chips,
            "clicksCount": click_count,
            "suggestionsShownTotal": shown_total,
            "moreOptionsResponses": more_options_count,
            "clickThroughRate": overall_ctr,
            "byIntent": dict(by_intent),
            "byLabelShown": dict(by_label_shown),
            "byLabelClicked": dict(by_label_clicked),
            "byGroupClicked": dict(by_group_clicked),
            "ctrByLabel": ctr_by_label,
            "topShown": top_shown,
            "topClicked": top_clicked,
            "recentImpressions": recent_impressions,
            "recentClicks": recent_clicks,
        }
