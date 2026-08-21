"""Política texto-first e visuais sob demanda — Playbook 12 R14.

Anti-padrão: nunca forçar texto (e ocultar tabela/árvore no renderPlan) quando o
perfil efetivo do turno pede evidência (`table_when_available`, `tree_when_available`,
`kpi_when_available`, `stock`). Callers devem passar ``metadata`` para reutilizar o
``presentationProfile`` cacheado / shape OpenAPI.
"""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import ChatAssistantVocabularyService
from app.domain.services.chat_presentation_profile_service import ChatPresentationProfileService

_EXPLICIT_FORMATS = frozenset({"text", "table", "tree", "chart", "canvas", "topics", "dashboard", "kpi"})
_AUXILIARY_SLOTS = (
    "chartPresentation",
    "treePresentation",
    "kpiPresentation",
    "dashboardPresentation",
)
_EVIDENCE_VIEW_POLICIES = frozenset(
    {
        "table_when_available",
        "tree_when_available",
        "kpi_when_available",
        "stock",
    }
)


class ChatPresentationTextFirstPolicyService(ChatAssistantVocabularyService):
    BUNDLE = "presentation_vocabulary"
    _ROOT = ("textFirstPolicy",)

    @classmethod
    def _resolve_profile(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return ChatPresentationProfileService.resolve_profile(
            path,
            entity,
            metadata=metadata,
        )

    @classmethod
    def view_build_policy(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        profile = cls._resolve_profile(path, entity, metadata=metadata)
        token = str(profile.get("viewBuildPolicy") or "on_demand").strip().lower()

        return token if token in {"eager", "on_demand"} else "on_demand"


    @classmethod
    def stack_layout_policy(
        cls,
        path: str | None,
        entity: str | None = None,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        profile = cls._resolve_profile(path, entity, metadata=metadata)
        token = str(profile.get("stackLayoutPolicy") or "on_demand").strip().lower()

        return token if token in {"always", "on_demand"} else "on_demand"

    @classmethod
    def normalize_explicit_format(cls, token: str | None) -> str | None:
        normalized = str(token or "").strip().lower()

        if normalized in {"", "auto"}:
            return None

        if normalized == "topics":
            return "text"

        if normalized in _EXPLICIT_FORMATS:
            return normalized

        return None

    @classmethod
    def looks_like_integrated_stack_request(cls, message: str | None) -> bool:
        lowered = re.sub(r"\s+", " ", str(message or "").strip().lower())

        if not lowered:
            return False

        return any(
            hint in lowered
            for hint in cls.terms(*cls._ROOT, "integratedStackHints")
        )

    @classmethod
    def should_build_views(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        explicit_format: str | None = None,
        user_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        if cls.view_build_policy(path, entity, metadata=metadata) == "eager":
            return True

        if cls.stack_layout_policy(path, entity, metadata=metadata) == "always":
            return True

        normalized = cls.normalize_explicit_format(explicit_format)

        if normalized and normalized not in {"text"}:
            return True

        if cls.looks_like_integrated_stack_request(user_message):
            return True

        return False


    @classmethod
    def should_default_to_text_only(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        explicit_format: str | None = None,
        user_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        normalized = cls.normalize_explicit_format(explicit_format)

        if normalized and normalized != "text":
            return False

        if cls.looks_like_integrated_stack_request(user_message):
            return False

        if cls.view_build_policy(path, entity, metadata=metadata) == "eager":
            return False

        profile = cls._resolve_profile(path, entity, metadata=metadata)
        policy = str(profile.get("defaultViewPolicy") or "generic").strip().lower()

        # Evidência tabular/árvore/KPI nunca é ocultada por texto-first automático.
        if policy in _EVIDENCE_VIEW_POLICIES:
            return False

        profile_key = str(profile.get("profileKey") or "").strip()

        if not profile_key or profile_key.startswith("openapi:"):
            profile_key = ChatPresentationProfileService.resolve_effective_profile_key(
                path,
                entity,
                shape=str(profile.get("openapiShape") or "").strip() or None,
            )

        if not normalized and ChatPresentationProfileService.is_text_first_profile(profile_key):
            strategy = str(profile.get("presentationStrategy") or "").strip().lower()

            if strategy == "as_delivered":
                return policy == "text_when_available"

            return True

        if policy == "text_when_available":
            return True

        if cls.view_build_policy(path, entity, metadata=metadata) == "on_demand" and not normalized:
            return policy not in _EVIDENCE_VIEW_POLICIES

        return False

    @classmethod
    def should_use_stack_layout(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        explicit_format: str | None = None,
        user_message: str | None = None,
        available_view_count: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        if available_view_count < 2:
            return False

        if cls.stack_layout_policy(path, entity, metadata=metadata) == "always":
            return True

        if cls.looks_like_integrated_stack_request(user_message):
            return True

        normalized = cls.normalize_explicit_format(explicit_format)

        return normalized is not None and normalized != "text"

    @classmethod
    def latent_available_views(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        has_text: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> list[str]:
        profile = cls._resolve_profile(path, entity, metadata=metadata)
        views = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]

        if has_text and "text" not in views:
            views.insert(0, "text")

        if not views and has_text:
            return ["text"]

        return list(dict.fromkeys(views))

    @classmethod
    def apply_text_primary_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        path: str | None,
        entity: str | None = None,
        explicit_format: str | None = None,
        user_message: str | None = None,
    ) -> bool:
        if not isinstance(metadata, dict):
            return False

        if not cls.should_default_to_text_only(
            path=path,
            entity=entity,
            explicit_format=explicit_format,
            user_message=user_message,
            metadata=metadata,
        ):
            return False

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return False

        from app.domain.services.chat_presentation_primary_view_service import (
            ChatPresentationPrimaryViewService,
        )

        ChatPresentationPrimaryViewService.relocate_primary_to_text_auxiliary_slots(metadata)
        metadata["preferredFormat"] = "text"

        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            presentation_type = str(presentation.get("type") or "").strip().lower()

            if presentation_type == "table" and not metadata.get("tablePresentation"):
                metadata["tablePresentation"] = presentation
            elif presentation_type == "chart" and not metadata.get("chartPresentation"):
                metadata["chartPresentation"] = presentation
            elif presentation_type == "tree" and not metadata.get("treePresentation"):
                metadata["treePresentation"] = presentation
            elif presentation_type == "kpi" and not metadata.get("kpiPresentation"):
                metadata["kpiPresentation"] = presentation
            elif presentation_type == "dashboard" and not metadata.get("dashboardPresentation"):
                metadata["dashboardPresentation"] = presentation

        metadata["presentation"] = None

        if not cls.should_build_views(
            path=path,
            entity=entity,
            explicit_format=explicit_format,
            user_message=user_message,
            metadata=metadata,
        ):
            cls._strip_auxiliary_presentations(
                metadata,
                path=path,
                entity=entity,
                explicit_format=explicit_format,
            )

        return True

    @classmethod
    def _strip_auxiliary_presentations(
        cls,
        metadata: dict[str, Any],
        *,
        path: str | None = None,
        entity: str | None = None,
        explicit_format: str | None = None,
    ) -> None:
        profile = cls._resolve_profile(
            path or str(metadata.get("path") or ""),
            entity,
            metadata=metadata,
        )
        keep_tree = profile.get("textEmbedTreeOutline") is True
        explicit_text = cls.normalize_explicit_format(explicit_format) == "text"
        keep_chart = (
            profile.get("textEmbedChartsInMarkdown") is True and explicit_text
        )

        for slot in _AUXILIARY_SLOTS:
            if slot == "treePresentation" and keep_tree:
                continue

            if slot == "chartPresentation" and keep_chart:
                continue

            metadata.pop(slot, None)

        formats = [
            str(token).strip().lower()
            for token in (metadata.get("availableFormats") or [])
            if str(token).strip()
        ]
        latent = cls.latent_available_views(
            path=path or str(metadata.get("path") or ""),
            entity=entity,
            has_text=bool(metadata.get("textPresentation")),
            metadata=metadata,
        )
        kept = [
            token
            for token in latent
            if token in {"text", "canvas", "table", "chart", "tree", "kpi", "dashboard"}
        ]

        for token in formats:
            if token in {"text", "canvas", "table", "chart", "tree", "kpi", "dashboard"} and token not in kept:
                kept.append(token)

        if metadata.get("textPresentation") and "text" not in kept:
            kept.insert(0, "text")

        metadata["availableFormats"] = list(dict.fromkeys(kept))
