from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.refugos.refugos_period import RefugosPeriod
from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.application.use_cases.refugos.get_refugos_scrap_cost_pct_use_case import (
    GetRefugosScrapCostPctUseCase,
)


def _request(
    *,
    filial: str = "01",
    data_inicio: str = "2026-06-01",
    data_fim: str = "2026-06-30",
    mp: str | None = None,
) -> RefugosQueryRequest:
    return RefugosQueryRequest(
        period=RefugosPeriod.resolve(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
        ),
        mp=mp,
    )


def test_scrap_cost_pct_uses_rol_with_ipi() -> None:
    refugos_repo = MagicMock()
    refugos_repo.get_resumo.return_value = {
        "total_valor": 2500.0,
        "total_quantidade": 10.0,
        "ocorrencias": 3,
        "registros_sem_custo": 1,
    }
    financial_repo = MagicMock()
    financial_repo.get_rol.return_value = {
        "rol": 90_000.0,
        "rol_with_ipi": 100_000.0,
        "gross_revenue": 120_000.0,
        "returns": 5_000.0,
        "discounts": 5_000.0,
        "ipi_separated": 10_000.0,
    }

    result = GetRefugosScrapCostPctUseCase(refugos_repo, financial_repo).execute(
        _request()
    )

    assert result["scrap_cost"] == 2500.0
    assert result["rol_with_ipi"] == 100_000.0
    assert result["scrap_cost_pct"] == 2.5
    assert result["summary"]["scrap_cost_pct"] == 2.5
    assert result["branch"] == "01"
    assert result["filters_applied"]["mp"] is None

    rol_request = financial_repo.get_rol.call_args.args[0]
    assert rol_request.branch == "01"
    assert rol_request.start_date == "2026-06-01"
    assert rol_request.end_date == "2026-06-30"


def test_scrap_cost_pct_null_when_rol_is_zero() -> None:
    refugos_repo = MagicMock()
    refugos_repo.get_resumo.return_value = {
        "total_valor": 100.0,
        "total_quantidade": 1.0,
        "ocorrencias": 1,
        "registros_sem_custo": 0,
    }
    financial_repo = MagicMock()
    financial_repo.get_rol.return_value = {
        "rol": 0.0,
        "rol_with_ipi": 0.0,
        "gross_revenue": 0.0,
        "returns": 0.0,
        "discounts": 0.0,
        "ipi_separated": 0.0,
    }

    result = GetRefugosScrapCostPctUseCase(refugos_repo, financial_repo).execute(
        _request()
    )

    assert result["scrap_cost_pct"] is None
    assert result["scrap_cost"] == 100.0


def test_consolidated_when_filial_omitted() -> None:
    refugos_repo = MagicMock()
    refugos_repo.get_resumo.return_value = {
        "total_valor": 5000.0,
        "total_quantidade": 2.0,
        "ocorrencias": 2,
        "registros_sem_custo": 0,
    }
    financial_repo = MagicMock()
    financial_repo.get_rol.return_value = {
        "rol": 200_000.0,
        "rol_with_ipi": 200_000.0,
        "gross_revenue": 200_000.0,
        "returns": 0.0,
        "discounts": 0.0,
        "ipi_separated": 0.0,
    }

    request = RefugosQueryRequest(
        period=RefugosPeriod.resolve(
            filial=None,
            data_inicio="2026-06-01",
            data_fim="2026-06-30",
            require_filial=False,
        )
    )
    result = GetRefugosScrapCostPctUseCase(refugos_repo, financial_repo).execute(request)

    assert result["branch"] == "consolidated"
    assert result["summary"]["branch_filter_applied"] is False
    assert result["summary"]["consolidated_across_branches"] is True
    assert result["scrap_cost_pct"] == 2.5
    assert refugos_repo.get_resumo.call_args.kwargs["branch"] is None
    assert financial_repo.get_rol.call_args.args[0].branch is None


def test_optional_mp_filter_forwarded_to_refugos_repository() -> None:
    refugos_repo = MagicMock()
    refugos_repo.get_resumo.return_value = {
        "total_valor": 10.0,
        "total_quantidade": 1.0,
        "ocorrencias": 1,
        "registros_sem_custo": 0,
    }
    financial_repo = MagicMock()
    financial_repo.get_rol.return_value = {
        "rol": 1000.0,
        "rol_with_ipi": 1000.0,
        "gross_revenue": 1000.0,
        "returns": 0.0,
        "discounts": 0.0,
        "ipi_separated": 0.0,
    }

    result = GetRefugosScrapCostPctUseCase(refugos_repo, financial_repo).execute(
        _request(mp="MP-123")
    )

    assert result["filters_applied"]["mp"] == "MP-123"
    assert refugos_repo.get_resumo.call_args.kwargs["mp"] == "MP-123"
