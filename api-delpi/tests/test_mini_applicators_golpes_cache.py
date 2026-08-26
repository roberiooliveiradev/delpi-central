from unittest.mock import MagicMock, patch

from app.application.services.mini_applicators.mini_applicators_golpes_cache import (
    get_or_set_cached_golpes_batch,
    golpes_batch_cache_key,
)
from app.application.use_cases.mini_applicators.mini_applicators_use_cases import (
    PostMiniApplicatorsGolpesBatchUseCase,
)
from app.composition.query_cache_composer import reset_query_cache_for_tests


def setup_function() -> None:
    reset_query_cache_for_tests()


def test_golpes_batch_cache_key_is_stable() -> None:
    items = [
        {
            "codigo_ferramenta": "23-001",
            "data_inicial": "2026-01-01T00:00:00",
            "data_final": "2026-06-01T00:00:00",
        }
    ]
    first = golpes_batch_cache_key(filial="01", items=items)
    second = golpes_batch_cache_key(filial="01", items=list(reversed(items)))
    assert first == second


@patch(
    "app.application.use_cases.mini_applicators.mini_applicators_use_cases.get_or_set_cached_golpes_batch"
)
def test_post_mini_applicators_golpes_batch_use_case_uses_cache(mock_cache) -> None:
    repository = MagicMock()
    repository.get_golpes_batch.return_value = [
        {
            "codigo_ferramenta": "23-001",
            "filial": "01",
            "data_inicial": "2026-01-01",
            "data_final": "2026-06-01",
            "total_golpes": 120,
        }
    ]
    mock_cache.side_effect = lambda *, filial, items, factory: factory()
    use_case = PostMiniApplicatorsGolpesBatchUseCase(repository)

    result = use_case.execute(
        filial="01",
        items=[
            {
                "codigo_ferramenta": "23-001",
                "data_inicial": "2026-01-01",
                "data_final": "2026-06-01",
            }
        ],
    )

    mock_cache.assert_called_once()
    assert result["items"][0]["total_golpes"] == 120


def test_get_or_set_cached_golpes_batch_reuses_value() -> None:
    calls = {"count": 0}

    def factory() -> list[dict[str, int]]:
        calls["count"] += 1
        return [{"total_golpes": 99}]

    items = [
        {
            "codigo_ferramenta": "23-001",
            "data_inicial": "2026-01-01T00:00:00",
            "data_final": "2026-06-01T00:00:00",
        }
    ]

    first = get_or_set_cached_golpes_batch(filial="01", items=items, factory=factory)
    second = get_or_set_cached_golpes_batch(filial="01", items=items, factory=factory)

    assert first == second
    assert calls["count"] == 1
