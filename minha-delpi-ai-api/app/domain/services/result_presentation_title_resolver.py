"""Resolução canônica de título de resultado/apresentação (não afeta routing)."""

from __future__ import annotations

from dataclasses import dataclass


SOURCE_SLOT_TITLE = "SLOT_TITLE"
SOURCE_PRESENTATION_TITLE = "PRESENTATION_TITLE"
SOURCE_ACTION_DISPLAY_LABEL = "ACTION_DISPLAY_LABEL"
SOURCE_TECHNICAL_FALLBACK = "TECHNICAL_FALLBACK"


@dataclass(frozen=True)
class ResultPresentationTitleResult:
    title: str
    source: str
    shadow_title: str | None = None
    shadow_source: str | None = None


class ResultPresentationTitleResolver:
    """Cascata: slot/presentation.title → action label → fallback."""

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
        # legacy_title retained for call-site compat; ignored in canonical cascade.
        _ = legacy_title
        return cls._resolve_canonical(
            path=path,
            method=method,
            summary=summary,
            action_id=action_id,
            slot_title=slot_title,
            metadata=metadata,
            fallback=fallback,
        )

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

        if result.source == "TECHNICAL_FALLBACK" and label in {
            path,
            action_id,
            "Consulta autorizada",
        }:
            return None

        return label

    @staticmethod
    def _coerce_title(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        token = value.strip()
        return token or None
