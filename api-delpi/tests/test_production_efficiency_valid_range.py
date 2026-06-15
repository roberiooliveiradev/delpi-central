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


def test_eficiencia_fabril_settings_use_shared_range() -> None:
    settings = EficienciaFabrilQuerySettings()
    assert settings.min_efficiency_indicator_pct == PRODUCTION_EFFICIENCY_VALID_MIN_PCT
    assert settings.max_efficiency_indicator_pct == PRODUCTION_EFFICIENCY_VALID_MAX_PCT
    assert settings.max_efficiency_indicator_pct == 199
