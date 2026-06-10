"""Política texto-first e visuais sob demanda — Playbook 12 R14."""

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


_TEXT_FIRST_PROFILES = frozenset(
    {
        "structure_exclusivity",
        "raw_material_price_intelligence",
        "cost_impact_simulation",
        "sale_pricing",
        "last_purchase",
        "purchase_price_history",
        "purchase_budget_history",
        "purchase_list",
    }
)


class ChatPresentationTextFirstPolicyService(ChatAssistantVocabularyService):
    BUNDLE = "presentation_vocabulary"
    _ROOT = ("textFirstPolicy",)

    @classmethod
    def visual_bundle_policy(cls, path: str | None, entity: str | None = None) -> str:
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        token = str(profile.get("visualBundlePolicy") or "on_demand").strip().lower()

        return token if token in {"eager", "on_demand"} else "on_demand"

    @classmethod
    def stack_layout_policy(cls, path: str | None, entity: str | None = None) -> str:
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
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
    def should_build_visual_bundle(
        cls,
        *,
        path: str | None,
        entity: str | None = None,
        explicit_format: str | None = None,
        user_message: str | None = None,
    ) -> bool:
        if cls.visual_bundle_policy(path, entity) == "eager":
            return True

        normalized = cls.normalize_explicit_format(explicit_format)

        if normalized and normalized not in {"text"}:
            return True

        if cls.looks_like_integrated_stack_request(user_message):
            return True

        if not cls.normalize_explicit_format(explicit_format):
            profile_key = ChatPresentationProfileService.resolve_profile_key(path, entity)

            if profile_key in {
                "factory_status",
                "production_status",
                "shipping_status",
            }:
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
    ) -> bool:
        normalized = cls.normalize_explicit_format(explicit_format)

        if normalized and normalized != "text":
            return False

        if cls.looks_like_integrated_stack_request(user_message):
            return False

        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        profile_key = ChatPresentationProfileService.resolve_profile_key(path, entity)

        if not normalized and profile_key in _TEXT_FIRST_PROFILES:
            return True

        policy = str(profile.get("defaultViewPolicy") or "generic").strip().lower()

        if policy == "text_when_available":
            return True

        if cls.visual_bundle_policy(path, entity) == "on_demand" and not normalized:
            return policy not in {"tree_when_available", "table_when_available", "stock"}

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
    ) -> bool:
        if available_view_count < 2:
            return False

        if cls.stack_layout_policy(path, entity) == "always":
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
    ) -> list[str]:
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
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
        ):
            return False

        text_presentation = metadata.get("textPresentation")

        if not isinstance(text_presentation, dict):
            return False

        from app.domain.services.chat_presentation_primary_view_service import (
            ChatPresentationPrimaryViewService,
        )

        ChatPresentationPrimaryViewService.apply_session_preference(metadata, "text")
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

        if not cls.should_build_visual_bundle(
            path=path,
            entity=entity,
            explicit_format=explicit_format,
            user_message=user_message,
        ):
            cls._strip_auxiliary_presentations(metadata, path=path, entity=entity)

        return True

    @classmethod
    def _strip_auxiliary_presentations(
        cls,
        metadata: dict[str, Any],
        *,
        path: str | None = None,
        entity: str | None = None,
    ) -> None:
        profile = ChatPresentationProfileService.resolve_profile(
            path or str(metadata.get("path") or ""),
            entity,
        )
        keep_tree = profile.get("textEmbedTreeOutline") is True
        keep_chart = profile.get("textEmbedChartsInMarkdown") is True

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
