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
                tree_pres = meta.get("treePresentation") or meta.get("presentation")
                if tree_pres and tree_pres.get("type") == "tree":
                    meta["presentation"] = tree_pres
                    meta["treePresentation"] = None
                elif last_data:
                    path = meta.get("path") or ""
                    forced_tree = self._presenter.build_tree_presentation(
                        last_data, path=path
                    )
                    if forced_tree:
                        meta["presentation"] = forced_tree
                        meta["treePresentation"] = None

            elif requested_format == "table":
                meta["preferredFormat"] = "table"
                table_pres = meta.get("tablePresentation") or meta.get("presentation")
                if table_pres and table_pres.get("type") == "table":
                    meta["presentation"] = table_pres
                    meta["tablePresentation"] = None
                elif last_data:
                    path = meta.get("path") or ""
                    forced_table = self._presenter.build_presentation(
                        last_data, path=path
                    )
                    if forced_table:
                        meta["presentation"] = forced_table
                        meta["tablePresentation"] = None

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
