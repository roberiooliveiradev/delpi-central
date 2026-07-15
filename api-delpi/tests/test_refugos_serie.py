from unittest.mock import MagicMock

from app.application.dto.refugos.refugos_serie_request import RefugosSerieRequest
from app.application.use_cases.refugos.get_refugos_serie_use_case import (
    GetRefugosSerieUseCase,
)


def test_serie_request_auto_picks_day_for_short_period() -> None:
    request = RefugosSerieRequest.from_query(
        filial="01",
        data_inicio="2026-07-01",
        data_fim="2026-07-15",
        granularity="auto",
    )
    assert request.granularity == "day"


def test_serie_request_auto_picks_month_for_long_period() -> None:
    request = RefugosSerieRequest.from_query(
        filial="01",
        data_inicio="2026-01-01",
        data_fim="2026-07-15",
        granularity="auto",
    )
    assert request.granularity == "month"


def test_serie_use_case_formats_day_buckets() -> None:
    repo = MagicMock()
    repo.get_serie.return_value = [
        {"bucket": "20260713", "total_valor": 100.5, "total_quantidade": 2.0, "ocorrencias": 3},
        {"bucket": "20260714", "total_valor": 50.0, "total_quantidade": 1.0, "ocorrencias": 1},
    ]
    result = GetRefugosSerieUseCase(repo).execute(
        RefugosSerieRequest.from_query(
            filial="01",
            data_inicio="2026-07-13",
            data_fim="2026-07-14",
            granularity="day",
        )
    )

    assert result["granularity"] == "day"
    assert result["points"][0]["date"] == "2026-07-13"
    assert result["points"][0]["label"] == "13/07/2026"
    assert result["points"][0]["value"] == 100.5
    assert result["points"][1]["occurrenceCount"] == 1
    assert repo.get_serie.call_args.kwargs["branch"] == "01"
