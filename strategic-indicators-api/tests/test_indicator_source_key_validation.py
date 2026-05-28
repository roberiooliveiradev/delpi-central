from __future__ import annotations

import pytest

from si_app.application.services.strategic_indicators.indicator_source_key_validation import (
    normalize_indicator_source_key,
    validate_indicator_source_key,
)


def test_active_indicator_requires_source_key() -> None:
    with pytest.raises(ValueError, match="source_key é obrigatório"):
        validate_indicator_source_key(None, is_active=True)

    with pytest.raises(ValueError, match="source_key é obrigatório"):
        validate_indicator_source_key("   ", is_active=True)


def test_inactive_indicator_allows_empty_source_key() -> None:
    validate_indicator_source_key(None, is_active=False)
    validate_indicator_source_key("", is_active=False)


def test_source_key_pattern() -> None:
    validate_indicator_source_key("commercial_rol", is_active=True)
    validate_indicator_source_key("production_otd", is_active=True)

    with pytest.raises(ValueError, match="source_key inválido"):
        validate_indicator_source_key("Commercial-Rol", is_active=True)


def test_normalize_indicator_source_key() -> None:
    assert normalize_indicator_source_key("  commercial_rol  ") == "commercial_rol"
    assert normalize_indicator_source_key("") is None
