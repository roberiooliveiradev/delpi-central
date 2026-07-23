from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.refugos.refugos_period import RefugosPeriod
from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.application.use_cases.refugos.get_refugos_custo_x_rol_use_case import (
    GetRefugosCustoXRolUseCase,
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


def test_custo_sobre_rol_pct_uses_rol_with_ipi() -> None:
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

    result = GetRefugosCustoXRolUseCase(refugos_repo, financial_repo).execute(_request())

    assert result["custoRefugo"] == 2500.0
    assert result["rolWithIpi"] == 100_000.0
    assert result["custoSobreRolPct"] == 2.5
    assert result["summary"]["custo_sobre_rol_pct"] == 2.5
    assert result["periodo"]["filial"] == "01"
    assert result["filtrosAplicados"]["mp"] is None

    rol_request = financial_repo.get_rol.call_args.args[0]
    assert rol_request.branch == "01"
    assert rol_request.start_date == "2026-06-01"
    assert rol_request.end_date == "2026-06-30"


def test_custo_sobre_rol_pct_null_when_rol_is_zero() -> None:
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

    result = GetRefugosCustoXRolUseCase(refugos_repo, financial_repo).execute(_request())

    assert result["custoSobreRolPct"] is None
    assert result["custoRefugo"] == 100.0


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

    result = GetRefugosCustoXRolUseCase(refugos_repo, financial_repo).execute(
        _request(mp="MP-123")
    )

    assert result["filtrosAplicados"]["mp"] == "MP-123"
    assert refugos_repo.get_resumo.call_args.kwargs["mp"] == "MP-123"
