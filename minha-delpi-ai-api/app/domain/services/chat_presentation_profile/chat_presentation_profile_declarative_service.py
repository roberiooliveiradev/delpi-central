"""Delegate — vocabulário declarativo W2 (text-first, tier A, tabela, namespace)."""

from __future__ import annotations

from app.domain.services.chat_presentation_profile.chat_presentation_profile_facade_access import (
    presentation_profile_service,
)
from app.domain.services.chat_presentation_profile.chat_presentation_profile_resolve_service import (
    ChatPresentationProfileResolveService,
)


class ChatPresentationProfileDeclarativeService:
    @classmethod
    def text_first_profile_keys(cls) -> frozenset[str]:
        return presentation_profile_service().entity_set("textFirstProfiles")

    @classmethod
    def tier_a_profile_keys(cls) -> frozenset[str]:
        return presentation_profile_service().entity_set("tierAProfileKeys")

    @classmethod
    def is_text_first_profile(cls, profile_key: str | None) -> bool:
        token = str(profile_key or "").strip()

        return bool(token and token in cls.text_first_profile_keys())

    @classmethod
    def path_fragments_for_profile_keys(cls, profile_keys: frozenset[str]) -> frozenset[str]:
        rules = presentation_profile_service().node("pathRules") or []
        fragments: set[str] = set()

        if not isinstance(rules, list):
            return frozenset()

        for rule in rules:
            if not isinstance(rule, dict):
                continue

            profile = str(rule.get("profile") or "").strip()
            fragment = str(rule.get("contains") or "").strip().lower()

            if profile in profile_keys and fragment:
                fragments.add(fragment)

        return frozenset(fragments)

    @classmethod
    def tier_a_table_assembly_path_fragments(cls) -> frozenset[str]:
        return cls.path_fragments_for_profile_keys(cls.tier_a_profile_keys())

    @classmethod
    def route_namespace(cls, profile_key: str | None = None, *, path: str | None = None, entity: str | None = None) -> str:
        key = str(profile_key or "").strip()

        if not key:
            key = presentation_profile_service().resolve_profile_key(path, entity)

        profile = ChatPresentationProfileResolveService.profile(key)
        namespace = str(profile.get("routeNamespace") or "").strip()

        return namespace

    @classmethod
    def table_profile_for_entity(cls, entity: str | None) -> str | None:
        token = str(entity or "").strip()

        if not token:
            return None

        mapping = presentation_profile_service().mapping("entityTableProfiles")
        hinted = mapping.get(token)

        return str(hinted).strip() if hinted else None
