"""Acesso a presenter_content.json — Fase 3A lote 16."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionPresenterContentPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _path_fragment_title(self, fragment: str) -> str | None:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        key = str(fragment or "").strip()
        if not key:
            return None

        if not key.startswith("/"):
            key = f"/{key}"

        return ChatAssistantContentService.get(
            "presenter_content",
            "titlesByPathFragment",
            key,
        ) or ChatAssistantContentService.get(
            "presenter_content",
            "titlesByPathFragment",
            key.lstrip("/"),
        )

    def _analyser_markdown(self, key: str, **values: str) -> str:
        return self._presenter_text("analyserMarkdown", key, **values)

    def _route_narrative(self, route: str, key: str, **values: str) -> str:
        return self._presenter_text("routeNarratives", route, key, **values)

    def _route_presentation(self, route: str, key: str, **values: str) -> str:
        return self._presenter_text("routePresentations", route, key, **values)

    def _presenter_text(
        self,
        section: str,
        text_key: str,
        *extra_path: str,
        **values: str,
    ) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        path = (section, text_key, *extra_path)

        if values:
            return ChatAssistantContentService.format(
                "presenter_content",
                *path,
                **values,
            )

        return ChatAssistantContentService.get("presenter_content", *path)

    def _presenter_root_format(self, key: str, **values: str) -> str:
        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        return ChatAssistantContentService.format(
            "presenter_content",
            key,
            **values,
        )
