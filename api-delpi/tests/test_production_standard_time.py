"""Domínio — tempo padrão canônico da operação de OP (SHY → SG2, peça física)."""

from app.domain.production.production_standard_time import (
    DATA_QUALITY_COMPLETE,
    DATA_QUALITY_PIECE_CONVERSION_UNAVAILABLE,
    DATA_QUALITY_STANDARD_TIME_UNAVAILABLE,
    STANDARD_TIME_SOURCE_SG2_TEMPAD,
    STANDARD_TIME_SOURCE_SHY_TEMPAD,
    STANDARD_TIME_SOURCE_SHY_TEMPOM_QUANT,
    STANDARD_TIME_SOURCE_UNAVAILABLE,
    compute_operation_standard_time,
    resolve_setup_hours,
    resolve_standard_time_unit_hours,
)
from app.domain.services.production.production_operational_quantity_service import (
    ProductionOperationalQuantityService,
)


def _pieces_factor(unit: str) -> float | None:
    return ProductionOperationalQuantityService.resolve(unit).pieces_factor


# ── Fonte canônica do tempo unitário ──────────────────────────────────────


def test_hy_tempad_wins_and_reports_shy_source() -> None:
    result = compute_operation_standard_time(
        hy_tempad=0.001,
        hy_tempom=3.9,
        hy_quant=0.78,
        g2_tempad=0.005,
        pieces_conversion_factor=_pieces_factor("UN"),
    )
    assert result.standard_time_source == STANDARD_TIME_SOURCE_SHY_TEMPAD
    assert result.standard_time_unit_hours == 0.001
    assert result.ideal_cycle_seconds == 3.6
    assert result.data_quality == DATA_QUALITY_COMPLETE


def test_hy_tempom_over_hy_quant_fallback() -> None:
    unit_hours, source = resolve_standard_time_unit_hours(
        hy_tempad=None, hy_tempom=3.9, hy_quant=0.78
    )
    assert source == STANDARD_TIME_SOURCE_SHY_TEMPOM_QUANT
    assert unit_hours == 5.0


def test_sg2_tempad_last_fallback() -> None:
    unit_hours, source = resolve_standard_time_unit_hours(g2_tempad=5.0)
    assert source == STANDARD_TIME_SOURCE_SG2_TEMPAD
    assert unit_hours == 5.0


def test_shy_wins_over_sg2_when_both_present() -> None:
    unit_hours, source = resolve_standard_time_unit_hours(
        hy_tempad=4.0, g2_tempad=5.0
    )
    assert source == STANDARD_TIME_SOURCE_SHY_TEMPAD
    assert unit_hours == 4.0


def test_no_standard_time_is_unavailable_not_zero() -> None:
    result = compute_operation_standard_time(
        pieces_conversion_factor=_pieces_factor("UN")
    )
    assert result.standard_time_unit_hours is None
    assert result.ideal_cycle_seconds is None
    assert result.standard_time_source == STANDARD_TIME_SOURCE_UNAVAILABLE
    assert result.data_quality == DATA_QUALITY_STANDARD_TIME_UNAVAILABLE


def test_invalid_values_are_ignored_in_each_fallback_level() -> None:
    # TEMPAD=0 cai para TEMPOM/QUANT; TEMPOM=0/QUANT=0 cai para SG2.
    unit_hours, source = resolve_standard_time_unit_hours(
        hy_tempad=0, hy_tempom=0, hy_quant=0, g2_tempad=2.0
    )
    assert source == STANDARD_TIME_SOURCE_SG2_TEMPAD
    assert unit_hours == 2.0


# ── Conversão para peça física (piecesFactor) ─────────────────────────────


def test_un_unit_converts_one_to_one() -> None:
    result = compute_operation_standard_time(
        hy_tempad=0.001, pieces_conversion_factor=_pieces_factor("UN")
    )
    assert result.pieces_conversion_factor == 1
    assert result.ideal_cycle_seconds == 3.6


def test_pc_unit_converts_one_to_one() -> None:
    result = compute_operation_standard_time(
        hy_tempad=0.001, pieces_conversion_factor=_pieces_factor("PC")
    )
    assert result.pieces_conversion_factor == 1
    assert result.ideal_cycle_seconds == 3.6


def test_mi_unit_divides_by_1000_for_physical_piece() -> None:
    """0,5 h/milheiro → 1,8 s/peça (não 1800)."""
    result = compute_operation_standard_time(
        hy_tempad=0.5, pieces_conversion_factor=_pieces_factor("MI")
    )
    assert result.pieces_conversion_factor == 1000
    assert result.ideal_cycle_seconds == 1.8
    assert result.data_quality == DATA_QUALITY_COMPLETE


def test_unit_without_pieces_factor_never_invents_cycle() -> None:
    """MT não converte para peça: ciclo None, qualidade explícita."""
    result = compute_operation_standard_time(
        hy_tempad=0.5, pieces_conversion_factor=_pieces_factor("MT")
    )
    assert result.ideal_cycle_seconds is None
    assert result.standard_time_unit_hours == 0.5
    assert result.standard_time_source == STANDARD_TIME_SOURCE_SHY_TEMPAD
    assert result.data_quality == DATA_QUALITY_PIECE_CONVERSION_UNAVAILABLE


def test_unknown_unit_falls_to_piece_conversion_unavailable() -> None:
    result = compute_operation_standard_time(
        hy_tempad=0.001, pieces_conversion_factor=_pieces_factor("KG")
    )
    assert result.ideal_cycle_seconds is None
    assert result.data_quality == DATA_QUALITY_PIECE_CONVERSION_UNAVAILABLE


def test_cycle_keeps_subsecond_precision() -> None:
    """Máquinas rápidas: não arredondar ciclo para inteiro."""
    result = compute_operation_standard_time(
        hy_tempad=0.000090903, pieces_conversion_factor=_pieces_factor("UN")
    )
    assert result.ideal_cycle_seconds == 0.327251


# ── Setup (conceito separado do ciclo) ────────────────────────────────────


def test_setup_uses_hy_setup_first() -> None:
    result = compute_operation_standard_time(
        hy_tempad=0.001,
        hy_setup=0.25,
        g2_setup=0.5,
        pieces_conversion_factor=_pieces_factor("UN"),
    )
    assert result.setup_seconds == 900.0


def test_setup_falls_back_to_g2() -> None:
    assert resolve_setup_hours(hy_setup=None, g2_setup=0.5) == 0.5
    result = compute_operation_standard_time(
        hy_tempad=0.001,
        g2_setup=0.5,
        pieces_conversion_factor=_pieces_factor("UN"),
    )
    assert result.setup_seconds == 1800.0


def test_setup_defaults_to_zero_when_both_missing() -> None:
    result = compute_operation_standard_time(
        hy_tempad=0.001, pieces_conversion_factor=_pieces_factor("UN")
    )
    assert result.setup_seconds == 0.0


def test_setup_zero_from_shy_is_honored() -> None:
    """HY_SETUP=0 é valor real (COALESCE), não «ausente»."""
    assert resolve_setup_hours(hy_setup=0, g2_setup=0.5) == 0.0
