"""PPM por família: numerador filtrado, denominador geral (apontamentos)."""

from unittest.mock import MagicMock

from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.use_cases.ppm.get_ppm_summary_use_case import GetPpmSummaryUseCase


def test_scoped_summary_filters_numerator_only() -> None:
    repository = MagicMock()
    returned = MagicMock()
    returned.get_totals.return_value = {"qty_returned_un": 10.0, "nc_count": 2}
    produced = MagicMock()
    produced.get_totals.return_value = {
        "qty_produced_milheiro": 20,
        "qty_produced_un": 20000,
    }
    request = PpmSummaryRequest(
        type="internal",
        branch="01",
        date_start="2026-07-01",
        date_end="2026-07-09",
        product_prefix="9026",
    )

    summary = GetPpmSummaryUseCase(repository, produced, returned).execute(request)

    returned.get_totals.assert_called_once_with(request)
    assert summary.total_produzido_un == 20000
    assert summary.total_devolvido_un == 10.0
    produced.get_totals.assert_called_once()
    payload = summary.to_dict()
    assert payload["numerator"] == {"qty_returned_un": 10.0}
    assert payload["denominator"]["qty_produced_un"] == 20000
    assert payload["denominator"]["qty_produced_milheiro"] == 20
