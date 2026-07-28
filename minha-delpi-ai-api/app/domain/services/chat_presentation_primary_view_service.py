"""Alinha visão primária ao formato explícito de sessão (Fase 1 — preferência UI)."""

from __future__ import annotations

from typing import Any

from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)

_EXPLICIT_SESSION_FORMATS = frozenset({"text", "table", "tree", "chart", "canvas", "dashboard"})
_EXPLICIT_NATIVE_SINGLE = frozenset({"table", "tree", "chart", "dashboard", "kpi"})
_VIEW_SLOT_BY_TYPE = {
    "table": "tablePresentation",
    "tree": "treePresentation",
    "chart": "chartPresentation",
    "kpi": "kpiPresentation",
    "dashboard": "dashboardPresentation",
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
        elif token == "dashboard":
            cls._apply_dashboard_primary(metadata)
        elif token == "canvas":
            pass

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
                from app.domain.services.chat_rich_presentation_text_service import (
                    ChatRichPresentationTextService,
                )

                if not ChatRichPresentationTextService._uses_humanized_stack_sections(metadata):
                    title = str(
                        text_presentation.get("title")
                        or kpi_presentation.get("title")
                        or ""
                    ).strip()
                    text_presentation["markdown"] = f"### {title}".strip() if title else ""

            return

        native_selected = selected in _VIEW_SLOT_BY_TYPE or selected in _CHART_SELECTED_TYPES

        if selected == "text" or (explicit == "text" and not native_selected):
            presentation = metadata.get("presentation")

            if isinstance(presentation, dict) and presentation.get("type") == "kpi":
                metadata["kpiPresentation"] = presentation
                metadata["presentation"] = None

            return

        if native_selected and explicit == "text":
            preferred = str(metadata.get("preferredFormat") or "").strip().lower()

            if preferred == selected and preferred not in {"", "text", "topics"}:
                metadata["explicitSessionFormat"] = selected
                metadata["preferredFormat"] = selected

            return

        if explicit == "canvas":
            decision["selected"] = "canvas"
            decision["layoutMode"] = "single"
            decision["visualOrder"] = ["canvas", "text"]
            return

        preferred = str(metadata.get("preferredFormat") or "").strip().lower()
        force_single = explicit in _EXPLICIT_SESSION_FORMATS or (
            preferred in _EXPLICIT_SESSION_FORMATS
            and preferred == selected
            and selected not in {"", "text"}
        )

        if force_single and selected:
            cls._align_primary_to_selected(metadata, selected)
            decision["layoutMode"] = "single"
            decision["visualOrder"] = [selected]

    @classmethod
    def finalize_explicit_native_single_view(cls, metadata: dict[str, Any]) -> None:
        """Pós-pipeline: promove visão explícita (Painel/Tabela/…) sem remover demais formatos."""
        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if explicit not in _EXPLICIT_NATIVE_SINGLE:
            return

        cls._promote_view(metadata, explicit)

        from app.domain.services.chat_presentation_text_mode_service import (
            ChatPresentationTextModeService,
        )

        ChatPresentationTextModeService.align_explicit_session_decision(metadata)

    @classmethod
    def sync_render_contract_for_explicit_session(cls, metadata: dict[str, Any]) -> None:
        """Playbook 13 P6 — alinha decisão/renderPlan antes do prune para cada modo de sessão."""
        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        if not explicit:
            return

        if explicit in {"text", "topics"}:
            cls._sync_explicit_text_session(metadata)
            return

        if explicit == "canvas":
            cls._sync_explicit_canvas_session(metadata)
            return

        if explicit in _EXPLICIT_NATIVE_SINGLE:
            cls._sync_explicit_native_single_session(metadata)

    @classmethod
    def sync_render_contract_for_explicit_native_view(cls, metadata: dict[str, Any]) -> None:
        """Compat — delega para sync_render_contract_for_explicit_session."""
        cls.sync_render_contract_for_explicit_session(metadata)

    @classmethod
    def _sync_explicit_native_single_session(cls, metadata: dict[str, Any]) -> None:
        from app.domain.services.chat_presentation_vocabulary_service import (
            ChatPresentationVocabularyService,
        )

        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            return

        # Tenta montar/promover o slot pedido antes de decidir se é realizável.
        cls.finalize_explicit_native_single_view(metadata)

        selected = explicit

        if not cls.view_is_realizable(metadata, explicit):
            selected = cls._resolve_realizable_fallback(metadata, decision, preferred=explicit)
            decision["reason"] = ChatPresentationVocabularyService.decision_reason(
                "formatUnavailableFallback",
            )
            # Preferência de sessão permanece em explicitSessionFormat para o próximo turno apto.

        decision["selected"] = selected
        decision["layoutMode"] = "single"
        decision["visualOrder"] = [selected]

        if selected in _EXPLICIT_NATIVE_SINGLE:
            cls._align_primary_to_selected(metadata, selected)

    @classmethod
    def view_is_realizable(cls, metadata: dict[str, Any], view_type: str) -> bool:
        token = str(view_type or "").strip().lower()

        if token in {"text", "topics", "canvas"}:
            return True

        if token in _CHART_SELECTED_TYPES:
            token = "chart"

        view, _ = cls._find_view(metadata, token)

        if not isinstance(view, dict):
            # chart/table ainda podem estar só no slot auxiliar após promote parcial
            if token == "chart":
                view = metadata.get("chartPresentation")
            elif token == "table":
                view = metadata.get("tablePresentation")
                if not isinstance(view, dict):
                    view = cls._find_table_in_presentations(metadata)
            elif token == "tree":
                view = metadata.get("treePresentation")
            elif token == "kpi":
                view = metadata.get("kpiPresentation")
            elif token == "dashboard":
                view = metadata.get("dashboardPresentation")

        if not isinstance(view, dict):
            return False

        if token == "tree":
            return isinstance(view.get("root"), dict)

        if token == "table":
            return isinstance(view.get("rows"), list)

        if token == "chart":
            data = view.get("data")
            return isinstance(data, list) and len(data) > 0

        if token == "kpi":
            cards = view.get("cards")
            return isinstance(cards, list) and len(cards) > 0

        if token == "dashboard":
            panels = view.get("panels")
            return isinstance(panels, list) and len(panels) > 0

        return cls._presentation_type(view) == token

    @classmethod
    def _resolve_realizable_fallback(
        cls,
        metadata: dict[str, Any],
        decision: dict[str, Any],
        *,
        preferred: str,
    ) -> str:
        fallback = str(decision.get("fallback") or "").strip().lower()
        candidates: list[str] = []

        if fallback and fallback != preferred:
            candidates.append(fallback)

        for view in decision.get("availableViews") or []:
            token = str(view or "").strip().lower()

            if token and token != preferred and token not in candidates:
                candidates.append(token)

        for token in ("table", "tree", "kpi", "chart", "text"):
            if token != preferred and token not in candidates:
                candidates.append(token)

        for candidate in candidates:
            if candidate in {"text", "topics"}:
                return "text"

            if candidate == "canvas":
                continue

            if cls.view_is_realizable(metadata, candidate):
                return candidate

        return "text"

    @classmethod
    def _sync_explicit_text_session(cls, metadata: dict[str, Any]) -> None:
        from app.domain.services.chat_presentation_text_mode_service import (
            ChatPresentationTextModeService,
        )

        ChatPresentationTextModeService.align_explicit_session_decision(metadata)

    @classmethod
    def _sync_explicit_canvas_session(cls, metadata: dict[str, Any]) -> None:
        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            return

        decision["selected"] = "canvas"
        decision["layoutMode"] = "single"
        decision["visualOrder"] = ["canvas", "text"]

    @classmethod
    def relocate_primary_to_text_auxiliary_slots(cls, metadata: dict[str, Any]) -> None:
        """Move visão primária para slots auxiliares sem marcar preferência explícita da sessão."""
        cls._apply_text_primary(metadata)

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
            bundle_table = cls._schema_bundle_view(presenter, data, path=path).table

            if bundle_table and cls._presentation_type(bundle_table) == "table":
                cls._set_primary(metadata, bundle_table)
                return

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
                return

            bundle_tree = cls._schema_bundle_view(presenter, data, path=path).tree

            if bundle_tree and cls._presentation_type(bundle_tree) == "tree":
                cls._set_primary(metadata, bundle_tree)

    @classmethod
    def _apply_dashboard_primary(cls, metadata: dict[str, Any]) -> None:
        if cls._promote_view(metadata, "dashboard"):
            return

        dashboard = metadata.get("dashboardPresentation")

        if isinstance(dashboard, dict) and cls._presentation_type(dashboard) == "dashboard":
            cls._set_primary(metadata, dashboard)

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

        if view_type == "table":
            from_table_presentations = cls._find_table_in_presentations(metadata)

            if from_table_presentations is not None:
                return from_table_presentations, "tablePresentations"

        return None, None

    @classmethod
    def _find_table_in_presentations(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        bulk = metadata.get("tablePresentations")

        if not isinstance(bulk, list):
            return None

        for candidate in bulk:
            if not isinstance(candidate, dict) or candidate.get("type") != "table":
                continue

            if candidate.get("role") == "list" and candidate.get("rows"):
                return candidate

        for candidate in bulk:
            if isinstance(candidate, dict) and candidate.get("type") == "table" and candidate.get("rows"):
                return candidate

        return None

    @classmethod
    def _schema_bundle_view(
        cls,
        presenter: ExternalActionResultPresenter,
        data: Any,
        *,
        path: str,
    ):
        from app.domain.services.chat_operational_response_profile_service import (
            ChatOperationalResponseProfileService,
        )
        from app.domain.services.chat_schema_driven_presentation_service import (
            ChatSchemaDrivenPresentationService,
        )

        profile = ChatOperationalResponseProfileService.resolve(data, path=path)

        return ChatSchemaDrivenPresentationService.build_bundle(
            presenter,
            data,
            path=path,
            entity=profile.entity,
        )

    @staticmethod
    def _presentation_type(presentation: dict[str, Any] | None) -> str:
        if not isinstance(presentation, dict):
            return ""

        return str(presentation.get("type") or "").strip().lower()
