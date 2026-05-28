from __future__ import annotations

from unittest.mock import MagicMock

from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicIndicatorMeasuredValue,
)
from si_app.application.services.strategic_indicators import snapshot_shared_cache
from si_app.infrastructure.providers.strategic_indicators.real_indicator_measurements_provider import (
    RealStrategicIndicatorsMeasurementsProvider,
)


def test_get_indicator_measurements_uses_shared_cache(monkeypatch) -> None:
    snapshot_shared_cache._measurements_cache.invalidate_all()

    provider = RealStrategicIndicatorsMeasurementsProvider(
        engineering_snapshot_port=MagicMock(),
        production_snapshot_port=MagicMock(),
        commercial_snapshot_port=MagicMock(),
        quality_snapshot_port=MagicMock(),
    )

    expected = (
        [
            StrategicIndicatorMeasuredValue(
                department_id="engineering",
                indicator_id="eng-1",
                value=1.0,
                source="test",
            )
        ],
        [],
    )
    provider._build_collectors = MagicMock(return_value={})  # type: ignore[method-assign]
    provider._collect_parallel = MagicMock(return_value=[])  # type: ignore[method-assign]

    cache_key = snapshot_shared_cache.measurements_cache_key(
        start_date="01-05-2026",
        end_date="31-05-2026",
        competence=None,
        department_id="engineering",
        branch=None,
    )
    snapshot_shared_cache._measurements_cache.set(cache_key, expected)

    result = provider.get_indicator_measurements(
        start_date="01-05-2026",
        end_date="31-05-2026",
        department_id="engineering",
        branch=None,
    )

    assert result == expected
    provider._collect_parallel.assert_not_called()
