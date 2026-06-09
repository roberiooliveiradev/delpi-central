"""Perfis declarativos de apresentação — rotas e entidades api-delpi (Fase 2)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class ChatPresentationProfileService(ChatAssistantVocabularyService):
    BUNDLE = "presentation_profiles"

    _SESSION_FORMAT_ALIASES = {
        "topics": "text",
    }

    @classmethod
    def path_lowered(cls, path: str | None) -> str:
        return str(path or "").strip().lower()

    @classmethod
    def resolve_profile_key(cls, path: str | None, entity: str | None = None) -> str:
        entity_token = str(entity or "").strip()

        if entity_token:
            mapped = cls.mapping("entityProfiles").get(entity_token)

            if mapped:
                return str(mapped)

        lowered = cls.path_lowered(path)

        for rule in cls.node("pathRules") or []:
            if not isinstance(rule, dict):
                continue

            fragment = str(rule.get("contains") or "").strip().lower()

            if fragment and fragment in lowered:
                return str(rule.get("profile") or "generic")

        return "generic"

    @classmethod
    def profile(cls, profile_key: str | None = None) -> dict[str, Any]:
        key = str(profile_key or "generic").strip() or "generic"
        resolved = cls.node("profiles", key)

        if isinstance(resolved, dict):
            return resolved

        defaults = cls.node("defaults")

        return defaults if isinstance(defaults, dict) else {}

    @classmethod
    def resolve_profile(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        key = cls.resolve_profile_key(path, entity)
        merged = dict(cls.node("defaults") or {})
        merged.update(cls.profile(key))
        merged["profileKey"] = key
        return merged

    @classmethod
    def flags(cls, path: str | None, entity: str | None = None) -> frozenset[str]:
        profile = cls.resolve_profile(path, entity)
        raw = profile.get("flags") or []

        return frozenset(str(item).strip().lower() for item in raw if str(item).strip())

    @classmethod
    def has_flag(
        cls,
        path: str | None,
        flag: str,
        *,
        entity: str | None = None,
    ) -> bool:
        return str(flag or "").strip().lower() in cls.flags(path, entity)

    @classmethod
    def stack_plan_config(
        cls,
        path: str | None,
        entity: str | None = None,
    ) -> dict[str, Any]:
        profile = cls.resolve_profile(path, entity)
        stack_key = str(profile.get("stackPlan") or "default").strip() or "default"
        resolved = cls.node("stackPlans", stack_key)

        if isinstance(resolved, dict):
            return dict(resolved)

        default_plan = cls.node("stackPlans", "default")

        return dict(default_plan) if isinstance(default_plan, dict) else {}

    @classmethod
    def resolve_default_preferred_format(
        cls,
        *,
        path: str | None,
        session_format: str | None = None,
        entity: str | None = None,
        has_tree: bool = False,
        has_table: bool = False,
        has_chart: bool = False,
        has_text: bool = False,
        has_kpi: bool = False,
    ) -> str | None:
        token = str(session_format or "").strip().lower()

        if token in {"table", "text", "tree", "chart", "topics", "canvas"}:
            if token == "canvas":
                return "text"

            return cls._SESSION_FORMAT_ALIASES.get(token, token)

        profile = cls.resolve_profile(path, entity)
        policy = str(profile.get("defaultViewPolicy") or "generic").strip().lower()
        flags = cls.flags(path, entity)

        if policy == "stock" or "stock" in flags:
            if has_chart and not has_table:
                return "chart"

            if has_table:
                return "table"

            if has_chart:
                return "chart"

            return "text" if has_text else None

        if policy == "tree_when_available":
            if has_tree and ("tree" in flags or "analyser" in flags):
                return "tree"

        if policy == "table_when_available":
            if has_table and ("table" in flags or "analyser" in flags):
                return "table"

        return cls._generic_default_preferred_format(
            has_tree=has_tree,
            has_table=has_table,
            has_chart=has_chart,
            has_text=has_text,
            has_kpi=has_kpi,
        )

    @classmethod
    def apply_visual_order(
        cls,
        decision: dict[str, Any],
        *,
        path: str | None,
        entity: str | None = None,
    ) -> None:
        views = list(decision.get("availableViews") or [])

        if not views:
            return

        normalized = {str(view).strip().lower() for view in views}
        profile = cls.resolve_profile(path, entity)
        priority = [
            str(view).strip().lower()
            for view in (profile.get("viewOrder") or [])
            if str(view).strip()
        ]

        ordered: list[str] = []

        for view in priority:
            if view in normalized and view not in ordered:
                ordered.append(view)

        for view in sorted(normalized):
            if view not in ordered:
                ordered.append(view)

        if len(ordered) >= 2 and str(decision.get("layoutMode") or "") != "single":
            decision["layoutMode"] = "stack"

        decision["visualOrder"] = ordered
        decision["presentationProfileKey"] = profile.get("profileKey")

    @classmethod
    def _generic_default_preferred_format(
        cls,
        *,
        has_tree: bool,
        has_table: bool,
        has_chart: bool,
        has_text: bool,
        has_kpi: bool,
    ) -> str | None:
        if has_kpi:
            return "kpi"

        if has_chart:
            return "chart"

        if has_table:
            return "table"

        if has_text:
            return "text"

        return None
