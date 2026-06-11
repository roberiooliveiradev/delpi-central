"""Normalização declarativa de títulos de apresentação — Playbook 12 A9/R24."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ChatPresentationTitleNormalizationService:
    @classmethod
    def normalize_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        path: str,
        presenter: ExternalActionResultPresenter,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        lowered = str(path or "").lower()

        for policy in ChatPresentationVocabularyService.presentation_title_policies():
            if not isinstance(policy, dict):
                continue

            fragments = policy.get("pathFragments") or []

            if not any(str(fragment or "").strip().lower() in lowered for fragment in fragments):
                continue

            wrong_titles = {
                str(title or "").strip()
                for title in (policy.get("wrongTitles") or [])
                if str(title or "").strip()
            }
            fallback_title = str(policy.get("fallbackTitle") or "").strip()
            title = presenter._infer_items_title([], path) or fallback_title or None

            if not title:
                continue

            for key in policy.get("presentationKeys") or []:
                presentation = metadata.get(str(key))

                if not isinstance(presentation, dict):
                    continue

                current = str(presentation.get("title") or "").strip()

                if not current or current in wrong_titles:
                    presentation["title"] = title

            dashboard = metadata.get("presentation")
            panel_types = {
                str(token or "").strip().lower()
                for token in (policy.get("dashboardPanelTypes") or [])
                if str(token or "").strip()
            }

            if not isinstance(dashboard, dict) or dashboard.get("type") != "dashboard":
                continue

            for panel in dashboard.get("panels") or []:
                if not isinstance(panel, dict):
                    continue

                for nested_key in ("presentation", "chartPresentation"):
                    nested = panel.get(nested_key)

                    if not isinstance(nested, dict):
                        continue

                    nested_type = str(nested.get("type") or "").strip().lower()
                    current = str(nested.get("title") or "").strip()

                    if panel_types and nested_type in panel_types and (
                        not current or current in wrong_titles
                    ):
                        nested["title"] = (
                            title
                            if nested_type == "chart"
                            else panel.get("title") or "Itens do painel"
                        )
