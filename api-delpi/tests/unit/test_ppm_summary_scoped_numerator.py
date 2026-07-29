"""PPM por família: numerador filtrado, denominador geral (apontamentos)."""

from unittest.mock import MagicMock, patch

from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.use_cases.ppm.get_ppm_summary_use_case import GetPpmSummaryUseCase
from app.infrastructure.persistence.totvs.ppm_repositories.ppm_query_repository import (
    PpmQueryRepository,
)


def test_scoped_summary_filters_numerator_only() -> None:
    captured: dict[str, object] = {}

    def fake_execute_one(sql: str, params: tuple) -> dict:
        captured["sql"] = sql
        captured["params"] = params
        return {"total_devolvido_un": 10}

    repository = PpmQueryRepository()
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

    with patch.object(PpmQueryRepository, "_connect"), patch.object(
        repository, "execute_one", side_effect=fake_execute_one
    ):
        summary = GetPpmSummaryUseCase(repository, produced).execute(request)

    sql = str(captured["sql"])
    params = tuple(captured["params"])

    assert "QI2_ITEM LIKE ?" in sql
    assert "9026%" in params
    assert "SH6.H6_PRODUTO LIKE" not in sql
    assert "apont_inspecao" not in sql
    assert summary.total_produzido_un == 20000
    produced.get_totals.assert_called_once()
