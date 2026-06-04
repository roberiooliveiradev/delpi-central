"""Evita o mesmo conteúdo de estrutura/BOM em árvore e tabela na mesma resposta."""

from __future__ import annotations

from typing import Any


class ChatPresentationStructureDedupService:
    _STRUCTURE_TABLE_TITLE_MARKERS = (
        "componentes da estrutura",
    )
    _PARENTS_TABLE_TITLE_MARKERS = (
        "produtos pai",
        "onde é usado",
    )

    @classmethod
    def is_structure_components_table(cls, presentation: dict[str, Any] | None) -> bool:
        if not isinstance(presentation, dict) or presentation.get("type") != "table":
            return False

        title = str(presentation.get("title") or "").strip().lower()

        if any(marker in title for marker in cls._STRUCTURE_TABLE_TITLE_MARKERS):
            return True

        columns = presentation.get("columns") or []
        keys = {
            str(column.get("key") or "").strip().lower()
            for column in columns
            if isinstance(column, dict)
        }

        return {"parent_code", "component_code"}.issubset(keys)

    @classmethod
    def is_parents_usage_table(cls, presentation: dict[str, Any] | None) -> bool:
        if not isinstance(presentation, dict) or presentation.get("type") != "table":
            return False

        title = str(presentation.get("title") or "").strip().lower()

        return any(marker in title for marker in cls._PARENTS_TABLE_TITLE_MARKERS)

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
    def _prefers_table_over_tree(cls, metadata: dict[str, Any]) -> bool:
        preferred = str(metadata.get("preferredFormat") or "").strip().lower()

        return preferred == "table"

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

        for key in ("profileTablePresentation", "inspectionTablePresentation", "tablePresentation"):
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
    def dedupe_metadata(cls, metadata: dict[str, Any]) -> None:
        """Árvore e tabela plana da mesma hierarquia não coexistem na mesma resposta."""
        if not isinstance(metadata, dict):
            return

        cls._normalize_auxiliary_table_slots(metadata)

        if cls._prefers_table_over_tree(metadata) and cls._any_hierarchy_duplicate_table(metadata):
            structure_table = cls._first_hierarchy_duplicate_table(metadata)
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

            return

        if not cls.metadata_has_tree(metadata):
            return

        primary = metadata.get("presentation")

        if cls.is_hierarchy_duplicate_table(primary):
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

    @classmethod
    def prune_available_views(cls, views: list[str], metadata: dict[str, Any]) -> list[str]:
        if cls.metadata_has_tree(metadata) and cls.count_non_duplicate_tables(metadata) == 0:
            return [view for view in views if str(view).strip().lower() != "table"]

        return views
