"""Papel (`role`) de tabelas ricas — vocabulário declarativo (Playbook 12 R1)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationTableRoleService:
    @classmethod
    def allowed_roles(cls) -> frozenset[str]:
        return frozenset(ChatPresentationVocabularyService.table_role_allowed_roles())

    @classmethod
    def default_role(cls) -> str:
        return ChatPresentationVocabularyService.table_role_default()

    @classmethod
    def _title_token_groups_for_profile(cls, profile_key: str) -> tuple[str, ...]:
        profile_groups = ChatPresentationVocabularyService.table_role_profile_title_token_groups(
            profile_key,
        )

        if profile_groups:
            return profile_groups

        return ChatPresentationVocabularyService.table_role_title_token_group_priority()

    @classmethod
    def _match_title_token_group_role(cls, normalized_title: str, group_keys: tuple[str, ...]) -> str | None:
        for group_key in group_keys:
            role = ChatPresentationVocabularyService.table_role_for_title_token_group(group_key)

            if not role:
                continue

            for token in ChatPresentationVocabularyService.table_title_tokens(group_key):
                token_value = str(token or "").strip().lower()

                if token_value and token_value in normalized_title:
                    return role

        return None

    @classmethod
    def resolve_role(
        cls,
        title: str,
        *,
        path: str = "",
        profile_key: str = "",
    ) -> str:
        del path

        normalized = str(title or "").strip().lower()

        if not normalized:
            return cls.default_role()

        for prefix in ChatPresentationVocabularyService.profile_table_title_prefixes():
            prefix_token = str(prefix or "").strip().lower()

            if prefix_token and normalized.startswith(prefix_token):
                return "profile"

        for token in ChatPresentationVocabularyService.profile_table_title_tokens():
            token_value = str(token or "").strip().lower()

            if token_value and token_value in normalized:
                return "profile"

        resolved_profile = str(profile_key or "").strip()
        group_keys = cls._title_token_groups_for_profile(resolved_profile)

        if resolved_profile and resolved_profile != "generic":
            grouped_role = cls._match_title_token_group_role(normalized, group_keys)

            if grouped_role:
                return grouped_role

        for role_key in ChatPresentationVocabularyService.table_role_global_match_order():
            for token in ChatPresentationVocabularyService.table_role_global_tokens(role_key):
                token_value = str(token or "").strip().lower()

                if token_value and token_value in normalized:
                    return role_key

        if not resolved_profile or resolved_profile == "generic":
            grouped_role = cls._match_title_token_group_role(
                normalized,
                ChatPresentationVocabularyService.table_role_title_token_group_priority(),
            )

            if grouped_role:
                return grouped_role

        return cls.default_role()

    @classmethod
    def assign_table_role(
        cls,
        table: dict[str, Any],
        *,
        path: str = "",
        profile_key: str = "",
        forced_role: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(table, dict):
            return table

        if str(table.get("type") or "").strip().lower() != "table":
            return table

        updated = dict(table)
        existing = str(updated.get("role") or "").strip()

        if existing in cls.allowed_roles():
            return updated

        if forced_role and forced_role in cls.allowed_roles():
            updated["role"] = forced_role
            return updated

        updated["role"] = cls.resolve_role(
            str(updated.get("title") or ""),
            path=path,
            profile_key=profile_key,
        )
        return updated

    @classmethod
    def assign_roles(
        cls,
        tables: list[dict[str, Any]],
        *,
        path: str = "",
        profile_key: str = "",
    ) -> list[dict[str, Any]]:
        return [
            cls.assign_table_role(table, path=path, profile_key=profile_key)
            for table in tables
            if isinstance(table, dict)
        ]

    @classmethod
    def enrich_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        path: str = "",
        profile_key: str = "",
        entity: str | None = None,
    ) -> None:
        if not isinstance(metadata, dict):
            return

        resolved_path = str(path or metadata.get("path") or "").strip()
        resolved_profile = str(profile_key or "").strip() or ChatPresentationProfileService.resolve_profile_key(
            resolved_path,
            entity=str(entity or metadata.get("entity") or "").strip() or None,
        )

        metadata_roles = ChatPresentationVocabularyService.table_role_metadata_presentation_roles()

        for metadata_key, role in metadata_roles.items():
            presentation = metadata.get(metadata_key)

            if not isinstance(presentation, dict):
                continue

            metadata[metadata_key] = cls.assign_table_role(
                presentation,
                path=resolved_path,
                profile_key=resolved_profile,
                forced_role=role,
            )

        for metadata_key in (
            "presentation",
            "tablePresentation",
        ):
            presentation = metadata.get(metadata_key)

            if isinstance(presentation, dict):
                metadata[metadata_key] = cls.assign_table_role(
                    presentation,
                    path=resolved_path,
                    profile_key=resolved_profile,
                )

        table_presentations = metadata.get("tablePresentations")

        if isinstance(table_presentations, list):
            metadata["tablePresentations"] = cls.assign_roles(
                table_presentations,
                path=resolved_path,
                profile_key=resolved_profile,
            )

        dashboard = metadata.get("dashboardPresentation")

        if isinstance(dashboard, dict) and isinstance(dashboard.get("panels"), list):
            panels: list[Any] = []

            for panel in dashboard.get("panels") or []:
                if not isinstance(panel, dict):
                    panels.append(panel)
                    continue

                updated_panel = dict(panel)
                presentation = updated_panel.get("presentation")

                if isinstance(presentation, dict):
                    updated_panel["presentation"] = cls.assign_table_role(
                        presentation,
                        path=resolved_path,
                        profile_key=resolved_profile,
                    )

                panels.append(updated_panel)

            dashboard["panels"] = panels
