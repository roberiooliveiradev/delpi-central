"""Modo Texto explícito — markdown completo sem componentes nativos no payload."""

from __future__ import annotations

from typing import Any

_NATIVE_VISUAL_SLOTS = (
    "presentation",
    "tablePresentation",
    "tablePresentations",
    "treePresentation",
    "chartPresentation",
    "kpiPresentation",
    "dashboardPresentation",
    "inspectionTablePresentation",
    "profileTablePresentation",
)


class ChatPresentationTextModeService:
    @classmethod
    def is_user_explicit_text_mode(cls, metadata: dict[str, Any]) -> bool:
        if not isinstance(metadata, dict):
            return False

        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        return explicit in {"text", "topics"}

    @classmethod
    def should_embed_in_markdown(cls, metadata: dict[str, Any]) -> bool:
        """Embute árvore/tabela/gráfico no markdown só no modo Texto explícito da sessão."""
        return cls.is_user_explicit_text_mode(metadata)

    @classmethod
    def enforce_single_text_decision(cls, metadata: dict[str, Any]) -> None:
        if not cls.is_user_explicit_text_mode(metadata):
            return

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            return

        decision["selected"] = "text"
        decision["layoutMode"] = "single"
        decision["visualOrder"] = ["text"]

        views = decision.get("availableViews")

        if isinstance(views, list) and views:
            merged = list(dict.fromkeys(["text", *[str(view).strip().lower() for view in views if str(view).strip()]]))
            decision["availableViews"] = merged

    @classmethod
    def strip_native_visual_slots(cls, metadata: dict[str, Any]) -> None:
        if not cls.is_user_explicit_text_mode(metadata):
            return

        for slot in _NATIVE_VISUAL_SLOTS:
            metadata.pop(slot, None)

        decision = metadata.get("presentationDecision")

        if isinstance(decision, dict):
            decision["layoutMode"] = "single"
            decision["visualOrder"] = ["text"]

        metadata["preferredFormat"] = "text"
