"""Montagem declarativa de tablePresentations — Playbook 12 R3."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_route_policy_service import (
    ChatPresentationRoutePolicyService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

TableBuilderFn = Callable[["ExternalActionResultPresenter", dict[str, Any], str], list[dict[str, Any]]]


@dataclass(frozen=True)
class TableAssemblyResult:
    table_presentations: list[dict[str, Any]]
    table_presentation: dict[str, Any] | None
    profile_table_presentation: dict[str, Any] | None
    inspection_table_presentation: dict[str, Any] | None


class ChatPresentationTableAssemblyService:
    @classmethod
    def builder_registry(
        cls,
        presenter: ExternalActionResultPresenter,
    ) -> dict[str, TableBuilderFn]:
        return {
            "build_analyser_auxiliary_table_presentations": cls._build_analyser_tables,
            "build_stock_table_presentations": lambda p, root, path: p.build_stock_table_presentations(root, path),
            "build_factory_status_table_presentations": lambda p, root, path: p.build_factory_status_table_presentations(root, path),
            "build_production_status_table_presentations": lambda p, root, path: p.build_production_status_table_presentations(root, path),
            "build_shipping_status_table_presentations": lambda p, root, path: p.build_shipping_status_table_presentations(root, path),
            "build_structure_exclusivity_table_presentations": lambda p, root, path: p.build_structure_exclusivity_table_presentations(root, path),
            "build_raw_material_price_intelligence_table_presentations": lambda p, root, path: p.build_raw_material_price_intelligence_table_presentations(root, path),
            "build_cost_impact_simulation_table_presentations": lambda p, root, path: p.build_cost_impact_simulation_table_presentations(root, path),
            "build_product_pricing_table_presentations": lambda p, root, path: p.build_product_pricing_table_presentations(root, path),
            "build_last_purchase_table_presentations": lambda p, root, path: p.build_last_purchase_table_presentations(root, path),
            "build_purchase_history_table_presentations": lambda p, root, path: p.build_purchase_history_table_presentations(root, path),
            "build_product_directives_table_presentations": (
                lambda p, root, path: p.build_product_directives_table_presentations(root, path)
            ),
            "build_tree_hierarchy_table_presentations": cls._build_tree_hierarchy_tables,
        }

    @staticmethod
    def _build_tree_hierarchy_tables(
        presenter: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
    ) -> list[dict[str, Any]]:
        del path

        table = presenter._build_analyser_structure_components_table(root)

        if isinstance(table, dict) and table.get("type") == "table":
            return [table]

        return []

    @staticmethod
    def _build_analyser_tables(
        presenter: ExternalActionResultPresenter,
        root: dict[str, Any],
        path: str,
    ) -> list[dict[str, Any]]:
        del path

        return presenter.build_analyser_auxiliary_table_presentations(root)

    @classmethod
    def table_assembly_config(cls, profile: dict[str, Any]) -> dict[str, Any]:
        raw = profile.get("tableAssembly")

        return dict(raw) if isinstance(raw, dict) else {}

    @classmethod
    def should_skip_assembly(cls, root: dict[str, Any], config: dict[str, Any]) -> bool:
        if config.get("requiresProduct") is True and not isinstance(root.get("product"), dict):
            return True

        if config.get("requiresItems") is True:
            items = root.get("items")

            return not isinstance(items, list) or not items

        return False

    @classmethod
    def assemble(
        cls,
        presenter: ExternalActionResultPresenter,
        root_payload: dict[str, Any] | None,
        path: str,
        *,
        profile: dict[str, Any] | None = None,
        entity: str | None = None,
        table_presentation: dict[str, Any] | None = None,
        tree_presentation: dict[str, Any] | None = None,
        session_format: str = "",
    ) -> TableAssemblyResult:
        empty = TableAssemblyResult([], table_presentation, None, None)

        if not isinstance(root_payload, dict):
            return empty

        resolved_profile = profile or ChatPresentationProfileService.resolve_profile(path, entity)
        config = cls.table_assembly_config(resolved_profile)

        if not config:
            resolved_table = cls.apply_session_tree_table_fallback(
                presenter,
                root_payload,
                path,
                table_presentation=table_presentation,
                tree_presentation=tree_presentation,
                session_format=session_format,
            )
            return TableAssemblyResult([], resolved_table, None, None)

        if cls.should_skip_assembly(root_payload, config):
            return empty

        builder_name = str(config.get("builder") or "").strip()
        builder = cls.builder_registry(presenter).get(builder_name)

        if not builder:
            return empty

        tables = [table for table in builder(presenter, root_payload, path) if isinstance(table, dict)]

        if builder_name == "build_structure_exclusivity_table_presentations":
            normalized_format = str(session_format or "").strip().lower()

            if normalized_format == "text":
                embed_tables = presenter.build_structure_exclusivity_text_embed_table_presentations(
                    root_payload,
                    path,
                )
                tables.extend(
                    table for table in embed_tables if isinstance(table, dict)
                )

        if not tables:
            return empty

        layout = str(config.get("layout") or "profile_primary").strip().lower()

        if layout == "analyser_slots":
            result = cls._layout_analyser_slots(tables, table_presentation=table_presentation)
        elif layout == "profile_only":
            result = cls._layout_profile_only(tables)
        elif layout == "single_table":
            result = cls._layout_single_table(tables)
        else:
            profile_index = int(config.get("profileTableIndex", 0))
            primary_index = int(config.get("primaryTableIndex", 1))
            result = cls._layout_profile_primary(
                tables,
                profile_table_index=profile_index,
                primary_table_index=primary_index,
            )

        resolved_table = cls.apply_session_tree_table_fallback(
            presenter,
            root_payload,
            path,
            table_presentation=result.table_presentation,
            tree_presentation=tree_presentation,
            session_format=session_format,
        )

        return TableAssemblyResult(
            table_presentations=result.table_presentations,
            table_presentation=resolved_table,
            profile_table_presentation=result.profile_table_presentation,
            inspection_table_presentation=result.inspection_table_presentation,
        )

    @classmethod
    def _layout_profile_primary(
        cls,
        tables: list[dict[str, Any]],
        *,
        profile_table_index: int,
        primary_table_index: int,
    ) -> TableAssemblyResult:
        profile_table = tables[profile_table_index] if len(tables) > profile_table_index else None
        primary_table = None

        if len(tables) > primary_table_index:
            primary_table = tables[primary_table_index]
        elif tables:
            primary_table = tables[0]

        return TableAssemblyResult(
            table_presentations=tables,
            table_presentation=primary_table,
            profile_table_presentation=profile_table,
            inspection_table_presentation=None,
        )

    @classmethod
    def _layout_profile_only(cls, tables: list[dict[str, Any]]) -> TableAssemblyResult:
        primary = tables[0]

        return TableAssemblyResult(
            table_presentations=tables,
            table_presentation=primary,
            profile_table_presentation=primary,
            inspection_table_presentation=None,
        )

    @classmethod
    def _layout_single_table(cls, tables: list[dict[str, Any]]) -> TableAssemblyResult:
        primary = tables[0]

        return TableAssemblyResult(
            table_presentations=tables,
            table_presentation=primary,
            profile_table_presentation=None,
            inspection_table_presentation=None,
        )

    @classmethod
    def _layout_analyser_slots(
        cls,
        tables: list[dict[str, Any]],
        *,
        table_presentation: dict[str, Any] | None,
    ) -> TableAssemblyResult:
        profile_table = None
        inspection_table = None
        primary_table = table_presentation

        for candidate in tables:
            title = str(candidate.get("title") or "")
            title_lower = title.lower()

            if cls._matches_profile_prefix(title_lower):
                profile_table = candidate
                continue

            if cls._matches_token_group(title_lower, "analyserInspection"):
                inspection_table = candidate
                continue

            if cls._matches_token_group(title_lower, "analyserGuide") and primary_table is None:
                primary_table = candidate

        if primary_table is None and tables:
            primary_table = tables[0]

        return TableAssemblyResult(
            table_presentations=tables,
            table_presentation=primary_table,
            profile_table_presentation=profile_table,
            inspection_table_presentation=inspection_table,
        )

    @classmethod
    def _matches_profile_prefix(cls, title_lower: str) -> bool:
        for prefix in ChatPresentationVocabularyService.profile_table_title_prefixes():
            prefix_token = str(prefix or "").strip().lower()

            if prefix_token and title_lower.startswith(prefix_token):
                return True

        return False

    @classmethod
    def _matches_token_group(cls, title_lower: str, group_key: str) -> bool:
        for token in ChatPresentationVocabularyService.table_title_tokens(group_key):
            token_value = str(token or "").strip().lower()

            if token_value and token_value in title_lower:
                return True

        return False

    @classmethod
    def apply_session_tree_table_fallback(
        cls,
        presenter: ExternalActionResultPresenter,
        root_payload: dict[str, Any],
        path: str,
        *,
        table_presentation: dict[str, Any] | None,
        tree_presentation: dict[str, Any] | None,
        session_format: str,
    ) -> dict[str, Any] | None:
        if table_presentation is not None:
            return table_presentation

        if str(session_format or "").strip().lower() != "table":
            return None

        if not tree_presentation:
            return None

        if not ChatPresentationRoutePolicyService.is_tree_route(path):
            return None

        structure_table = presenter._build_analyser_structure_components_table(root_payload)

        if isinstance(structure_table, dict):
            return structure_table

        return None

    @classmethod
    def try_build_presentation_table(
        cls,
        presenter: ExternalActionResultPresenter,
        root_payload: dict[str, Any],
        path: str,
        *,
        entity: str | None = None,
    ) -> dict[str, Any] | None:
        """Primeira tabela para slot ``presentation`` — declarativo via ``tableAssembly``."""
        profile = ChatPresentationProfileService.resolve_profile(path, entity)
        config = cls.table_assembly_config(profile)
        builder_name = str(config.get("builder") or "").strip()

        if not builder_name:
            return None

        builder = cls.builder_registry(presenter).get(builder_name)

        if not callable(builder):
            return None

        tables = [
            table for table in builder(presenter, root_payload, path) if isinstance(table, dict)
        ]

        if tables:
            return tables[0]

        raw_fallback = config.get("presentationFallback")

        if raw_fallback is None:
            return None

        fallback = str(raw_fallback).strip().lower()

        if fallback == "legacy_factory_table":
            return presenter._build_factory_status_table(root_payload, path)

        if fallback == "playbook_report":
            return presenter._build_playbook_report_table(root_payload, path, entity=entity)

        return None
