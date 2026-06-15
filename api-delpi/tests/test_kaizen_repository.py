from unittest.mock import MagicMock

from app.application.dto.kaizen.kaizen_summary_request import KaizenSummaryRequest
from app.infrastructure.persistence.google_sheets.kaizen.kaizen_repository import (
    KaizenRepository,
)
from app.infrastructure.persistence.google_sheets.utils import Utils


def _repository(rows: list[dict]) -> KaizenRepository:
    client = MagicMock()
    client.read_csv_rows.return_value = rows
    return KaizenRepository(
        client=client,
        sheet_id="sheet-id",
        gid="gid",
        utils=Utils(),
    )


def _kaizen_row(**overrides: str) -> dict:
    base = {
        "filial": "01",
        "descricao": "App resina CT-16",
        "responsavel": "Ossamu",
        "area_setor": "Producao",
        "custo_investimento": "620,00",
        "segudos_por_ocorrecia": "1.015,96",
        "ocorrecias_por_dia": "0,21",
        "custo_hora": "127,16",
        "status": "implantado",
        "data": "16/01/2026",
        "deleted": "FALSE",
    }
    base.update(overrides)
    return base


def test_kaizen_daily_savings_calculated_from_sheet_inputs() -> None:
    repository = _repository([_kaizen_row()])

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            date_start="01-01-2026",
            date_end="31-01-2026",
        )
    )

    assert summary.total_kaizens == 1
    assert summary.list_kaizen[0].daily_savings == 7.54
    assert summary.list_kaizen[0].annual_savings == round(7.54 * 365, 2)


def test_kaizen_daily_savings_supports_correct_column_names() -> None:
    repository = _repository(
        [
            _kaizen_row(
                descricao="Gaveta limpeza CT-85",
                segundos_por_ocorrencia="47,00",
                ocorrencias_por_dia="2,00",
                custo_hora="113,42",
                segudos_por_ocorrecia="",
                ocorrecias_por_dia="",
            )
        ]
    )

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            date_start="01-01-2026",
            date_end="31-01-2026",
        )
    )

    assert summary.list_kaizen[0].daily_savings == 2.96


def test_kaizen_total_savings_uses_calculated_daily_gain() -> None:
    repository = _repository([_kaizen_row()])

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            date_start="16-01-2026",
            date_end="18-01-2026",
        )
    )

    assert summary.total_savings == round(7.54 * 3, 2)


def test_kaizen_daily_savings_none_when_inputs_missing() -> None:
    repository = _repository([_kaizen_row(custo_hora="")])

    summary = repository.get_kaizen_summary(
        KaizenSummaryRequest(
            date_start="01-01-2026",
            date_end="31-01-2026",
        )
    )

    assert summary.list_kaizen[0].daily_savings is None
    assert summary.list_kaizen[0].annual_savings is None
    assert summary.total_savings == 0.0


def test_kaizen_get_by_id_returns_detail() -> None:
    repository = _repository([_kaizen_row()])

    detail = repository.get_kaizen_by_id("01-16/01/2026-App resina CT-16")

    assert detail is not None
    assert detail.title == "App resina CT-16"
    assert detail.daily_savings == 7.54
    assert detail.annual_savings == round(7.54 * 365, 2)
    assert detail.seconds_per_occurrence == 1015.96
    assert detail.occurrences_per_day == 0.21
    assert detail.hourly_cost == 127.16


def test_kaizen_get_by_id_returns_none_when_missing() -> None:
    repository = _repository([_kaizen_row()])

    assert repository.get_kaizen_by_id("inexistente") is None
