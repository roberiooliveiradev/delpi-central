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

_CHART_VIEW_FAMILY = frozenset(
    {
        "chart",
        "line_chart",
        "bar_chart",
        "horizontal_bar",
        "donut",
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

            preferred_format = None

            if isinstance(decision, dict):
                selected = str(decision.get("selected") or "").strip() or None
                raw_views = decision.get("availableViews") or []

                if isinstance(raw_views, list):
                    available_views = [
                        str(view).strip()
                        for view in raw_views
                        if str(view or "").strip()
                    ]

            for call in reversed(tool_calls):
                if not isinstance(call, dict):
                    continue

                call_metadata = call.get("metadata")

                if not isinstance(call_metadata, dict):
                    continue

                token = str(call_metadata.get("preferredFormat") or "").strip().lower()

                if token:
                    preferred_format = token
                    break

            if isinstance(presentation, dict) and presentation.get("type") == "chart":
                chart_type = str(presentation.get("chartType") or "").strip() or None

            return {
                "selected": selected,
                "preferredFormat": preferred_format,
                "presentationType": presentation_type,
                "chartType": chart_type,
                "availableViews": available_views,
                "formatRespected": cls._format_respected(
                    preferred=preferred_format,
                    selected=selected,
                    presentation_type=presentation_type,
                ),
            }

        return None

    @classmethod
    def _format_respected(
        cls,
        *,
        preferred: str | None,
        selected: str | None,
        presentation_type: str | None,
    ) -> bool | None:
        token = str(preferred or "").strip().lower()

        if not token or token == "auto":
            return None

        effective = str(selected or presentation_type or "").strip().lower()

        if not effective:
            return None

        if token == effective:
            return True

        if token in _CHART_VIEW_FAMILY and effective in _CHART_VIEW_FAMILY:
            return True

        if token == "chart" and effective in _CHART_VIEW_FAMILY:
            return True

        return False

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
        explicit_preference_turns = 0
        format_respected_turns = 0
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

            preferred = str(snapshot.get("preferredFormat") or "").strip().lower()

            if preferred and preferred not in {"auto", ""}:
                explicit_preference_turns += 1

                if snapshot.get("formatRespected") is True:
                    format_respected_turns += 1

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

        view_switch_count = by_event.get("presentation_view_switch", 0)
        axis_change_count = by_event.get("presentation_axis_change", 0)
        switch_to_table_count = by_view_target.get("table", 0)

        engagement_rate = (
            round(events_count / responses_with_rich, 4) if responses_with_rich else 0.0
        )
        view_switch_rate = (
            round(view_switch_count / responses_with_rich, 4) if responses_with_rich else 0.0
        )
        axis_change_rate = (
            round(axis_change_count / responses_with_rich, 4) if responses_with_rich else 0.0
        )
        switch_to_table_rate = (
            round(switch_to_table_count / view_switch_count, 4)
            if view_switch_count
            else 0.0
        )
        session_format_respected_ratio = (
            round(format_respected_turns / explicit_preference_turns, 4)
            if explicit_preference_turns
            else None
        )

        def _top(counter: Counter[str], limit: int = 8) -> list[dict[str, Any]]:
            return [
                {"label": label, "count": count}
                for label, count in counter.most_common(limit)
            ]

        top_selected = _top(by_selected, 10)
        top_events = _top(by_event, 10)

        alerts = cls._build_alerts(
            responses_with_rich=responses_with_rich,
            events_count=events_count,
            view_switch_count=view_switch_count,
            axis_change_count=axis_change_count,
            switch_to_table_count=switch_to_table_count,
            engagement_rate=engagement_rate,
            view_switch_rate=view_switch_rate,
            axis_change_rate=axis_change_rate,
            switch_to_table_rate=switch_to_table_rate,
        )

        return {
            "windowHours": hours,
            "since": since_iso,
            "responsesWithRichPresentation": responses_with_rich,
            "eventsCount": events_count,
            "viewSwitchCount": view_switch_count,
            "chartTypeSwitchCount": by_event.get("presentation_chart_type_switch", 0),
            "axisChangeCount": axis_change_count,
            "exportPngCount": by_event.get("presentation_chart_export_png", 0),
            "categoryFilterCount": by_event.get("presentation_category_filter", 0),
            "switchToTableCount": switch_to_table_count,
            "engagementRate": engagement_rate,
            "viewSwitchRate": view_switch_rate,
            "axisChangeRate": axis_change_rate,
            "switchToTableRate": switch_to_table_rate,
            "explicitPreferenceTurns": explicit_preference_turns,
            "formatRespectedTurns": format_respected_turns,
            "sessionFormatRespectedRatio": session_format_respected_ratio,
            "bySelected": dict(by_selected),
            "byPresentationType": dict(by_presentation_type),
            "byChartType": dict(by_chart_type),
            "byEvent": dict(by_event),
            "byViewTarget": dict(by_view_target),
            "byAxisColumn": dict(by_axis_column),
            "byFilterKey": dict(by_filter_key),
            "topSelected": top_selected,
            "topEvents": top_events,
            "topViewTargets": _top(by_view_target),
            "topAxisColumns": _top(by_axis_column),
            "topFilterKeys": _top(by_filter_key),
            "recentImpressions": recent_impressions,
            "recentEvents": recent_events,
            "alerts": alerts,
        }

    @classmethod
    def _build_alerts(
        cls,
        *,
        responses_with_rich: int,
        events_count: int,
        view_switch_count: int,
        axis_change_count: int,
        switch_to_table_count: int,
        engagement_rate: float,
        view_switch_rate: float,
        axis_change_rate: float,
        switch_to_table_rate: float,
    ) -> list[str]:
        alerts: list[str] = []

        if responses_with_rich == 0:
            alerts.append(
                "Nenhuma resposta com apresentação rica na janela — verificar auditoria "
                "(`presentationMetrics` em chat.message.sent/streamed)."
            )
            return alerts

        if responses_with_rich >= 5 and view_switch_rate >= 0.45:
            alerts.append(
                "Alta taxa de troca de formato (≥45% das respostas ricas) — revisar "
                "`ChatPresentationDecisionService` e recomendações automáticas."
            )

        if view_switch_count >= 3 and switch_to_table_rate >= 0.5:
            alerts.append(
                "Usuários mudam frequentemente para tabela após o formato inicial — "
                "priorizar tabela ou ajustar subtipo de gráfico (`ChatChartTypeSelectionService`)."
            )

        if responses_with_rich >= 5 and axis_change_rate >= 0.25:
            alerts.append(
                "Muitas alterações de eixo na janela — revisar "
                "`ChatPresentationAxisPreferenceService` (ex.: eficiência no eixo Y)."
            )

        if responses_with_rich >= 10 and engagement_rate < 0.05 and events_count == 0:
            alerts.append(
                "Respostas ricas sem eventos de UI na janela — confirmar telemetria "
                "`POST /chat/assistant/help-events` no MFE."
            )

        if events_count >= 8 and switch_to_table_count == 0 and view_switch_count >= 5:
            alerts.append(
                "Trocas de vista sem destino «tabela» — usuários alternam entre gráfico/texto; "
                "revisar toggles e chips de formato."
            )

        return alerts
