"""Detecção e override de formato de apresentação — Fase 3C lote 9."""

from __future__ import annotations

from app.domain.services.chat_presentation_format_vocabulary_service import (
    ChatPresentationFormatVocabularyService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


class ChatToolContextFormatService:
    def __init__(self, presenter: ExternalActionResultPresenter | None = None) -> None:
        self._presenter = presenter or ExternalActionResultPresenter()

    @classmethod
    def session_response_format(cls, workspace_context: dict | None) -> str | None:
        working = (workspace_context or {}).get("workingMemory") or {}
        behavior = working.get("behaviorInstructions") or {}
        token = str(behavior.get("responseFormat") or "").strip().lower()

        if token in {"table", "text", "tree", "chart", "topics", "canvas"}:
            return token

        prefs = working.get("userPreferences") or {}
        pref_behavior = prefs.get("behavior") if isinstance(prefs, dict) else None

        if isinstance(pref_behavior, dict):
            token = str(pref_behavior.get("responseFormat") or "").strip().lower()

            if token in {"table", "text", "tree", "chart", "topics", "canvas"}:
                return token

        return None

    @classmethod
    def detect_requested_format(cls, message: str) -> str | None:
        """Detecta se o usuário pediu um formato específico de apresentação."""
        lowered = (message or "").lower()

        if any(h in lowered for h in ChatPresentationFormatVocabularyService.text_hints(include_tool_context=True)):
            return "text"

        if any(h in lowered for h in ChatPresentationFormatVocabularyService.tree_hints(include_tool_context=True)):
            return "tree"

        if any(h in lowered for h in ChatPresentationFormatVocabularyService.table_hints(include_tool_context=True)):
            return "table"

        if any(h in lowered for h in ChatPresentationFormatVocabularyService.chart_hints()):
            return "chart"

        return None

    @classmethod
    def resolve_consolidation_format(
        cls,
        message: str,
        previous_messages: list | None,
        *,
        workspace_context: dict | None = None,
    ) -> str | None:
        requested_format = cls.detect_requested_format(message)

        if requested_format:
            return requested_format

        session_format = cls.session_response_format(workspace_context)

        if session_format and session_format != "topics":
            return session_format

        from app.domain.services.chat_pagination_consolidation_service import (
            ChatPaginationConsolidationService,
        )

        return ChatPaginationConsolidationService.collect_last_preferred_format(
            previous_messages,
        )

    def _force_tree_presentation(
        self,
        meta: dict,
        last_data,
        *,
        path: str,
    ) -> dict | None:
        tree_pres = meta.get("treePresentation") or meta.get("presentation")

        if isinstance(tree_pres, dict) and tree_pres.get("type") == "tree":
            return tree_pres

        if last_data is None:
            return None

        from app.domain.services.chat_presentation_profile_visual_bundle_service import (
            ChatPresentationProfileVisualBundleService,
        )

        path_token = str(path or "")
        profile_tree = ChatPresentationProfileVisualBundleService.build_profile_view(
            self._presenter,
            path=path_token,
            view="tree",
            data=last_data,
        )

        if isinstance(profile_tree, dict) and profile_tree.get("type") == "tree":
            return profile_tree

        forced_tree = self._presenter.build_tree_presentation(last_data, path=path_token)

        if isinstance(forced_tree, dict) and forced_tree.get("type") == "tree":
            return forced_tree

        return None

    def _force_table_presentation(
        self,
        meta: dict,
        last_data,
        *,
        path: str,
    ) -> dict | None:
        table_pres = meta.get("tablePresentation")

        if isinstance(table_pres, dict) and table_pres.get("type") == "table":
            return table_pres

        presentation = meta.get("presentation")

        if isinstance(presentation, dict) and presentation.get("type") == "table":
            return presentation

        cached = self._find_table_presentation(meta)

        if isinstance(cached, dict) and cached.get("type") == "table":
            return cached

        if last_data is None:
            return None

        from app.domain.services.chat_presentation_profile_visual_bundle_service import (
            ChatPresentationProfileVisualBundleService,
        )

        path_token = str(path or "")
        profile_table = ChatPresentationProfileVisualBundleService.build_profile_table_view(
            self._presenter,
            path=path_token,
            data=last_data,
        )

        if isinstance(profile_table, dict) and profile_table.get("type") == "table":
            return profile_table

        forced_table = self._presenter.build_presentation(last_data, path=path_token)

        if isinstance(forced_table, dict) and forced_table.get("type") == "table":
            return forced_table

        return None

    def apply_format_override(
        self,
        safe_tool_calls: list[dict],
        requested_format: str,
        last_data,
    ) -> None:
        """Sobrescreve a presentation com base no formato solicitado pelo usuário."""
        for tc in safe_tool_calls:
            if tc.get("name") != "execute_external_action":
                continue
            meta = tc.get("metadata")
            if not meta or not meta.get("ok"):
                continue

            if requested_format == "text":
                meta["preferredFormat"] = "text"
                decision = meta.get("presentationDecision")

                if isinstance(decision, dict):
                    decision["selected"] = "text"

                had_kpi_primary = (
                    isinstance(meta.get("presentation"), dict)
                    and meta["presentation"].get("type") == "kpi"
                )

                from app.application.use_cases.execute_external_action_use_case import (
                    ExecuteExternalActionUseCase,
                )

                ExecuteExternalActionUseCase._align_presentation_with_decision(
                    meta,
                    kpi_presentation=(
                        meta.get("kpiPresentation")
                        if isinstance(meta.get("kpiPresentation"), dict)
                        else meta.get("presentation")
                        if had_kpi_primary
                        else None
                    ),
                )

                text_presentation = meta.get("textPresentation")
                markdown = (
                    str(text_presentation.get("markdown") or "").strip()
                    if isinstance(text_presentation, dict)
                    else ""
                )
                caption_only = markdown.startswith("###") and "**" not in markdown

                if last_data and (had_kpi_primary or caption_only):
                    path = str(meta.get("path") or "")
                    rebuilt = self._presenter.build_text_presentation(
                        last_data,
                        path=path,
                    )

                    if rebuilt:
                        meta["textPresentation"] = rebuilt

            elif requested_format == "tree":
                meta["preferredFormat"] = "tree"
                forced_tree = self._force_tree_presentation(
                    meta,
                    last_data,
                    path=str(meta.get("path") or ""),
                )

                if forced_tree:
                    meta["presentation"] = forced_tree
                    meta["treePresentation"] = None

                self._align_decision_for_format(meta, "tree")

            elif requested_format == "table":
                meta["preferredFormat"] = "table"
                forced_table = self._force_table_presentation(
                    meta,
                    last_data,
                    path=str(meta.get("path") or ""),
                )

                if forced_table:
                    meta["presentation"] = forced_table
                    meta["tablePresentation"] = None

                self._align_decision_for_format(meta, "table")

            elif requested_format == "chart":
                meta["preferredFormat"] = "chart"
                chart_pres = meta.get("presentation")
                if chart_pres and chart_pres.get("type") == "chart":
                    pass
                elif last_data:
                    path = meta.get("path") or ""
                    forced_chart = self._presenter.build_chart_presentation(
                        last_data, path=path, force=True
                    )
                    if forced_chart:
                        meta["presentation"] = forced_chart
                        meta["tablePresentation"] = None

                self._align_decision_for_format(meta, "chart")

    @staticmethod
    def _find_table_presentation(meta: dict) -> dict | None:
        from app.domain.services.chat_presentation_primary_view_service import (
            ChatPresentationPrimaryViewService,
        )

        table, _source = ChatPresentationPrimaryViewService._find_view(meta, "table")

        return table if isinstance(table, dict) else None

    @staticmethod
    def _align_decision_for_format(meta: dict, requested_format: str) -> None:
        decision = meta.get("presentationDecision")

        if not isinstance(decision, dict):
            return

        decision["selected"] = requested_format
        decision["layoutMode"] = "single"
        decision["visualOrder"] = [requested_format]

        from app.domain.services.chat_presentation_recommendation_service import (
            ChatPresentationRecommendationService,
        )

        ChatPresentationRecommendationService.prune_for_selected(decision)

        meta["explicitSessionFormat"] = requested_format
        meta["preferredFormat"] = requested_format

        from app.application.use_cases.execute_external_action_use_case import (
            ExecuteExternalActionUseCase,
        )

        ExecuteExternalActionUseCase._align_presentation_with_decision(
            meta,
            kpi_presentation=(
                meta.get("kpiPresentation")
                if isinstance(meta.get("kpiPresentation"), dict)
                else None
            ),
        )
