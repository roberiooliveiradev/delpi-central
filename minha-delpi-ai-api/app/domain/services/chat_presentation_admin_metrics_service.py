"""Agregação de métricas de apresentação rica — Playbook 09 Fase 6."""

from __future__ import annotations

from collections import Counter
from typing import Any

_PRESENTATION_EVENTS = frozenset(
    {
        "presentation_view_switch",
        "presentation_chart_type_switch",
        "presentation_axis_change",
        "presentation_chart_export_png",
        "presentation_category_filter",
    }
)


class ChatPresentationAdminMetricsService:
    @classmethod
    def snapshot_from_assistant_metadata(
        cls,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not isinstance(metadata, dict):
            return None

        tool_calls = metadata.get("toolCalls") or metadata.get("tool_calls") or []

        if not isinstance(tool_calls, list):
            return None

        for call in reversed(tool_calls):
            if not isinstance(call, dict):
                continue

            call_metadata = call.get("metadata")

            if not isinstance(call_metadata, dict) or not call_metadata.get("ok"):
                continue

            presentation = call_metadata.get("presentation")
            decision = call_metadata.get("presentationDecision")
            presentation_type = None

            if isinstance(presentation, dict):
                presentation_type = str(presentation.get("type") or "").strip() or None

            if not isinstance(decision, dict) and not presentation_type:
                continue

            selected = None
            available_views: list[str] = []
            chart_type = None

            if isinstance(decision, dict):
                selected = str(decision.get("selected") or "").strip() or None
                raw_views = decision.get("availableViews") or []

                if isinstance(raw_views, list):
                    available_views = [
                        str(view).strip()
                        for view in raw_views
                        if str(view or "").strip()
                    ]

            if isinstance(presentation, dict) and presentation.get("type") == "chart":
                chart_type = str(presentation.get("chartType") or "").strip() or None

            return {
                "selected": selected,
                "presentationType": presentation_type,
                "chartType": chart_type,
                "availableViews": available_views,
            }

        return None

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        assistant_metadata: dict[str, Any] | None = None,
    ) -> dict:
        snapshot = cls.snapshot_from_assistant_metadata(assistant_metadata)

        if snapshot and (snapshot.get("selected") or snapshot.get("presentationType")):
            audit_metadata["presentationMetrics"] = snapshot

        return audit_metadata

    @classmethod
    def snapshot_from_event(
        cls,
        *,
        event: str,
        metadata: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        token = str(event or "").strip()

        if token not in _PRESENTATION_EVENTS:
            return None

        safe_meta = metadata if isinstance(metadata, dict) else {}

        return {
            "event": token,
            "from": safe_meta.get("from"),
            "to": safe_meta.get("to"),
            "axis": safe_meta.get("axis"),
            "column": safe_meta.get("column"),
            "chartType": safe_meta.get("chartType"),
            "filterKey": safe_meta.get("filterKey"),
            "filterValue": safe_meta.get("filterValue"),
        }

    @classmethod
    def aggregate(
        cls,
        *,
        impression_entries: list[dict[str, Any]],
        event_entries: list[dict[str, Any]],
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        responses_with_rich = 0
        by_selected: Counter[str] = Counter()
        by_presentation_type: Counter[str] = Counter()
        by_chart_type: Counter[str] = Counter()
        by_event: Counter[str] = Counter()
        by_view_target: Counter[str] = Counter()
        by_axis_column: Counter[str] = Counter()
        by_filter_key: Counter[str] = Counter()
        recent_impressions: list[dict[str, Any]] = []
        recent_events: list[dict[str, Any]] = []

        for entry in impression_entries:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            responses_with_rich += 1
            selected = str(snapshot.get("selected") or "unknown")
            by_selected[selected] += 1

            presentation_type = str(snapshot.get("presentationType") or "unknown")
            by_presentation_type[presentation_type] += 1

            chart_type = snapshot.get("chartType")

            if chart_type:
                by_chart_type[str(chart_type)] += 1

        for entry in impression_entries[:10]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent_impressions.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "selected": snapshot.get("selected"),
                    "presentationType": snapshot.get("presentationType"),
                    "chartType": snapshot.get("chartType"),
                }
            )

        events_count = 0

        for entry in event_entries:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            events_count += 1
            event_name = str(snapshot.get("event") or "unknown")
            by_event[event_name] += 1

            target = snapshot.get("to")

            if event_name == "presentation_view_switch" and target:
                by_view_target[str(target)] += 1

            column = snapshot.get("column")

            if event_name == "presentation_axis_change" and column:
                by_axis_column[str(column)] += 1

            filter_key = snapshot.get("filterKey")

            if event_name == "presentation_category_filter" and filter_key:
                by_filter_key[str(filter_key)] += 1

        for entry in event_entries[:15]:
            snapshot = entry.get("snapshot")

            if not isinstance(snapshot, dict):
                continue

            recent_events.append(
                {
                    "loggedAt": entry.get("loggedAt"),
                    "event": snapshot.get("event"),
                    "from": snapshot.get("from"),
                    "to": snapshot.get("to"),
                    "column": snapshot.get("column"),
                    "filterKey": snapshot.get("filterKey"),
                    "filterValue": snapshot.get("filterValue"),
                }
            )

        top_selected = [
            {"label": label, "count": count}
            for label, count in by_selected.most_common(10)
        ]
        top_events = [
            {"label": label, "count": count}
            for label, count in by_event.most_common(10)
        ]

        return {
            "windowHours": hours,
            "since": since_iso,
            "responsesWithRichPresentation": responses_with_rich,
            "eventsCount": events_count,
            "viewSwitchCount": by_event.get("presentation_view_switch", 0),
            "chartTypeSwitchCount": by_event.get("presentation_chart_type_switch", 0),
            "axisChangeCount": by_event.get("presentation_axis_change", 0),
            "exportPngCount": by_event.get("presentation_chart_export_png", 0),
            "categoryFilterCount": by_event.get("presentation_category_filter", 0),
            "bySelected": dict(by_selected),
            "byPresentationType": dict(by_presentation_type),
            "byChartType": dict(by_chart_type),
            "byEvent": dict(by_event),
            "byViewTarget": dict(by_view_target),
            "byAxisColumn": dict(by_axis_column),
            "byFilterKey": dict(by_filter_key),
            "topSelected": top_selected,
            "topEvents": top_events,
            "recentImpressions": recent_impressions,
            "recentEvents": recent_events,
        }
