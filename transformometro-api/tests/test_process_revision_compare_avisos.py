"""Testes utilitários do comparativo de revisões (Playbook 22 Fase B)."""

from tm_app.application.services.process_revision_compare_service import (
    ProcessRevisionCompareService,
)


def test_volume_avisos_economia_tempo_when_volumes_diverge():
    avisos = ProcessRevisionCompareService._volume_avisos(
        categoria="economia_tempo",
        volume_acima=True,
        volume_abaixo=False,
        delta_volume=10,
    )
    codes = {a["code"] for a in avisos}
    assert "volume_acima_referencia" in codes
    assert "economia_tempo_volume_diverge" in codes


def test_volume_avisos_empty_when_aligned():
    avisos = ProcessRevisionCompareService._volume_avisos(
        categoria="economia_tempo",
        volume_acima=False,
        volume_abaixo=False,
        delta_volume=0,
    )
    assert avisos == []
