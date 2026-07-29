"""Formatters — rótulo de motivo SIGLA - significado."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.dto.refugos.refugos_formatters import format_code_dash_label
from app.application.dto.refugos.refugos_query_request import RefugosQueryRequest
from app.application.use_cases.refugos.get_refugos_rankings_use_case import (
    GetRefugosRankingsUseCase,
)
from app.application.use_cases.refugos.get_refugos_registros_use_case import (
    GetRefugosRegistrosUseCase,
)
from app.application.dto.refugos.refugos_registros_request import RefugosRegistrosRequest
from app.domain.quality.refugos.refugos_scope import MOTIVO_SEM_LABEL


def test_format_code_dash_label_joins_code_and_description() -> None:
    assert format_code_dash_label("FM", "Falha de material") == "FM - Falha de material"


def test_format_code_dash_label_avoids_duplicate_when_equal() -> None:
    assert format_code_dash_label("FM", "FM") == "FM"
    assert format_code_dash_label("fm", "FM") == "fm"


def test_format_code_dash_label_fallbacks() -> None:
    assert format_code_dash_label("FM", "") == "FM"
    assert format_code_dash_label("", "Falha") == "Falha"
    assert (
        format_code_dash_label("", "", empty_fallback=MOTIVO_SEM_LABEL)
        == MOTIVO_SEM_LABEL
    )


def test_rankings_motivo_label_is_code_dash_description() -> None:
    repo = MagicMock()
    repo.get_ranking.return_value = [
        {
            "code": "FM",
            "label": "Falha de material",
            "quantity": 1,
            "value": 100.0,
            "occurrence_count": 2,
        },
        {
            "code": "XX",
            "label": None,
            "quantity": 1,
            "value": 50.0,
            "occurrence_count": 1,
        },
    ]
    use_case = GetRefugosRankingsUseCase(repo)
    request = RefugosQueryRequest.from_query(
        filial="01",
        data_inicio="2026-07-01",
        data_fim="2026-07-31",
        dimension="motivo",
    )

    result = use_case.execute(request)

    assert result["items"][0]["code"] == "FM"
    assert result["items"][0]["label"] == "FM - Falha de material"
    assert result["items"][1]["label"] == "XX"


def test_registros_motivo_is_code_dash_description() -> None:
    repo = MagicMock()
    repo.count_registros.return_value = 1
    repo.get_registros.return_value = [
        {
            "filial": "01",
            "loss_date": "20260715",
            "production_order": "OP1",
            "finished_product": "PA1",
            "finished_product_desc": "PA",
            "material_code": "MP1",
            "description": "MP",
            "unit": "UN",
            "reason_code": "FM",
            "reason_label": "Falha de material",
            "quantity": 1,
            "value": 10,
            "unit_cost": 10,
            "work_center": "CT1",
            "operator_id": "1",
            "operator_name": "Ana",
        }
    ]
    use_case = GetRefugosRegistrosUseCase(repo)
    request = RefugosRegistrosRequest.from_query(
        filial="01",
        data_inicio="2026-07-01",
        data_fim="2026-07-31",
    )

    result = use_case.execute(request)

    assert result["items"][0]["motivoCodigo"] == "FM"
    assert result["items"][0]["motivo"] == "FM - Falha de material"
