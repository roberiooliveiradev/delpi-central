"""Evita o mesmo conteúdo de estrutura/BOM em árvore e tabela na mesma resposta."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


class ChatPresentationStructureDedupService:
    @classmethod
    def _structure_table_title_markers(cls) -> tuple[str, ...]:
        return ChatPresentationVocabularyService.structure_table_title_markers()

    @classmethod
    def _parents_table_title_markers(cls) -> tuple[str, ...]:
        return ChatPresentationVocabularyService.parents_table_title_markers()

    @classmethod
    def is_structure_components_table(cls, presentation: dict[str, Any] | None) -> bool:
        if not isinstance(presentation, dict) or presentation.get("type") != "table":
            return False

        title = str(presentation.get("title") or "").strip().lower()

        if any(marker in title for marker in cls._structure_table_title_markers()):
            return True

        columns = presentation.get("columns") or []
        keys = {
            str(column.get("key") or "").strip().lower()
            for column in columns
            if isinstance(column, dict)
        }

        if {"parent_code", "component_code"}.issubset(keys):
            return True

        if {"level", "component_code"}.issubset(keys):
            return True

        if {"level", "product_code"}.issubset(keys) and (
            "exclusive_raw_material_label" in keys
            or "exclusive_raw_material" in keys
            or "component_type" in keys
        ):
            return True

        return False

    @classmethod
    def is_parents_usage_table(cls, presentation: dict[str, Any] | None) -> bool:
        if not isinstance(presentation, dict) or presentation.get("type") != "table":
            return False

        title = str(presentation.get("title") or "").strip().lower()

        return any(marker in title for marker in cls._parents_table_title_markers())

    @classmethod
    def is_hierarchy_duplicate_table(cls, presentation: dict[str, Any] | None) -> bool:
        return cls.is_structure_components_table(presentation) or cls.is_parents_usage_table(
            presentation
        )

    @classmethod
    def metadata_has_tree(cls, metadata: dict[str, Any]) -> bool:
        for key in ("treePresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "tree":
                return True

        return False

    @classmethod
    def _clear_table_slot(cls, metadata: dict[str, Any], key: str) -> None:
        presentation = metadata.get(key)

        if cls.is_hierarchy_duplicate_table(presentation):
            metadata[key] = None

    @classmethod
    def _filter_table_list(cls, tables: list[Any]) -> list[dict[str, Any]]:
        filtered: list[dict[str, Any]] = []

        for item in tables:
            if not isinstance(item, dict) or item.get("type") != "table":
                continue

            if cls.is_hierarchy_duplicate_table(item):
                continue

            filtered.append(item)

        return filtered

    @classmethod
    def count_non_duplicate_tables(cls, metadata: dict[str, Any]) -> int:
        count = 0
        bundled = metadata.get("tablePresentations")

        if isinstance(bundled, list):
            count += len(cls._filter_table_list(bundled))

        for key in (
            "tablePresentation",
            "profileTablePresentation",
            "inspectionTablePresentation",
        ):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "table":
                if not cls.is_hierarchy_duplicate_table(presentation):
                    count += 1

        primary = metadata.get("presentation")

        if isinstance(primary, dict) and primary.get("type") == "table":
            if not cls.is_hierarchy_duplicate_table(primary):
                count += 1

        return count

    @classmethod
    def _any_hierarchy_duplicate_table(cls, metadata: dict[str, Any]) -> bool:
        for key in (
            "tablePresentation",
            "profileTablePresentation",
            "inspectionTablePresentation",
            "presentation",
        ):
            if cls.is_hierarchy_duplicate_table(metadata.get(key)):
                return True

        bundled = metadata.get("tablePresentations")

        if isinstance(bundled, list):
            return any(cls.is_hierarchy_duplicate_table(item) for item in bundled)

        return False

    @classmethod
    def _first_hierarchy_duplicate_table(cls, metadata: dict[str, Any]) -> dict[str, Any] | None:
        for key in ("tablePresentation", "presentation"):
            presentation = metadata.get(key)

            if cls.is_hierarchy_duplicate_table(presentation):
                return presentation

        bundled = metadata.get("tablePresentations")

        if isinstance(bundled, list):
            for item in bundled:
                if cls.is_hierarchy_duplicate_table(item):
                    return item

        return None

    @classmethod
    def _suppress_tree_presentations(cls, metadata: dict[str, Any]) -> None:
        for key in ("treePresentation", "presentation"):
            presentation = metadata.get(key)

            if isinstance(presentation, dict) and presentation.get("type") == "tree":
                metadata[key] = None

    @classmethod
    def _explicit_table_session(cls, metadata: dict[str, Any]) -> bool:
        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower()

        return explicit == "table"

    @classmethod
    def _prefers_table_over_tree(cls, metadata: dict[str, Any]) -> bool:
        if cls._explicit_table_session(metadata):
            return True

        preferred = str(metadata.get("preferredFormat") or "").strip().lower()

        if preferred == "table":
            return True

        return False

    @classmethod
    def _should_preserve_tree_for_rich_stack(cls, metadata: dict[str, Any]) -> bool:
        if not cls.metadata_has_tree(metadata):
            return False

        from app.domain.services.chat_presentation_rich_stack_policy_service import (
            ChatPresentationRichStackPolicyService,
        )

        path = str(metadata.get("path") or "").strip() or None
        entity = None
        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            raw_entity = api_meta.get("entity")

            if isinstance(raw_entity, str) and raw_entity.strip():
                entity = raw_entity.strip()

        explicit = str(metadata.get("explicitSessionFormat") or "").strip().lower() or None

        if not ChatPresentationRichStackPolicyService.has_rich_text_narrative(metadata):
            return False

        return ChatPresentationRichStackPolicyService.count_auxiliary_visuals(metadata) >= 1 or bool(
            path
            and ChatPresentationRichStackPolicyService.is_rich_playbook_route(path, entity=entity)
        )

    @classmethod
    def _normalize_auxiliary_table_slots(cls, metadata: dict[str, Any]) -> None:
        bundled = metadata.get("tablePresentations")

        if not isinstance(bundled, list) or not bundled:
            return

        signatures = {
            cls._table_signature(item)
            for item in bundled
            if isinstance(item, dict) and item.get("type") == "table"
        }

        # Só `tablePresentation` — slots nomeados (profile/inspection) referenciam
        # tabelas do bundle de propósito (Playbook 12 R3 / stack por role).
        for key in ("tablePresentation",):
            presentation = metadata.get(key)

            if not isinstance(presentation, dict) or presentation.get("type") != "table":
                continue

            if cls._table_signature(presentation) in signatures:
                metadata[key] = None

    @classmethod
    def _table_signature(cls, presentation: dict[str, Any]) -> str:
        title = str(presentation.get("title") or "").strip().lower()
        columns = presentation.get("columns") or []
        keys = "|".join(
            str(column.get("key") or "").strip().lower()
            for column in columns
            if isinstance(column, dict)
        )
        rows = presentation.get("rows") or []
        row_count = len(rows) if isinstance(rows, list) else 0

        return f"{title}::{keys}::{row_count}"

    @classmethod
    def _is_summary_profile_table(cls, presentation: dict[str, Any] | None) -> bool:
        if not isinstance(presentation, dict) or presentation.get("type") != "table":
            return False

        if str(presentation.get("role") or "").strip().lower() == "profile":
            return True

        columns = presentation.get("columns") or []
        keys = {
            str(column.get("key") or "").strip().lower()
            for column in columns
            if isinstance(column, dict)
        }

        return keys.issubset({"campo", "valor", "field", "value"}) and bool(keys)

    @classmethod
    def _resolve_dashboard_presentation(
        cls,
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        for key in ("dashboardPresentation", "presentation"):
            presentation = metadata.get(key)

            if (
                isinstance(presentation, dict)
                and str(presentation.get("type") or "").strip().lower() == "dashboard"
            ):
                return presentation

        return None

    @classmethod
    def _metadata_has_dashboard(cls, metadata: dict[str, Any]) -> bool:
        return cls._resolve_dashboard_presentation(metadata) is not None

    @classmethod
    def _dashboard_embeds_kpi(cls, metadata: dict[str, Any]) -> bool:
        dashboard = cls._resolve_dashboard_presentation(metadata)

        if not isinstance(dashboard, dict):
            return False

        panels = dashboard.get("panels")

        if not isinstance(panels, list):
            return False

        return any(
            isinstance(panel, dict)
            and isinstance(panel.get("presentation"), dict)
            and str(panel["presentation"].get("type") or "").strip().lower() == "kpi"
            for panel in panels
        )

    @classmethod
    def _should_suppress_summary_profile_table(cls, metadata: dict[str, Any]) -> bool:
        from app.domain.services.chat_presentation_profile_service import (
            ChatPresentationProfileService,
        )

        path = str(metadata.get("path") or "").strip() or None
        entity = None
        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            raw_entity = api_meta.get("entity")

            if isinstance(raw_entity, str) and raw_entity.strip():
                entity = raw_entity.strip()

        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        tail_policy = str(profile.get("stackTailPolicy") or "").strip().lower()

        if tail_policy != "dashboard_only":
            return False

        return cls._dashboard_embeds_kpi(metadata)

    @classmethod
    def _suppress_redundant_summary_profile_tables(cls, metadata: dict[str, Any]) -> None:
        if not cls._should_suppress_summary_profile_table(metadata):
            return

        bundled = metadata.get("tablePresentations")

        if isinstance(bundled, list):
            filtered = [
                item
                for item in bundled
                if not (
                    isinstance(item, dict)
                    and cls._is_summary_profile_table(item)
                )
            ]
            metadata["tablePresentations"] = filtered or None

        profile_table = metadata.get("profileTablePresentation")

        if cls._is_summary_profile_table(profile_table):
            metadata["profileTablePresentation"] = None

        presentation = metadata.get("presentation")

        if cls._is_summary_profile_table(presentation):
            metadata["presentation"] = None

    @classmethod
    def dedupe_metadata(cls, metadata: dict[str, Any]) -> None:
        """Árvore e tabela plana da mesma hierarquia não coexistem na mesma resposta."""
        if not isinstance(metadata, dict):
            return

        cls._normalize_auxiliary_table_slots(metadata)
        cls._suppress_redundant_summary_profile_tables(metadata)

        if (
            not cls._explicit_table_session(metadata)
            and cls.metadata_has_tree(metadata)
            and (
                cls._should_preserve_tree_for_rich_stack(metadata)
                or not cls._prefers_table_over_tree(metadata)
            )
        ):
            primary = metadata.get("presentation")

            if cls.is_hierarchy_duplicate_table(primary) and not cls._prefers_table_over_tree(
                metadata
            ):
                metadata["presentation"] = metadata.get("treePresentation") or None

            cls._clear_table_slot(metadata, "tablePresentation")

            bundled = metadata.get("tablePresentations")

            if isinstance(bundled, list):
                filtered = cls._filter_table_list(bundled)
                metadata["tablePresentations"] = filtered or None

            available = metadata.get("availableFormats")

            if isinstance(available, list) and cls.count_non_duplicate_tables(metadata) == 0:
                metadata["availableFormats"] = [
                    token
                    for token in available
                    if str(token).strip().lower() != "table"
                ]

            decision = metadata.get("presentationDecision")

            if isinstance(decision, dict):
                views = decision.get("availableViews")

                if isinstance(views, list):
                    decision["availableViews"] = cls.prune_available_views(views, metadata)

            metadata["structureDedupApplied"] = True
            return

        if cls._prefers_table_over_tree(metadata) and cls._any_hierarchy_duplicate_table(metadata):
            structure_table = cls._first_hierarchy_duplicate_table(metadata)

            if cls._explicit_table_session(metadata) or not cls._should_preserve_tree_for_rich_stack(
                metadata
            ):
                cls._suppress_tree_presentations(metadata)

            if structure_table is not None:
                metadata["presentation"] = structure_table
                metadata["tablePresentation"] = None

            available = metadata.get("availableFormats")

            if isinstance(available, list):
                metadata["availableFormats"] = [
                    token
                    for token in available
                    if str(token).strip().lower() != "tree"
                ]

        metadata["structureDedupApplied"] = True

    @classmethod
    def prune_available_views(cls, views: list[str], metadata: dict[str, Any]) -> list[str]:
        if cls.metadata_has_tree(metadata) and cls.count_non_duplicate_tables(metadata) == 0:
            return [view for view in views if str(view).strip().lower() != "table"]

        return views
