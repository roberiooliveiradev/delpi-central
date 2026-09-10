"""Resolução canônica de título de resultado/apresentação (não afeta routing)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

SOURCE_SLOT_TITLE = "SLOT_TITLE"
SOURCE_PRESENTATION_TITLE = "PRESENTATION_TITLE"
SOURCE_ACTION_DISPLAY_LABEL = "ACTION_DISPLAY_LABEL"
SOURCE_LEGACY_PATH_FRAGMENT = "LEGACY_PATH_FRAGMENT"
SOURCE_LEGACY_PATH_TITLES = "LEGACY_PATH_TITLES"
SOURCE_TECHNICAL_FALLBACK = "TECHNICAL_FALLBACK"

_MODE_ENV = "PRESENTATION_TITLE_MODE"


@dataclass(frozen=True)
class ResultPresentationTitleResult:
    title: str
    source: str
    shadow_title: str | None = None
    shadow_source: str | None = None


class ResultPresentationTitleResolver:
    """Cascata: slot/presentation.title → action label → legacy JSON path titles.

    Modos (`PRESENTATION_TITLE_MODE`):
    - ``legacy``: só mapas JSON (comportamento histórico via callers)
    - ``shadow``: UX legacy; calcula candidato
    - ``default``: cascata canônica com legacy como fallback
    """

    @classmethod
    def mode(cls) -> str:
        token = str(os.environ.get(_MODE_ENV) or "default").strip().lower()
        if token in {"legacy", "shadow", "default"}:
            return token
        return "default"

    @classmethod
    def resolve(
        cls,
        *,
        path: str = "",
        method: str = "GET",
        summary: str = "",
        action_id: str = "",
        slot_title: str | None = None,
        metadata: dict | None = None,
        legacy_title: str | None = None,
        fallback: str = "Resultado",
    ) -> ResultPresentationTitleResult:
        legacy = cls._coerce_title(legacy_title)
        auto_legacy = None if legacy else cls._legacy_from_path(path)
        candidate = cls._resolve_canonical(
            path=path,
            method=method,
            summary=summary,
            action_id=action_id,
            slot_title=slot_title,
            metadata=metadata,
            legacy_title=legacy,
            auto_legacy_title=auto_legacy,
            fallback=fallback,
        )

        current_mode = cls.mode()

        if current_mode == "legacy":
            title = legacy or auto_legacy or fallback
            return ResultPresentationTitleResult(
                title=title,
                source=SOURCE_LEGACY_PATH_FRAGMENT if (legacy or auto_legacy) else SOURCE_TECHNICAL_FALLBACK,
            )

        if current_mode == "shadow":
            ux_title = legacy or auto_legacy or candidate.title
            if (legacy or auto_legacy) and ux_title != candidate.title:
                logger.info(
                    "presentation_title_shadow_diff",
                    extra={
                        "path": path,
                        "legacyTitle": ux_title,
                        "candidateTitle": candidate.title,
                        "candidateSource": candidate.source,
                    },
                )
            return ResultPresentationTitleResult(
                title=ux_title,
                source=(
                    SOURCE_LEGACY_PATH_FRAGMENT
                    if (legacy or auto_legacy)
                    else candidate.source
                ),
                shadow_title=candidate.title,
                shadow_source=candidate.source,
            )

        return candidate

    @classmethod
    def _resolve_canonical(
        cls,
        *,
        path: str,
        method: str,
        summary: str,
        action_id: str,
        slot_title: str | None,
        metadata: dict | None,
        legacy_title: str | None,
        auto_legacy_title: str | None,
        fallback: str,
    ) -> ResultPresentationTitleResult:
        slot = cls._coerce_title(slot_title)
        if slot:
            return ResultPresentationTitleResult(title=slot, source=SOURCE_SLOT_TITLE)

        presentation_title = cls._presentation_title(metadata)
        if presentation_title:
            return ResultPresentationTitleResult(
                title=presentation_title,
                source=SOURCE_PRESENTATION_TITLE,
            )

        # Editorial explícito do caller (ex.: kpiPathMatchers) vence action label genérico
        if legacy_title:
            return ResultPresentationTitleResult(
                title=legacy_title,
                source=SOURCE_LEGACY_PATH_FRAGMENT,
            )

        action_label = cls._action_label(
            path=path,
            method=method,
            summary=summary,
            action_id=action_id,
            metadata=metadata,
        )
        if action_label:
            return ResultPresentationTitleResult(
                title=action_label,
                source=SOURCE_ACTION_DISPLAY_LABEL,
            )

        if auto_legacy_title:
            return ResultPresentationTitleResult(
                title=auto_legacy_title,
                source=SOURCE_LEGACY_PATH_FRAGMENT,
            )

        return ResultPresentationTitleResult(
            title=fallback,
            source=SOURCE_TECHNICAL_FALLBACK,
        )

    @classmethod
    def _presentation_title(cls, metadata: dict | None) -> str | None:
        if not isinstance(metadata, dict):
            return None

        for key in ("title", "sectionTitle", "routeTitle"):
            value = cls._coerce_title(metadata.get(key))
            if value:
                return value

        presentation = metadata.get("presentation")
        if isinstance(presentation, dict):
            for key in ("title", "sectionTitle", "routeTitle"):
                value = cls._coerce_title(presentation.get(key))
                if value:
                    return value

        decision = metadata.get("presentationDecision")
        if isinstance(decision, dict):
            value = cls._coerce_title(decision.get("title") or decision.get("sectionTitle"))
            if value:
                return value

        return None

    @classmethod
    def _action_label(
        cls,
        *,
        path: str,
        method: str,
        summary: str,
        action_id: str,
        metadata: dict | None,
    ) -> str | None:
        from app.domain.services.action_display_label_resolver import (
            ActionDisplayLabelResolver,
        )

        meta = metadata if isinstance(metadata, dict) else {}
        raw_summary = (
            summary
            or str(meta.get("summary") or meta.get("actionSummary") or "").strip()
        )
        if not path and not raw_summary and not action_id:
            return None

        result = ActionDisplayLabelResolver.resolve(
            path=path or str(meta.get("path") or ""),
            method=method or str(meta.get("method") or "GET"),
            summary=raw_summary,
            action_id=action_id or str(meta.get("actionId") or ""),
            provider_key=str(meta.get("providerKey") or ""),
            delpi_metadata=(
                meta.get("delpiMetadata")
                if isinstance(meta.get("delpiMetadata"), dict)
                else None
            ),
            schema_hash=str(meta.get("schemaHash") or ""),
        )
        label = cls._coerce_title(result.label)
        if not label:
            return None

        # Evita usar fallback técnico genérico como título de painel
        if result.source == "TECHNICAL_FALLBACK" and label in {
            path,
            action_id,
            "Consulta autorizada",
        }:
            return None

        return label

    @classmethod
    def _legacy_from_path(cls, path: str) -> str | None:
        if not path:
            return None

        from app.domain.services.chat_assistant_content_service import (
            ChatAssistantContentService,
        )

        return cls._coerce_title(
            ChatAssistantContentService.title_for_path(
                "presenter_content",
                path,
                default=None,
            )
        )

    @staticmethod
    def _coerce_title(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        token = value.strip()
        return token or None
