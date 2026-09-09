"""Vocabulário PT de constraints de apresentação — ``presentation_constraints_vocabulary.json``."""

from __future__ import annotations

from app.domain.services.chat_assistant_vocabulary_service import (
    ChatAssistantVocabularyService,
)


class PresentationConstraintsVocabularyService(ChatAssistantVocabularyService):
    BUNDLE = "presentation_constraints_vocabulary"

    @classmethod
    def density_terms(cls, density: str) -> tuple[str, ...]:
        return cls.terms("density", density)

    @classmethod
    def prefer_canvas_terms(cls) -> tuple[str, ...]:
        return cls.terms("preferCanvas")

    @classmethod
    def dashboard_terms(cls) -> tuple[str, ...]:
        return cls.terms("dashboardPanels")

    @classmethod
    def column_count_markers(cls) -> tuple[str, ...]:
        return cls.terms("columnCount", "markers")

    @classmethod
    def column_count_max(cls) -> int:
        raw = cls.node("columnCount", "maxColumns")
        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 12

    @classmethod
    def kpi_markers(cls) -> tuple[str, ...]:
        return cls.terms("kpiMeasures", "markers")

    @classmethod
    def kpi_top_placement_terms(cls) -> tuple[str, ...]:
        return cls.terms("kpiMeasures", "topPlacement")

    @classmethod
    def kpi_max_count(cls) -> int:
        raw = cls.node("kpiMeasures", "maxCount")
        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return 8

    @classmethod
    def sort_asc_terms(cls) -> tuple[str, ...]:
        return cls.terms("sort", "ascMarkers")

    @classmethod
    def sort_desc_terms(cls) -> tuple[str, ...]:
        return cls.terms("sort", "descMarkers")

    @classmethod
    def sort_command_terms(cls) -> tuple[str, ...]:
        return cls.terms("sort", "commandMarkers")

    @classmethod
    def hidden_field_markers(cls) -> tuple[str, ...]:
        return cls.terms("hiddenFields", "markers")

    @classmethod
    def fields_only_markers(cls) -> tuple[str, ...]:
        return cls.terms("fields", "onlyMarkers")

    @classmethod
    def fields_paren_pattern(cls) -> str:
        raw = cls.node("fields", "parenPattern")
        return str(raw or r"\(([\w\s,à-ú/-]+)\)")

    @classmethod
    def emphasis_terms(cls, emphasis: str) -> tuple[str, ...]:
        return cls.terms("emphasis", emphasis)
