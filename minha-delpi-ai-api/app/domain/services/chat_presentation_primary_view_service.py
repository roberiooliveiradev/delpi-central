"""Alinha visão primária ao formato explícito de sessão (Fase 1 — preferência UI)."""

from __future__ import annotations

from typing import Any

from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)

_EXPLICIT_SESSION_FORMATS = frozenset({"text", "table", "tree", "chart"})
_VIEW_SLOT_BY_TYPE = {
    "table": "tablePresentation",
    "tree": "treePresentation",
    "chart": "chartPresentation",
}
_CHART_SELECTED_TYPES = frozenset(
    {"chart", "line_chart", "bar_chart", "horizontal_bar", "donut", "area_chart"}
)


class ChatPresentationPrimaryViewService:
    @classmethod
    def apply_session_preference(
        cls,
        metadata: dict[str, Any],
        session_format: str | None,
        *,
        data: Any = None,
        path: str = "",
        presenter: ExternalActionResultPresenter | None = None,
    ) -> bool:
        token = str(session_format or "").strip().lower()

        if token not in _EXPLICIT_SESSION_FORMATS:
            return False

        metadata["preferredFormat"] = token
        metadata["explicitSessionFormat"] = token

        if token == "text":
            cls._apply_text_primary(metadata)
        elif token == "table":
            cls._apply_table_primary(metadata, data=data, path=path, presenter=presenter)
        elif token == "tree":
            cls._apply_tree_primary(metadata, data=data, path=path, presenter=presenter)
        elif token == "chart":
            cls._apply_chart_primary(metadata, data=data, path=path, presenter=presenter)

        return True

    @classmethod
    def finalize_decision_alignment(
        cls,
        metadata: dict[str, Any],
        *,
        kpi_presentation: dict[str, Any] | None = None,
    ) -> None:
        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            return

        selected = str(decision.get("selected") or "").strip().lower()
        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if selected == "kpi" and isinstance(kpi_presentation, dict):
            metadata["presentation"] = kpi_presentation
            text_presentation = metadata.get("textPresentation")

            if isinstance(text_presentation, dict):
                title = str(
                    text_presentation.get("title")
                    or kpi_presentation.get("title")
                    or ""
                ).strip()
                text_presentation["markdown"] = f"### {title}".strip() if title else ""

            return

        if selected == "text":
            presentation = metadata.get("presentation")

            if isinstance(presentation, dict) and presentation.get("type") == "kpi":
                metadata["kpiPresentation"] = presentation
                metadata["presentation"] = None

            if explicit == "text":
                decision["layoutMode"] = "single"
                decision["visualOrder"] = ["text"]

            return

        if explicit in _EXPLICIT_SESSION_FORMATS and selected:
            cls._align_primary_to_selected(metadata, selected)
            decision["layoutMode"] = "single"
            decision["visualOrder"] = [selected]

    @classmethod
    def _apply_text_primary(cls, metadata: dict[str, Any]) -> None:
        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            presentation_type = cls._presentation_type(presentation)

            if presentation_type == "kpi":
                metadata["kpiPresentation"] = presentation
            elif presentation_type in _VIEW_SLOT_BY_TYPE:
                slot = _VIEW_SLOT_BY_TYPE[presentation_type]

                if not metadata.get(slot):
                    metadata[slot] = presentation

            if presentation_type != "text":
                metadata["presentation"] = None

    @classmethod
    def _apply_table_primary(
        cls,
        metadata: dict[str, Any],
        *,
        data: Any,
        path: str,
        presenter: ExternalActionResultPresenter | None,
    ) -> None:
        if cls._promote_view(metadata, "table"):
            return

        if presenter and data is not None:
            forced = presenter.build_presentation(data, path=path)

            if forced and cls._presentation_type(forced) == "table":
                cls._set_primary(metadata, forced)

    @classmethod
    def _apply_tree_primary(
        cls,
        metadata: dict[str, Any],
        *,
        data: Any,
        path: str,
        presenter: ExternalActionResultPresenter | None,
    ) -> None:
        if cls._promote_view(metadata, "tree"):
            return

        if presenter and data is not None:
            forced = presenter.build_tree_presentation(data, path=path)

            if forced and cls._presentation_type(forced) == "tree":
                cls._set_primary(metadata, forced)

    @classmethod
    def _apply_chart_primary(
        cls,
        metadata: dict[str, Any],
        *,
        data: Any,
        path: str,
        presenter: ExternalActionResultPresenter | None,
    ) -> None:
        if cls._promote_view(metadata, "chart"):
            return

        if presenter and data is not None:
            forced = presenter.build_chart_presentation(data, path=path, force=True)

            if forced and cls._presentation_type(forced) == "chart":
                cls._set_primary(metadata, forced)

    @classmethod
    def _align_primary_to_selected(cls, metadata: dict[str, Any], selected: str) -> None:
        if selected in _CHART_SELECTED_TYPES:
            cls._promote_view(metadata, "chart")
            return

        if selected in _VIEW_SLOT_BY_TYPE:
            cls._promote_view(metadata, selected)

    @classmethod
    def _promote_view(cls, metadata: dict[str, Any], view_type: str) -> bool:
        view, source_key = cls._find_view(metadata, view_type)

        if not isinstance(view, dict):
            return False

        primary = metadata.get("presentation")

        if source_key != "presentation" and isinstance(primary, dict):
            primary_type = cls._presentation_type(primary)

            if primary_type and primary_type != view_type:
                slot = _VIEW_SLOT_BY_TYPE.get(primary_type)

                if slot and not metadata.get(slot):
                    metadata[slot] = primary

        metadata["presentation"] = view

        if source_key != "presentation":
            metadata[source_key] = None

        return True

    @classmethod
    def _set_primary(cls, metadata: dict[str, Any], presentation: dict[str, Any]) -> None:
        primary = metadata.get("presentation")
        view_type = cls._presentation_type(presentation)

        if isinstance(primary, dict) and cls._presentation_type(primary) != view_type:
            slot = _VIEW_SLOT_BY_TYPE.get(cls._presentation_type(primary))

            if slot and not metadata.get(slot):
                metadata[slot] = primary

        metadata["presentation"] = presentation

        slot = _VIEW_SLOT_BY_TYPE.get(view_type)

        if slot and metadata.get(slot) is presentation:
            metadata[slot] = None

    @classmethod
    def _find_view(
        cls,
        metadata: dict[str, Any],
        view_type: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        primary = metadata.get("presentation")

        if isinstance(primary, dict) and cls._presentation_type(primary) == view_type:
            return primary, "presentation"

        slot_key = _VIEW_SLOT_BY_TYPE.get(view_type)

        if not slot_key:
            return None, None

        secondary = metadata.get(slot_key)

        if isinstance(secondary, dict) and cls._presentation_type(secondary) == view_type:
            return secondary, slot_key

        return None, None

    @staticmethod
    def _presentation_type(presentation: dict[str, Any] | None) -> str:
        if not isinstance(presentation, dict):
            return ""

        return str(presentation.get("type") or "").strip().lower()
