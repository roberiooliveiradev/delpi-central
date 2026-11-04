"""Unit — mapper horas improdutivas EN + aliases PT."""

from __future__ import annotations

from app.domain.services.production.unproductive_hours_item_mapper import (
    UnproductiveHoursItemMapper,
)


def test_map_item_emits_en_and_legacy_aliases() -> None:
    item = UnproductiveHoursItemMapper.map_item(
        {
            "data_referencia": "2026-01-15",
            "filial": "01",
            "op": "000123",
            "produto": "90300005",
            "operacao": "10",
            "recurso": "CNC01",
            "centro_custo": "CC1",
            "codigo_operador": "U1",
            "nome_operador": "Operador",
            "motivo": "RT",
            "motivo_descricao": "RETRABALHO",
            "observacao": "obs",
            "tempo_horas": 1.5,
            "valor_parada": 10.0,
            "fonte_custo": "SB2",
            "recno": 9,
        }
    )
    assert item["reference_date"] == "2026-01-15"
    assert item["dataReferencia"] == "2026-01-15"
    assert item["hours"] == 1.5
    assert item["tempoHoras"] == 1.5
    assert item["stop_reason"] == "RT"
    assert item["motivo"] == "RT"
    assert item["branch"] == "01"
    assert item["filial"] == "01"


def test_map_ranking_item_dual_keys() -> None:
    item = UnproductiveHoursItemMapper.map_ranking_item(
        rank=1,
        rank_by="stop_reason",
        row={
            "motivo": "OT",
            "motivo_descricao": "OUTROS",
            "total_apontamentos": 2,
            "total_horas": 3.0,
            "total_custo": 4.0,
            "horas_sem_custo": 0.5,
        },
    )
    assert item["rank"] == 1
    assert item["stop_reason"] == "OT"
    assert item["motivo"] == "OT"
    assert item["total_hours"] == 3.0
    assert item["totalHoras"] == 3.0
    assert "period" not in item


def test_map_ranking_item_includes_period_when_bucketed() -> None:
    item = UnproductiveHoursItemMapper.map_ranking_item(
        rank=2,
        rank_by="resource",
        row={
            "data_periodo": "2026-03-01",
            "recurso": "CT-12",
            "centro_custo": "CC01",
            "total_apontamentos": 1,
            "total_horas": 2.0,
            "total_custo": 10.0,
            "horas_sem_custo": 0.0,
            "rank_pos": 2,
        },
    )
    assert item["rank"] == 2
    assert item["period"] == "2026-03-01"
    assert item["periodo"] == "2026-03-01"
    assert item["date"] == "2026-03-01"
    assert item["resource"] == "CT-12"
