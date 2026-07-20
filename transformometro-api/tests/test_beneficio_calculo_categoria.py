"""Playbook 22 — categoria de cálculo de benefício."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tm_app.core.catalogs import (
    BENEFICIO_CALCULO_CATEGORIA_DEFAULT,
    normalize_beneficio_calculo_categoria,
    options_payload,
)
from tm_app.domain import calc_rules
from tm_app.interface.http.schemas.crud_schemas import RevisaoBody


def test_normalize_beneficio_default_when_empty():
    assert normalize_beneficio_calculo_categoria(None) == "economia_tempo"
    assert normalize_beneficio_calculo_categoria("") == "economia_tempo"
    assert normalize_beneficio_calculo_categoria("  ") == "economia_tempo"


def test_normalize_beneficio_rejects_unknown():
    with pytest.raises(ValueError, match="beneficio_calculo_categoria"):
        normalize_beneficio_calculo_categoria("desconhecido")


def test_options_payload_exposes_beneficio_categorias():
    payload = options_payload()
    assert payload["beneficio_calculo_categoria_default"] == BENEFICIO_CALCULO_CATEGORIA_DEFAULT
    assert "economia_tempo" in payload["beneficio_calculo_categoria"]
    assert payload["beneficio_calculo_categoria_labels"]["economia_tempo"]


def test_revisao_body_defaults_beneficio_economia_tempo():
    body = RevisaoBody(
        processo_id="p1",
        versao_revisao="1.0.0",
        cenario_tipo="baseline",
        data_inicio_vigencia="2026-01-01",
    )
    assert body.beneficio_calculo_categoria == "economia_tempo"


def test_compose_economia_bruta_adds_capacity():
    assert calc_rules.compose_economia_bruta(economia_custo=2500, ganho_capacidade=1000) == 3500
    assert calc_rules.compose_economia_bruta(economia_custo=2500, ganho_capacidade=0) == 2500

    assert (
        calc_rules.capacity_gain_month(
            volume_ref=100,
            volume_rev=100,
            tempo_medio_ref_min=60,
            custo_hora_ref=100,
        )
        == 0.0
    )
    # +10 execuções × 1h × R$100 = R$1000
    assert (
        calc_rules.capacity_gain_month(
            volume_ref=100,
            volume_rev=110,
            tempo_medio_ref_min=60,
            custo_hora_ref=100,
        )
        == 1000.0
    )


def test_volume_reduction_signal_when_below_reference():
    assert (
        calc_rules.volume_reduction_signal_month(
            volume_ref=100,
            volume_rev=90,
            tempo_medio_ref_min=60,
            custo_hora_ref=50,
        )
        == 500.0
    )
    assert (
        calc_rules.volume_reduction_signal_month(
            volume_ref=100,
            volume_rev=110,
            tempo_medio_ref_min=60,
            custo_hora_ref=50,
        )
        == 0.0
    )


def test_benefit_volume_signals():
    signals = calc_rules.benefit_volume_signals(volume_ref=10, volume_rev=12)
    assert signals["delta_volume"] == 2
    assert signals["volume_acima_referencia"] is True
    assert signals["volume_abaixo_referencia"] is False


def test_migration_v039_is_ddl_only():
    path = Path(__file__).resolve().parents[1] / "migrations" / "V039__beneficio_calculo_categoria.sql"
    text = path.read_text(encoding="utf-8")
    assert "ADD COLUMN" in text
    assert re.search(r"\bUPDATE\b", text, re.IGNORECASE) is None
    assert re.search(r"\bINSERT\b", text, re.IGNORECASE) is None
