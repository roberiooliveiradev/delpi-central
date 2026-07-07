from app.domain.services.kaizen.kaizen_categories import (
    categories_from_row,
    normalize_categories,
)


def test_normalize_categories_deduplicates_and_limits_length():
    result = normalize_categories([" Ergonomia ", "ergonomia", "Qualidade"])
    assert result == ["Ergonomia", "Qualidade"]


def test_normalize_categories_falls_back_to_legacy_category():
    assert normalize_categories(None, legacy_category="5S") == ["5S"]


def test_categories_from_row_prefers_array():
    row = {"categories": ["Segurança"], "category": "Ergonomia"}
    assert categories_from_row(row) == ["Segurança"]
