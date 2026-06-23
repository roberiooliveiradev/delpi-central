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
    assert "ovs_opened" in sql
    assert "ovs_won_accepted" in sql
    assert "ovs_won_latest" in sql
    assert "ROW_NUMBER()" in sql
    assert f"AD1.AD1_STATUS = '{WON_STATUS_CODE}'" in sql or "AD1.AD1_STATUS = ?" in sql
    assert "AD1_DTASSI" in sql
    assert "AD1_STAGE" not in sql
    assert result.qtd_proposals == 41
    assert result.qtd_won == 1
    assert result.sales_conversion_rate_pct == 2.44


def test_closing_rate_applies_customer_segment_weg_filter() -> None:
    repository = SalesConversionRateRepository()
    request = SalesConversionRateRequest(
        start_date="2026-05-01",
        end_date="2026-05-31",
        customer_segment="weg",
    )
    captured: dict[str, str] = {}

    def _execute_one(sql: str, params: tuple) -> dict:
        captured["sql"] = sql
        return {
            "qtd_proposals": 0,
            "qtd_won": 0,
            "sales_conversion_rate_pct": 0,
        }

    with patch.object(SalesConversionRateRepository, "__enter__", return_value=repository):
        with patch.object(SalesConversionRateRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_one", side_effect=_execute_one):
                repository.get_sales_conversion_rate(request)

    assert "AD1.AD1_CODCLI" in captured["sql"]
    assert "000001" in captured["sql"]
