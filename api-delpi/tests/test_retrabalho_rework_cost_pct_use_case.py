from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.retrabalho.retrabalho_period import RetrabalhoPeriod
from app.application.dto.retrabalho.retrabalho_query_request import RetrabalhoQueryRequest
from app.application.use_cases.retrabalho.get_retrabalho_rework_cost_pct_use_case import (
    GetRetrabalhoReworkCostPctUseCase,
)


def _request(
    *,
    filial: str = "01",
    data_inicio: str = "2026-06-01",
    data_fim: str = "2026-06-30",
    recurso: str | None = None,
) -> RetrabalhoQueryRequest:
    return RetrabalhoQueryRequest(
        period=RetrabalhoPeriod.resolve(
            filial=filial,
            data_inicio=data_inicio,
            data_fim=data_fim,
        ),
        recurso=recurso,
    )


def test_rework_cost_pct_uses_rol_with_ipi() -> None:
    retrabalho_repo = MagicMock()
    retrabalho_repo.get_resumo.return_value = {
        "total_custo": 1500.0,
        "total_horas": 30.0,
        "total_apontamentos": 12,
        "registros_sem_custo": 0,
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

    result = GetRetrabalhoReworkCostPctUseCase(retrabalho_repo, financial_repo).execute(
        _request()
    )

    assert result["rework_cost"] == 1500.0
    assert result["rol_with_ipi"] == 100_000.0
    assert result["rework_cost_pct"] == 1.5
    assert result["average_cost_per_hour"] == 50.0
    assert result["summary"]["rework_cost_pct"] == 1.5

    rol_request = financial_repo.get_rol.call_args.args[0]
    assert rol_request.branch == "01"
    assert rol_request.start_date == "2026-06-01"
    assert rol_request.end_date == "2026-06-30"


def test_rework_cost_pct_null_when_rol_is_zero() -> None:
    retrabalho_repo = MagicMock()
    retrabalho_repo.get_resumo.return_value = {
        "total_custo": 80.0,
        "total_horas": 2.0,
        "total_apontamentos": 1,
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

    result = GetRetrabalhoReworkCostPctUseCase(retrabalho_repo, financial_repo).execute(
        _request()
    )

    assert result["rework_cost_pct"] is None
    assert result["rework_cost"] == 80.0


def test_consolidated_when_filial_omitted() -> None:
    retrabalho_repo = MagicMock()
    retrabalho_repo.get_resumo.return_value = {
        "total_custo": 2000.0,
        "total_horas": 20.0,
        "total_apontamentos": 4,
        "registros_sem_custo": 0,
    }
    financial_repo = MagicMock()
    financial_repo.get_rol.return_value = {
        "rol": 100_000.0,
        "rol_with_ipi": 100_000.0,
        "gross_revenue": 100_000.0,
        "returns": 0.0,
        "discounts": 0.0,
        "ipi_separated": 0.0,
    }

    request = RetrabalhoQueryRequest(
        period=RetrabalhoPeriod.resolve(
            filial=None,
            data_inicio="2026-06-01",
            data_fim="2026-06-30",
            require_filial=False,
        )
    )
    result = GetRetrabalhoReworkCostPctUseCase(retrabalho_repo, financial_repo).execute(
        request
    )

    assert result["branch"] == "consolidated"
    assert result["summary"]["branch_filter_applied"] is False
    assert result["summary"]["consolidated_across_branches"] is True
    assert result["rework_cost_pct"] == 2.0
    assert retrabalho_repo.get_resumo.call_args.kwargs["branch"] is None
    assert financial_repo.get_rol.call_args.args[0].branch is None


def test_optional_recurso_filter_forwarded_to_repository() -> None:
    retrabalho_repo = MagicMock()
    retrabalho_repo.get_resumo.return_value = {
        "total_custo": 10.0,
        "total_horas": 1.0,
        "total_apontamentos": 1,
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

    result = GetRetrabalhoReworkCostPctUseCase(retrabalho_repo, financial_repo).execute(
        _request(recurso="CT-23")
    )

    assert result["filters_applied"]["recurso"] == "CT-23"
    assert retrabalho_repo.get_resumo.call_args.kwargs["recurso"] == "CT-23"
