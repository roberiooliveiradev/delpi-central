from unittest.mock import patch

from app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from app.domain.services.commercial_proposal_status import WON_STATUS_CODE
from app.infrastructure.persistence.totvs.commercial_repositories.sales_conversion_rate_repository import (
    SalesConversionRateRepository,
)


def test_closing_rate_counts_period_revisions_with_won_status_code() -> None:
    repository = SalesConversionRateRepository()
    request = SalesConversionRateRequest(
        start_date="2026-05-01",
        end_date="2026-05-31",
        branch="02",
    )
    captured: dict[str, str] = {}

    def _execute_one(sql: str, params: tuple) -> dict:
        captured["sql"] = sql
        captured["params"] = str(params)
        return {
            "qtd_proposals": 41,
            "qtd_won": 1,
            "sales_conversion_rate_pct": 2.44,
        }

    with patch.object(SalesConversionRateRepository, "__enter__", return_value=repository):
        with patch.object(SalesConversionRateRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_one", side_effect=_execute_one):
                result = repository.get_sales_conversion_rate(request)

    sql = captured["sql"]
    assert "ovs_base" in sql
    assert "ovs_latest" not in sql
    assert "ROW_NUMBER()" not in sql
    assert f"AD1_STATUS = '{WON_STATUS_CODE}'" in sql
    assert "AD1_STAGE" not in sql
    assert result.qtd_proposals == 41
    assert result.qtd_won == 1
    assert result.sales_conversion_rate_pct == 2.44
