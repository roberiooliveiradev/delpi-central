"""Testes da faixa válida de eficiência de produção (0–199%)."""

import pytest

from app.domain.production.production_efficiency_valid_range import (
    PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
    PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
    is_valid_production_efficiency_pct,
)
from app.infrastructure.persistence.totvs.eficiencia_fabril.eficiencia_fabril_query_settings import (
    EficienciaFabrilQuerySettings,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, True),
        (199, True),
        (100.5, True),
        (-0.1, False),
        (199.01, False),
        (250, False),
        (None, False),
        ("abc", False),
    ],
)
def test_is_valid_production_efficiency_pct(value, expected) -> None:
    assert is_valid_production_efficiency_pct(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (49.9, True),
        (50, False),
        (0, True),
        (199, False),
        (250, False),
        (None, False),
    ],
)
def test_is_low_production_efficiency_pct(value, expected) -> None:
    from app.domain.production.production_efficiency_valid_range import (
        is_low_production_efficiency_pct,
    )

    assert is_low_production_efficiency_pct(value) is expected


def test_eficiencia_fabril_settings_use_shared_range() -> None:
    settings = EficienciaFabrilQuerySettings()
    assert settings.min_efficiency_indicator_pct == PRODUCTION_EFFICIENCY_VALID_MIN_PCT
    assert settings.max_efficiency_indicator_pct == PRODUCTION_EFFICIENCY_VALID_MAX_PCT
    assert settings.max_efficiency_indicator_pct == 199


def test_parse_efficiency_bands_normalizes_and_filters() -> None:
    from app.domain.production.production_efficiency_valid_range import (
        parse_efficiency_bands,
    )

    assert parse_efficiency_bands("ok, low, verify") == ["ok", "low", "verify"]
    assert parse_efficiency_bands("OK,invalid") == ["ok"]
    assert parse_efficiency_bands(None) == []


def test_build_efficiency_bands_where_clause() -> None:
    from app.domain.production.production_efficiency_valid_range import (
        EFFICIENCY_BAND_LOW,
        EFFICIENCY_BAND_OK,
        EFFICIENCY_BAND_VERIFY,
        build_efficiency_bands_where_clause,
        resolve_production_list_status_filter_clause,
    )

    low_clause = build_efficiency_bands_where_clause([EFFICIENCY_BAND_LOW])
    assert "status = 'valid'" in low_clause
    assert "oee_pct < 50" in low_clause

    verify_clause = build_efficiency_bands_where_clause([EFFICIENCY_BAND_VERIFY])
    assert "status = 'outlier'" in verify_clause

    ok_clause = build_efficiency_bands_where_clause([EFFICIENCY_BAND_OK])
    assert "oee_pct >= 50" in ok_clause

    assert resolve_production_list_status_filter_clause("valid", "low") == low_clause
    assert resolve_production_list_status_filter_clause(None, None) == ""
    assert resolve_production_list_status_filter_clause("outlier", None) == (
        "WHERE status = 'outlier'"
    )
