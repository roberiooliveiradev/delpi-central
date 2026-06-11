"""Vocabulário PT de heurísticas de apresentação — bundle ``presentation_vocabulary.json``."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

from app.domain.services.chat_assistant_vocabulary_service import ChatAssistantVocabularyService


class ChatPresentationVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "presentation_vocabulary"

    @classmethod
    def structure_table_title_markers(cls) -> tuple[str, ...]:
        return cls.terms("structureDedup", "structureTableTitleMarkers")

    @classmethod
    def parents_table_title_markers(cls) -> tuple[str, ...]:
        return cls.terms("structureDedup", "parentsTableTitleMarkers")

    @classmethod
    def table_title_tokens(cls, key: str) -> tuple[str, ...]:
        return cls.terms("sectionAvailability", "tableTitleTokens", key)

    @classmethod
    def profile_table_title_prefixes(cls) -> tuple[str, ...]:
        return cls.terms("sectionAvailability", "profileTableTitlePrefixes")

    @classmethod
    def profile_table_title_tokens(cls) -> tuple[str, ...]:
        return cls.terms("sectionAvailability", "profileTableTitleTokens")

    @classmethod
    def boolean_label(cls, *, yes: bool) -> str:
        path = ("booleanLabels", "yes") if yes else ("booleanLabels", "no")

        return cls.text(*path, default="Sim" if yes else "Não")

    @classmethod
    def exclusive_raw_material_truthy(cls) -> frozenset[str]:
        return frozenset(token.upper() for token in cls.terms("exclusiveRawMaterialTruthy"))

    @classmethod
    def hierarchy_tree_text(cls, key: str, *, default: str = "") -> str:
        return cls.text("hierarchyTree", key, default=default)

    @classmethod
    def hierarchy_tree_terms(cls, *path: str) -> tuple[str, ...]:
        return cls.terms("hierarchyTree", *path)

    @classmethod
    def hierarchy_group_badge_label(cls, group_key: str) -> str:
        token = str(group_key or "").strip().lower()

        return cls.text("hierarchyTree", "groupBadgeLabels", token, default="")

    @classmethod
    def hierarchy_group_node_label(cls, group_key: str, value: str) -> str:
        token = str(group_key or "").strip().lower()
        bucket = str(value or "").strip() or cls.hierarchy_tree_text("emptyLabel", default="—")
        template = cls.text("hierarchyTree", "groupNodeLabels", token, default="")

        if template and "{value}" in template:
            return template.replace("{value}", bucket)

        return bucket

    @classmethod
    @lru_cache(maxsize=1)
    def absence_insight_pattern(cls) -> re.Pattern[str]:
        pattern = cls.text(
            "sectionAvailability",
            "absenceInsightPattern",
            default="",
        )

        if not pattern:
            return re.compile(r"$^")

        return re.compile(pattern, re.IGNORECASE)

    @classmethod
    def intent_markers(cls, key: str) -> tuple[str, ...]:
        return cls.terms("intentMarkers", key)

    @classmethod
    def format_preference_markers(cls, key: str) -> tuple[str, ...]:
        return cls.terms("formatPreferenceMarkers", key)

    @classmethod
    def decision_reason(cls, key: str, *, default: str = "") -> str:
        return cls.text("decisionReasons", key, default=default)

    @classmethod
    def purpose_default(cls, view: str, *, default: str = "") -> str:
        token = str(view or "").strip().lower()

        return cls.text("purposeDefaults", token, default=default)

    @classmethod
    def route_policy_reason(cls, key: str, *, default: str = "") -> str:
        return cls.text("routePolicyReasons", key, default=default)

    @classmethod
    def operational_decision_markers(cls, group_key: str) -> tuple[str, ...]:
        return cls.terms("operationalDecision", group_key)

    @classmethod
    def insight_text(cls, key: str, *, default: str = "", **values: str) -> str:
        return cls.text("insights", key, default=default, **values)

    @classmethod
    def insight_table_line_unit(cls, count: int) -> str:
        path = "tableLineUnitOne" if count == 1 else "tableLineUnitMany"

        return cls.text("insights", path, default="linha" if count == 1 else "linhas")

    @classmethod
    def chart_type_label(cls, chart_type: str) -> str:
        labels = cls.mapping("chartExplain", "typeLabels")

        return labels.get(str(chart_type or "").strip().lower()) or cls.text(
            "chartExplain",
            "defaultChartLabel",
            default="gráfico",
        )

    @classmethod
    def chart_explain_text(cls, key: str, *, default: str = "", **values: str | int | float) -> str:
        normalized = {
            name: str(value)
            for name, value in values.items()
        }

        return cls.text("chartExplain", key, default=default, **normalized)

    @classmethod
    def dashboard_explain_text(cls, key: str, *, default: str = "", **values: str | int) -> str:
        normalized = {
            name: str(value)
            for name, value in values.items()
        }

        return cls.text("dashboardExplain", key, default=default, **normalized)

    @classmethod
    def playbook12_audit_files(cls) -> tuple[str, ...]:
        return cls.terms("playbook12Refactor", "auditFiles")

    @classmethod
    def playbook12_tier_a_profile_keys(cls) -> tuple[str, ...]:
        return cls.terms("playbook12Refactor", "tierAProfileKeys")

    @classmethod
    def playbook12_table_assembly_path_fragments(cls) -> frozenset[str]:
        return frozenset(cls.terms("playbook12Refactor", "tableAssemblyPathFragments"))

    @classmethod
    def playbook12_targets(cls) -> dict[str, int]:
        raw = cls.node("playbook12Refactor", "targets")

        if not isinstance(raw, dict):
            return {}

        return {
            str(key): int(value)
            for key, value in raw.items()
            if isinstance(value, (int, float))
        }

    @classmethod
    @lru_cache(maxsize=16)
    def playbook12_scan_pattern(cls, key: str) -> re.Pattern[str]:
        pattern = cls.text("playbook12Refactor", "scanPatterns", key, default="")

        if not pattern:
            return re.compile(r"$^")

        return re.compile(pattern)

    @classmethod
    def playbook12_tier_a_pipeline_cases(cls) -> tuple[dict[str, Any], ...]:
        raw = cls.node("playbook12Refactor", "tierAPipelineCases")

        if not isinstance(raw, list):
            return ()

        cases: list[dict[str, Any]] = []

        for item in raw:
            if isinstance(item, dict) and item.get("id"):
                cases.append(dict(item))

        return tuple(cases)

    @classmethod
    def presentation_title_policies(cls) -> tuple[dict[str, Any], ...]:
        raw = cls.node("playbook12Refactor", "presentationTitlePolicies")

        if not isinstance(raw, list):
            return ()

        return tuple(item for item in raw if isinstance(item, dict))

    @classmethod
    def table_role_default(cls) -> str:
        return cls.text("tableRoles", "defaultRole", default="other")

    @classmethod
    def table_role_allowed_roles(cls) -> tuple[str, ...]:
        return cls.terms("tableRoles", "allowedRoles")

    @classmethod
    def table_role_metadata_presentation_roles(cls) -> dict[str, str]:
        raw = cls.node("tableRoles", "metadataPresentationRoles")

        if not isinstance(raw, dict):
            return {}

        return {
            str(key): str(value)
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def table_role_title_token_group_priority(cls) -> tuple[str, ...]:
        return cls.terms("tableRoles", "titleTokenGroupPriority")

    @classmethod
    def table_role_for_title_token_group(cls, group_key: str) -> str:
        mapping = cls.mapping("tableRoles", "titleTokenGroupRoles")

        return str(mapping.get(str(group_key or "").strip()) or "").strip()

    @classmethod
    def table_role_global_match_order(cls) -> tuple[str, ...]:
        return cls.terms("tableRoles", "globalTitleMatchOrder")

    @classmethod
    def table_role_global_tokens(cls, role_key: str) -> tuple[str, ...]:
        return cls.terms("tableRoles", "globalTitleTokens", str(role_key or "").strip())

    @classmethod
    def table_role_profile_title_token_groups(cls, profile_key: str) -> tuple[str, ...]:
        return cls.terms(
            "tableRoles",
            "profileTitleTokenGroups",
            str(profile_key or "").strip(),
        )

    @classmethod
    def legacy_fallbacks_inventory_baseline(cls) -> dict[str, Any]:
        raw = cls.node("legacyFallbacks", "inventoryBaseline")

        return dict(raw) if isinstance(raw, dict) else {}

    @classmethod
    def legacy_fallbacks_allowed_path_include_modules(cls) -> tuple[str, ...]:
        return cls.terms("legacyFallbacks", "allowedPathIncludesModules")
