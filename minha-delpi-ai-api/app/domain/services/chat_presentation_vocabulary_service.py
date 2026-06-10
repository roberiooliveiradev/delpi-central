"""Vocabulário PT de heurísticas de apresentação — bundle ``presentation_vocabulary.json``."""

from __future__ import annotations

import re
from functools import lru_cache

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
    def route_policy_reason(cls, key: str, *, default: str = "") -> str:
        return cls.text("routePolicyReasons", key, default=default)

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
