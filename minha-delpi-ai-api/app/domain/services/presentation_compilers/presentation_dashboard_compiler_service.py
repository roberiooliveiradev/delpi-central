"""Compila spec.dashboard.panels → dashboardPresentation usando slots existentes."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_spec import PresentationSpec


class PresentationDashboardCompilerService:
    _SLOT_BY_PRESENTATION = {
        "kpi": "kpiPresentation",
        "chart": "chartPresentation",
        "table": "tablePresentation",
    }

    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
    ) -> None:
        if spec.dashboard is None or not spec.dashboard.panels:
            return

        available = cls._available_presentations(metadata)
        if not available:
            decision = metadata.setdefault("presentationDecision", {})
            if isinstance(decision, dict):
                decision["unmetIntent"] = "dashboard_not_materializable"
            return

        panels: list[dict[str, Any]] = []
        for panel_spec in spec.dashboard.panels:
            presentation_type = panel_spec.presentation
            source = available.get(presentation_type)
            if source is None:
                continue

            panel_payload = cls._build_panel(
                panel_spec,
                presentation=source,
                presentation_type=presentation_type,
            )
            if panel_payload:
                panels.append(panel_payload)

        if not panels:
            decision = metadata.setdefault("presentationDecision", {})
            if isinstance(decision, dict):
                decision["unmetIntent"] = "dashboard_not_materializable"
            return

        dashboard = metadata.get("dashboardPresentation")
        if not isinstance(dashboard, dict) and isinstance(metadata.get("presentation"), dict):
            if metadata["presentation"].get("type") == "dashboard":
                dashboard = metadata["presentation"]

        title = (
            (isinstance(dashboard, dict) and str(dashboard.get("title") or "").strip())
            or "Dashboard"
        )
        payload: dict[str, Any] = {
            "type": "dashboard",
            "title": title,
            "panels": panels,
        }
        config = dict((dashboard or {}).get("config") or {})
        config["bindingProvenance"] = "COMPILED"
        config["panelOrder"] = [panel["id"] for panel in panels]
        payload["config"] = config

        metadata["dashboardPresentation"] = payload
        decision = metadata.setdefault("presentationDecision", {})
        if isinstance(decision, dict):
            decision["selected"] = "dashboard"

        if metadata.get("presentation") is dashboard or (
            isinstance(metadata.get("presentation"), dict)
            and metadata["presentation"].get("type") == "dashboard"
        ):
            metadata["presentation"] = payload

    @classmethod
    def _available_presentations(
        cls,
        metadata: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        available: dict[str, dict[str, Any]] = {}
        for presentation_type, slot_key in cls._SLOT_BY_PRESENTATION.items():
            slot = metadata.get(slot_key)
            if isinstance(slot, dict) and slot.get("type") == presentation_type:
                available[presentation_type] = slot
                continue
            primary = metadata.get("presentation")
            if (
                isinstance(primary, dict)
                and primary.get("type") == presentation_type
            ):
                available[presentation_type] = primary
        return available

    @classmethod
    def _build_panel(
        cls,
        panel_spec,
        *,
        presentation: dict[str, Any],
        presentation_type: str,
    ) -> dict[str, Any] | None:
        nested = dict(presentation)
        if panel_spec.fields and presentation_type == "table":
            columns = nested.get("columns")
            if isinstance(columns, list):
                allowed = set(panel_spec.fields)
                nested["columns"] = [
                    column
                    for column in columns
                    if isinstance(column, dict)
                    and str(column.get("key") or "").strip() in allowed
                ]
        if panel_spec.measures and presentation_type == "kpi":
            cards = nested.get("cards")
            if isinstance(cards, list):
                allowed = set(panel_spec.measures)
                nested["cards"] = [
                    card
                    for card in cards
                    if isinstance(card, dict)
                    and str(card.get("key") or card.get("id") or "").strip() in allowed
                ]

        if presentation_type == "table" and not nested.get("columns"):
            return None
        if presentation_type == "kpi" and not nested.get("cards"):
            return None
        if presentation_type == "chart" and not nested.get("data"):
            return None

        panel: dict[str, Any] = {
            "id": panel_spec.id,
            "title": panel_spec.role or panel_spec.id.replace("_", " ").title(),
            "presentation": nested,
        }
        if panel_spec.role:
            panel["role"] = panel_spec.role
        return panel
