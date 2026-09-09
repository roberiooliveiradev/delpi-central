"""Extrai PresentationConstraints da mensagem do usuário (vocabulário declarativo)."""

from __future__ import annotations

import re
from typing import Any

from app.domain.services.presentation_constraints_vocabulary_service import (
    PresentationConstraintsVocabularyService,
)


class PresentationConstraintsExtractorService:
    """Restrições transversais de apresentação — sem regex acoplada a path/rota."""

    @classmethod
    def extract(cls, message: str | None) -> dict[str, Any]:
        text = cls._normalize(message)
        if not text:
            return {}

        constraints: dict[str, Any] = {}

        density = cls._detect_density(text)
        if density:
            constraints["density"] = density

        column_count = cls._detect_column_count(text)
        if column_count is not None:
            constraints["columnCount"] = column_count

        fields = cls._detect_field_hints(text)
        if fields:
            constraints["fields"] = fields

        hidden = cls._detect_hidden_fields(text)
        if hidden:
            constraints["hiddenFields"] = hidden

        sort = cls._detect_sort(text)
        if sort:
            constraints["sort"] = sort

        emphasis = cls._detect_emphasis(text)
        if emphasis:
            constraints["emphasis"] = emphasis

        kpi_measures = cls._detect_kpi_measures(text)
        if kpi_measures:
            constraints["kpiMeasures"] = kpi_measures

        if cls._detect_dashboard(text):
            constraints["dashboardPanels"] = True

        if cls._detect_prefer_canvas(text):
            constraints["preferCanvas"] = True

        return constraints

    @classmethod
    def _normalize(cls, message: str | None) -> str:
        return re.sub(r"\s+", " ", str(message or "").strip().lower())

    @classmethod
    def _contains_any(cls, text: str, terms: tuple[str, ...]) -> bool:
        return any(term in text for term in terms if term)

    @classmethod
    def _detect_density(cls, text: str) -> str | None:
        for density in ("compact", "comfortable", "spacious"):
            if cls._contains_any(text, PresentationConstraintsVocabularyService.density_terms(density)):
                return density
        return None

    @classmethod
    def _detect_column_count(cls, text: str) -> int | None:
        max_columns = PresentationConstraintsVocabularyService.column_count_max()
        for marker in PresentationConstraintsVocabularyService.column_count_markers():
            pattern = marker.replace("{n}", r"(?P<count>\d{1,2})")
            match = re.search(pattern, text)
            if not match:
                continue
            try:
                count = int(match.group("count"))
            except (TypeError, ValueError):
                continue
            if 1 <= count <= max_columns:
                return count
        return None

    @classmethod
    def _detect_field_hints(cls, text: str) -> list[str]:
        hints: list[str] = []
        pattern = PresentationConstraintsVocabularyService.fields_paren_pattern()
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            chunk = str(match.group(1) or "").strip()
            if not chunk:
                continue
            for token in re.split(r"[,/]", chunk):
                cleaned = cls._clean_field_token(token)
                if cleaned and cleaned not in hints:
                    hints.append(cleaned)

        if hints:
            return hints

        if not cls._contains_any(
            text,
            PresentationConstraintsVocabularyService.fields_only_markers(),
        ):
            return []

        trailing = re.search(
            r"(?:só colunas|somente colunas|apenas colunas|só os campos|somente os campos|apenas os campos)\s+(.+?)(?:\.|,|$)",
            text,
        )
        if not trailing:
            return []

        for token in re.split(r"[,/]", trailing.group(1)):
            cleaned = cls._clean_field_token(token)
            if cleaned and cleaned not in hints:
                hints.append(cleaned)
        return hints

    @classmethod
    def _clean_field_token(cls, token: str) -> str:
        cleaned = re.sub(r"^\W+|\W+$", "", str(token or "").strip().lower())
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned

    @classmethod
    def _detect_hidden_fields(cls, text: str) -> list[str]:
        hidden: list[str] = []
        for marker in PresentationConstraintsVocabularyService.hidden_field_markers():
            idx = text.find(marker)
            if idx < 0:
                continue
            tail = text[idx + len(marker) :].strip()
            token = re.split(r"[,.;]| e ", tail, maxsplit=1)[0].strip()
            cleaned = cls._clean_field_token(token)
            if cleaned and cleaned not in hidden:
                hidden.append(cleaned)
        return hidden

    @classmethod
    def _detect_sort(cls, text: str) -> dict[str, str] | None:
        direction = None
        if cls._contains_any(text, PresentationConstraintsVocabularyService.sort_desc_terms()):
            direction = "desc"
        elif cls._contains_any(text, PresentationConstraintsVocabularyService.sort_asc_terms()):
            direction = "asc"

        field = None
        for marker in PresentationConstraintsVocabularyService.sort_command_terms():
            idx = text.find(marker)
            if idx < 0:
                continue
            tail = text[idx + len(marker) :].strip()
            token = re.split(r"[,.;]| do | da | de ", tail, maxsplit=1)[0].strip()
            cleaned = cls._clean_field_token(token)
            if cleaned:
                field = cleaned
                break

        if field is None and "ordene" in text:
            match = re.search(
                r"ordene(?:\s+do|\s+da|\s+de)?\s+(?:maior|menor)?\s*(?:para o)?\s*(?:maior|menor)?\s*(.+?)(?:\.|,|$)",
                text,
            )
            if match:
                cleaned = cls._clean_field_token(match.group(1))
                if cleaned:
                    field = cleaned

        if not field and not direction:
            return None

        payload: dict[str, str] = {}
        if field:
            payload["field"] = field
        if direction:
            payload["direction"] = direction
        return payload or None

    @classmethod
    def _detect_emphasis(cls, text: str) -> str | None:
        for emphasis in ("lowBalance", "highBalance"):
            if cls._contains_any(
                text,
                PresentationConstraintsVocabularyService.emphasis_terms(emphasis),
            ):
                return emphasis
        return None

    @classmethod
    def _detect_kpi_measures(cls, text: str) -> list[str] | None:
        measures: list[str] = []
        max_count = PresentationConstraintsVocabularyService.kpi_max_count()

        for marker in PresentationConstraintsVocabularyService.kpi_markers():
            if "{n}" in marker:
                pattern = marker.replace("{n}", r"(?P<count>\d{1,2})")
                match = re.search(pattern, text)
                if not match:
                    continue
                try:
                    count = int(match.group("count"))
                except (TypeError, ValueError):
                    continue
                if 1 <= count <= max_count:
                    measures.append(f"count:{count}")
            elif marker in text:
                measures.append("top")

        if cls._contains_any(
            text,
            PresentationConstraintsVocabularyService.kpi_top_placement_terms(),
        ) and "top" not in measures:
            measures.append("top")

        return measures or None

    @classmethod
    def _detect_dashboard(cls, text: str) -> bool:
        return cls._contains_any(text, PresentationConstraintsVocabularyService.dashboard_terms())

    @classmethod
    def _detect_prefer_canvas(cls, text: str) -> bool:
        return cls._contains_any(
            text,
            PresentationConstraintsVocabularyService.prefer_canvas_terms(),
        )
